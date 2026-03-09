"""
Microsoft 365 / Graph API provider.
Uses Azure AD app registration with client credentials OAuth2 flow.
Required Graph API permissions (application, not delegated):
  User.Read.All, Group.Read.All, Sites.Read.All, TeamSettings.Read.All,
  Directory.Read.All, Organization.Read.All
"""
import logging
import requests

logger = logging.getLogger(__name__)

GRAPH_BASE = 'https://graph.microsoft.com/v1.0'
TOKEN_URL = 'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'


class M365Provider:
    """Read-only Microsoft Graph API client using client credentials flow."""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None

    def _get_token(self) -> str:
        if self._token:
            return self._token
        resp = requests.post(
            TOKEN_URL.format(tenant_id=self.tenant_id),
            data={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'https://graph.microsoft.com/.default',
            },
            timeout=15,
        )
        resp.raise_for_status()
        self._token = resp.json()['access_token']
        return self._token

    def _get(self, path: str, params: dict = None) -> dict:
        headers = {'Authorization': f'Bearer {self._get_token()}', 'Accept': 'application/json'}
        url = path if path.startswith('http') else f'{GRAPH_BASE}{path}'
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def _get_all(self, path: str, params: dict = None) -> list:
        """Follow @odata.nextLink to page through all results."""
        results = []
        data = self._get(path, params)
        results.extend(data.get('value', []))
        while '@odata.nextLink' in data:
            data = self._get(data['@odata.nextLink'])
            results.extend(data.get('value', []))
        return results

    def test_connection(self) -> dict:
        try:
            data = self._get('/organization', params={'$select': 'displayName,id'})
            org_name = data.get('value', [{}])[0].get('displayName', 'Unknown')
            return {'success': True, 'message': f"Connected to tenant: {org_name}"}
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                if e.response.status_code == 401:
                    return {'success': False, 'error': 'Authentication failed — check tenant ID, client ID and secret.'}
                if e.response.status_code == 403:
                    return {'success': False, 'error': 'Forbidden — ensure the app has required Graph API permissions.'}
                try:
                    err = e.response.json().get('error', {})
                    return {'success': False, 'error': f"{err.get('code')}: {err.get('message')}"}
                except Exception:
                    pass
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_users(self) -> list:
        try:
            return self._get_all('/users', params={
                '$select': 'displayName,userPrincipalName,accountEnabled,assignedLicenses,jobTitle,department,mail',
                '$filter': 'accountEnabled eq true',
                '$top': '999',
            })
        except Exception as e:
            logger.warning(f"M365 get_users failed: {e}")
            return []

    def get_licenses(self) -> list:
        try:
            return self._get_all('/subscribedSkus', params={
                '$select': 'skuPartNumber,consumedUnits,prepaidUnits,skuId',
            })
        except Exception as e:
            logger.warning(f"M365 get_licenses failed: {e}")
            return []

    def get_shared_mailboxes(self) -> list:
        """Get shared mailboxes (users with mailbox but no assigned licenses)."""
        try:
            users = self._get_all('/users', params={
                '$select': 'displayName,mail,userPrincipalName,assignedLicenses',
                '$filter': "mail ne null",
                '$top': '999',
            })
            return [u for u in users if not u.get('assignedLicenses')]
        except Exception as e:
            logger.warning(f"M365 get_shared_mailboxes failed: {e}")
            return []

    def get_teams(self) -> list:
        try:
            return self._get_all('/groups', params={
                '$select': 'displayName,description,visibility,createdDateTime,mail',
                '$filter': "groupTypes/any(c:c eq 'Unified') and resourceProvisioningOptions/Any(x:x eq 'Team')",
                '$top': '999',
            })
        except Exception as e:
            logger.warning(f"M365 get_teams failed: {e}")
            return []

    def get_sharepoint_sites(self) -> list:
        try:
            return self._get_all('/sites', params={
                '$select': 'displayName,webUrl,description,createdDateTime',
                '$search': '*',
            })
        except Exception as e:
            logger.warning(f"M365 get_sharepoint_sites failed: {e}")
            return []

    def get_roles(self) -> list:
        try:
            roles = self._get_all('/directoryRoles', params={'$select': 'id,displayName,description'})
            result = []
            for role in roles:
                try:
                    members = self._get_all(f"/directoryRoles/{role['id']}/members", params={'$select': 'displayName,userPrincipalName'})
                    if members:
                        role['members'] = members
                        result.append(role)
                except Exception:
                    pass
            return result
        except Exception as e:
            logger.warning(f"M365 get_roles failed: {e}")
            return []

    def sync(self) -> dict:
        """Pull all data and return structured summary."""
        return {
            'users': self.get_users(),
            'licenses': self.get_licenses(),
            'shared_mailboxes': self.get_shared_mailboxes(),
            'teams': self.get_teams(),
            'sharepoint_sites': self.get_sharepoint_sites(),
            'roles': self.get_roles(),
        }
