"""
HaloPSA Provider
Implements full integration with HaloPSA API.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from .base import BaseProvider, ProviderError, AuthenticationError

logger = logging.getLogger('integrations')


class HaloPSAProvider(BaseProvider):
    """
    HaloPSA provider.
    Requires credentials: client_id, client_secret, tenant (optional)
    HaloPSA uses OAuth2 client credentials flow for authentication.
    """
    provider_name = "HaloPSA"
    supports_companies = True
    supports_contacts = True
    supports_tickets = True
    supports_projects = True
    supports_agreements = True

    def __init__(self, connection):
        super().__init__(connection)
        self._access_token = None
        self._token_expires_at = None
        self._status_names = None

    def _get_access_token(self):
        """
        Get OAuth2 access token using client credentials flow.
        Caches token and refreshes when expired.
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token

        # Get new token
        client_id = self.credentials.get('client_id', '')
        client_secret = self.credentials.get('client_secret', '')
        tenant = self.credentials.get('tenant', '')

        if not all([client_id, client_secret]):
            raise AuthenticationError("Missing HaloPSA credentials")

        try:
            auth_url = f"{self.base_url}/auth/token"
            data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'all',
            }
            if tenant:
                data['tenant'] = tenant

            response = self.session.post(auth_url, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)

            return self._access_token

        except Exception as e:
            logger.error(f"HaloPSA token exchange failed: {e}")
            raise AuthenticationError(f"Failed to authenticate: {e}")

    def _get_auth_headers(self):
        """
        Get authentication headers with OAuth2 bearer token.
        """
        token = self._get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    def test_connection(self) -> bool:
        """Test HaloPSA connection by fetching user info."""
        try:
            response = self._make_request('GET', '/api/Agent')
            return response.status_code == 200
        except Exception as e:
            logger.error(f"HaloPSA connection test failed: {e}")
            return False

    def list_companies(self, page_size=100, updated_since=None) -> List[Dict]:
        """
        List clients from HaloPSA.
        """
        companies = []
        page_no = 1

        while True:
            params = {
                'pageinate': 'true',
                'page_size': page_size,
                'page_no': page_no,
            }

            if updated_since:
                # HaloPSA filter format
                date_str = updated_since.strftime('%Y-%m-%dT%H:%M:%S')
                params['updated_since'] = date_str

            try:
                response = self._make_request('GET', '/api/Client', params=params)
                data = response.json()

                clients = data.get('clients', [])
                if not clients:
                    break

                for raw_company in clients:
                    companies.append(self.normalize_company(raw_company))

                # Check if we have more pages
                record_count = data.get('record_count', 0)
                if len(companies) >= record_count:
                    break

                page_no += 1

            except Exception as e:
                logger.error(f"Error fetching HaloPSA clients page {page_no}: {e}")
                break

        return companies

    def get_company(self, company_id: str) -> Dict:
        """Get single client by ID."""
        try:
            response = self._make_request('GET', f'/api/Client/{company_id}')
            return self.normalize_company(response.json())
        except Exception as e:
            logger.error(f"Error fetching HaloPSA client {company_id}: {e}")
            raise ProviderError(f"Failed to fetch client: {e}")

    def list_contacts(self, company_id: Optional[str] = None, page_size=100, updated_since=None) -> List[Dict]:
        """List users/contacts from HaloPSA."""
        contacts = []
        page_no = 1

        while True:
            params = {
                'pageinate': 'true',
                'page_size': page_size,
                'page_no': page_no,
            }

            if company_id:
                params['client_id'] = company_id

            try:
                response = self._make_request('GET', '/api/Users', params=params)
                data = response.json()

                users = data.get('users', [])
                if not users:
                    break

                for raw_contact in users:
                    contacts.append(self.normalize_contact(raw_contact))

                record_count = data.get('record_count', 0)
                if len(contacts) >= record_count:
                    break

                page_no += 1

            except Exception as e:
                logger.error(f"Error fetching HaloPSA users page {page_no}: {e}")
                break

        return contacts

    def list_tickets(self, company_id: Optional[str] = None, status: Optional[str] = None,
                     updated_since: Optional[datetime] = None, page_size=100) -> List[Dict]:
        """List tickets from HaloPSA."""
        tickets = []
        page_no = 1

        while True:
            params = {
                'pageinate': 'true',
                'page_size': page_size,
                'page_no': page_no,
            }

            if company_id:
                params['client_id'] = company_id

            if updated_since:
                date_str = updated_since.strftime('%Y-%m-%dT%H:%M:%S')
                params['updated_since'] = date_str

            try:
                response = self._make_request('GET', '/api/Tickets', params=params)
                data = response.json()

                ticket_list = data.get('tickets', [])
                if not ticket_list:
                    break

                for raw_ticket in ticket_list:
                    tickets.append(self.normalize_ticket(raw_ticket))

                record_count = data.get('record_count', 0)
                if len(tickets) >= record_count:
                    break

                page_no += 1

            except Exception as e:
                logger.error(f"Error fetching HaloPSA tickets page {page_no}: {e}")
                break

        return tickets

    def get_ticket(self, ticket_id: str) -> Dict:
        """Get single ticket by ID."""
        try:
            response = self._make_request('GET', f'/api/Tickets/{ticket_id}')
            return self.normalize_ticket(response.json())
        except Exception as e:
            logger.error(f"Error fetching HaloPSA ticket {ticket_id}: {e}")
            raise ProviderError(f"Failed to fetch ticket: {e}")

    def normalize_company(self, raw_data: Dict) -> Dict:
        """Normalize HaloPSA client to standard format."""
        return {
            'external_id': str(raw_data.get('id', '')),
            'name': raw_data.get('name', ''),
            'phone': raw_data.get('phone', ''),
            'website': raw_data.get('website', ''),
            'address': self._format_address(raw_data),
            'raw_data': raw_data,
        }

    def normalize_contact(self, raw_data: Dict) -> Dict:
        """Normalize HaloPSA user to standard format."""
        return {
            'external_id': str(raw_data.get('id', '')),
            'company_id': str(raw_data.get('client_id', '')) if raw_data.get('client_id') else None,
            'first_name': raw_data.get('firstname', ''),
            'last_name': raw_data.get('surname', ''),
            'email': raw_data.get('emailaddress', ''),
            'phone': raw_data.get('phonenumber', ''),
            'title': raw_data.get('jobtitle', ''),
            'raw_data': raw_data,
        }

    def _get_status_names(self) -> Dict:
        """id -> name map from /api/Status, cached per provider instance."""
        if self._status_names is None:
            try:
                response = self._make_request('GET', '/api/Status')
                self._status_names = {
                    s.get('id'): (s.get('name') or '')
                    for s in response.json()
                    if isinstance(s, dict)
                }
            except Exception as e:
                logger.warning(f"Failed to fetch HaloPSA status list: {e}")
                self._status_names = {}
        return self._status_names

    def _bucket_status(self, name: str) -> str:
        """
        Map a HaloPSA status name (tenant-configurable, e.g. "Quote Sent",
        "Awaiting Procurement") onto PSATicket.STATUS_CHOICES.
        """
        n = (name or '').strip().lower()
        if not n or n == 'new':
            return 'new'
        if 'clos' in n or 'invoiced' in n:
            return 'closed'
        if 'resolv' in n or 'complet' in n:
            return 'resolved'
        if ('hold' in n or 'await' in n or 'wait' in n or 'parts' in n
                or n.startswith('with ')):
            return 'waiting'
        return 'in_progress'

    def normalize_ticket(self, raw_data: Dict) -> Dict:
        """Normalize HaloPSA ticket to standard format."""
        # The Tickets list endpoint returns only status_id; a status
        # name/dict is present only on some detail payloads.
        raw_status = raw_data.get('status')
        if isinstance(raw_status, dict):
            status_name = raw_status.get('name', '')
        else:
            status_name = raw_data.get('statusname', '')
        if not status_name and raw_data.get('status_id') is not None:
            status_name = self._get_status_names().get(raw_data.get('status_id'), '')
        status = self._bucket_status(status_name)

        # Map priority
        priority_map = {
            1: 'low',
            2: 'medium',
            3: 'high',
            4: 'urgent',
        }
        priority_id = raw_data.get('priority_id', 2)
        priority = priority_map.get(priority_id, 'medium')

        return {
            'external_id': str(raw_data.get('id', '')),
            'company_id': str(raw_data.get('client_id', '')) if raw_data.get('client_id') else None,
            'contact_id': str(raw_data.get('user_id', '')) if raw_data.get('user_id') else None,
            'ticket_number': str(raw_data.get('ticketidstring', raw_data.get('id', ''))),
            'subject': raw_data.get('summary', ''),
            'description': raw_data.get('details', ''),
            'status': status,
            'priority': priority,
            'created_at': self._parse_datetime(raw_data.get('dateoccurred')),
            'updated_at': self._parse_datetime(raw_data.get('dateupdated')),
            'raw_data': raw_data,
        }

    def _format_address(self, client_data: Dict) -> str:
        """Format client address from Halo format."""
        parts = []
        if client_data.get('address1'):
            parts.append(client_data['address1'])
        if client_data.get('address2'):
            parts.append(client_data['address2'])
        if client_data.get('address3'):
            parts.append(client_data['address3'])
        if client_data.get('address4'):
            parts.append(client_data['address4'])
        return ', '.join(parts)

    def _parse_datetime(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse HaloPSA datetime string."""
        if not date_string:
            return None
        try:
            # Halo format: 2023-01-15T10:30:00 (UTC, no offset)
            return datetime.strptime(date_string[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
        except Exception:
            return None
