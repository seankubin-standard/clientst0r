"""
UniFi Network Application API provider.
Uses the official UniFi API with X-API-Key header authentication.
Reference: https://help.ui.com/hc/en-us/articles/30076656117655
"""
import logging
import urllib3
import requests

logger = logging.getLogger(__name__)


class UnifiProvider:
    """Read-only UniFi Network Application API client."""

    def __init__(self, host: str, api_key: str, verify_ssl: bool = False):
        self.host = host.rstrip('/')
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _get(self, path: str, **kwargs) -> dict:
        url = f"{self.host}{path}"
        resp = self.session.get(url, verify=self.verify_ssl, timeout=15, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def test_connection(self) -> dict:
        """Test credentials by fetching the site list."""
        try:
            data = self._get('/proxy/network/integration/v1/sites')
            sites = data.get('data', [])
            return {'success': True, 'message': f"Connected. Found {len(sites)} site(s)."}
        except requests.exceptions.SSLError:
            return {'success': False, 'error': 'SSL error — try disabling SSL verification for self-signed certificates.'}
        except requests.exceptions.ConnectionError as e:
            return {'success': False, 'error': f'Cannot reach host: {e}'}
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                return {'success': False, 'error': 'Authentication failed — check your API key.'}
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_sites(self) -> list:
        try:
            data = self._get('/proxy/network/integration/v1/sites')
            return data.get('data', [])
        except Exception as e:
            logger.warning(f"UniFi get_sites failed: {e}")
            return []

    def get_devices(self, site_id: str) -> list:
        try:
            data = self._get(f'/proxy/network/integration/v1/sites/{site_id}/devices')
            return data.get('data', [])
        except Exception as e:
            logger.warning(f"UniFi get_devices({site_id}) failed: {e}")
            return []

    def get_wlans(self, site_id: str) -> list:
        """Get wireless networks for a site."""
        try:
            data = self._get(f'/proxy/network/api/s/{site_id}/rest/wlanconf')
            return data.get('data', [])
        except Exception as e:
            logger.warning(f"UniFi get_wlans({site_id}) failed: {e}")
            return []

    def get_vlans(self, site_id: str) -> list:
        """Get VLANs/networks for a site."""
        try:
            data = self._get(f'/proxy/network/api/s/{site_id}/rest/networkconf')
            return data.get('data', [])
        except Exception as e:
            logger.warning(f"UniFi get_vlans({site_id}) failed: {e}")
            return []

    def get_client_count(self, site_id: str) -> int:
        """Get active client count for a site."""
        try:
            data = self._get(f'/proxy/network/api/s/{site_id}/stat/sta')
            return len(data.get('data', []))
        except Exception as e:
            logger.warning(f"UniFi get_client_count({site_id}) failed: {e}")
            return 0

    def sync(self) -> dict:
        """Pull all data and return structured summary."""
        sites = self.get_sites()
        result = {'sites': []}
        for site in sites:
            site_id = site.get('siteId') or site.get('name', '')
            site_name = site.get('meta', {}).get('desc') or site.get('name', site_id)
            devices = self.get_devices(site_id)
            wlans = self.get_wlans(site_id)
            vlans = self.get_vlans(site_id)
            client_count = self.get_client_count(site_id)

            # Count device types
            type_counts = {}
            for d in devices:
                dtype = d.get('type', 'unknown')
                type_counts[dtype] = type_counts.get(dtype, 0) + 1

            result['sites'].append({
                'id': site_id,
                'name': site_name,
                'devices': devices,
                'device_type_counts': type_counts,
                'wlans': wlans,
                'vlans': vlans,
                'client_count': client_count,
            })
        return result
