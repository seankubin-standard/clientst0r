# API & Integrations

Full REST API with DRF browsable interface, webhook events, and RMM integrations.

---

## API Overview

| Feature | Details |
|---------|---------|
| **Base URL** | `/api/` |
| **Format** | JSON (default); browsable HTML UI at `/api/` |
| **Auth** | API key Bearer token |
| **Versioning** | URL-based (current: v1) |
| **Rate Limiting** | Configurable per key |

---

## Authentication

All API requests require an API key in the `Authorization` header:

```http
GET /api/assets/ HTTP/1.1
Host: your-server.example.com
Authorization: Bearer itdocs_live_xK9mPL3t8n...
```

Generate keys at **Profile → API Keys**. Keys inherit your organization access and role permissions.

---

## REST API Endpoints

### Assets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/assets/` | List assets (filterable) |
| POST | `/api/assets/` | Create asset |
| GET | `/api/assets/{id}/` | Get asset detail |
| PUT/PATCH | `/api/assets/{id}/` | Update asset |
| DELETE | `/api/assets/{id}/` | Delete asset |

### Passwords (Vault)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/passwords/` | List vault entries |
| POST | `/api/passwords/` | Create entry |
| GET | `/api/passwords/{id}/` | Get entry detail |
| GET | `/api/passwords/{id}/?reveal=true` | Get entry with plaintext password |
| GET | `/api/passwords/{id}/otp/` | Get current TOTP code |
| PUT/PATCH | `/api/passwords/{id}/` | Update entry |
| DELETE | `/api/passwords/{id}/` | Delete entry |

### Organizations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/organizations/` | List accessible organizations |
| GET | `/api/organizations/{id}/` | Get organization detail |

### Vehicles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vehicles/` | List vehicles |
| POST | `/api/vehicles/` | Create vehicle |
| GET | `/api/vehicles/{id}/` | Get vehicle detail |
| PUT/PATCH | `/api/vehicles/{id}/` | Update vehicle |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/monitors/` | List WAN monitors |
| POST | `/api/monitors/` | Create monitor |
| GET | `/api/monitors/{id}/` | Get monitor + status |
| PUT/PATCH | `/api/monitors/{id}/` | Update monitor |

---

## Filtering & Pagination

All list endpoints support:

```
GET /api/assets/?search=switch&ordering=-created_at&page=2&page_size=50
```

| Parameter | Description |
|-----------|-------------|
| `search` | Full-text search across key fields |
| `ordering` | Sort by any field; prefix `-` for descending |
| `page` | Page number (default: 1) |
| `page_size` | Results per page (default: 25, max: 200) |

Field-specific filters vary by endpoint — see the browsable API at `/api/` for all available filters.

---

## Webhooks

Configure webhooks at *Settings → Webhooks*. Events trigger a POST to your configured URL.

### Available Events

| Event | Trigger |
|-------|---------|
| `asset.created` | New asset added |
| `asset.updated` | Asset record changed |
| `asset.deleted` | Asset removed |
| `monitor.down` | WAN monitor fails |
| `monitor.up` | WAN monitor recovers |
| `vulnerability.found` | New CVE detected |
| `vault.breach` | Vault entry flagged as breached |

### Webhook Payload Structure

```json
{
  "event": "monitor.down",
  "timestamp": "2025-11-15T14:32:00Z",
  "organization": {
    "id": 42,
    "name": "Acme Corp"
  },
  "data": {
    "monitor_id": 7,
    "name": "Main Website",
    "url": "https://example.com",
    "error": "Connection timed out"
  }
}
```

Webhook deliveries are logged with the response status. Failed deliveries can be retried from *Settings → Webhooks → Delivery Log*.

---

## RMM Integrations

ClientSt0r can sync devices from Remote Monitoring & Management platforms:

| Platform | Features |
|----------|---------|
| **ConnectWise Automate** | Sync devices, GPS, status |
| **Datto RMM** | Sync devices, alerts |
| **NinjaRMM** | Sync devices |
| **Syncro** | Sync devices |

Configure at *Settings → Integrations → RMM*. Sync runs on a schedule and can be triggered manually.

---

*Previous: [Security](security.md) · Back to [User Guide](README.md)*
