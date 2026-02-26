# Getting Started

## Quick Start

1. **Log in** — Use your credentials or Azure AD SSO if configured.
2. **Create or select an Organization** — All data is scoped to organizations.
3. **Invite your team** — Go to *Settings → Users* and send invitations.
4. **Assign roles** — Grant Owner, Admin, Editor, or Read-Only per user.
5. **Add assets or passwords** — Start populating inventory or the vault.
6. **Set up WAN monitoring** — Create monitors for public-facing endpoints.

---

## Organizations

Organizations are the top-level containers for all data. ClientSt0r is **multi-tenant** — each client, department, or team has its own organization with full data isolation.

| Action | Where |
|--------|-------|
| Create | *Admin → Organizations → New Organization* |
| Switch | Organization selector in the top navigation bar |
| Scope | Assets, passwords, vehicles, and monitors all belong to one org |
| Global | Templates and reference data can be shared across all organizations |

**Switching organizations** — click the org name in the top nav bar. All data views immediately update to reflect the selected organization. Staff/superusers also have a Global View that shows all organizations simultaneously.

---

## Users & Roles

Access control uses **role-based permissions** with four built-in roles:

| Role | Capabilities |
|------|-------------|
| **Owner** | Full control including billing and organization deletion |
| **Admin** | Manage users, all data, and settings — no billing |
| **Editor** | Create and edit data; cannot manage users or settings |
| **Read-Only** | View data only; cannot create, edit, or delete |

- Invite members at *Settings → Users → Invite User*
- Custom roles with 42 granular permissions are available for fine-grained control
- A user can have **different roles** in different organizations

---

## API Keys

API keys authenticate programmatic access to the REST API and the browser extension.

| Action | Details |
|--------|---------|
| Generate | Click your username → *API Keys* → *Create New Key* |
| Format | Keys are prefixed `itdocs_live_…` |
| Usage | `Authorization: Bearer YOUR_KEY` header |
| Scope | Keys inherit your user's organization access and role |
| Revoke | Delete a key instantly to invalidate all current uses |

```bash
# Example API call
curl -H "Authorization: Bearer itdocs_live_xK9mPL..." \
     https://your-server/api/assets/
```

> **Security:** Copy your key immediately after creation — it is only shown once.

---

*Next: [Asset Management](asset-management.md)*
