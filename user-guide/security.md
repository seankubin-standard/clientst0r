# Security

Built-in security tooling — vulnerability scanning, role-based access control, audit logging, 2FA, and data protection.

---

## Vulnerability Scanning

ClientSt0r includes a built-in package vulnerability scanner:

| Feature | Details |
|---------|---------|
| **CVE Database** | Checks installed Python packages and OS packages against known CVEs |
| **Severity Ratings** | Critical / High / Medium / Low (CVSS-based) |
| **Scheduled Scans** | Runs automatically on a configurable schedule |
| **Remediation** | Each finding links to the CVE advisory and fix version |
| **History** | Track scan results over time to see improvement |

### Severity Levels

| Level | Color | CVSS Score |
|-------|-------|------------|
| **Critical** | Red | 9.0–10.0 |
| **High** | Orange | 7.0–8.9 |
| **Medium** | Yellow | 4.0–6.9 |
| **Low** | Grey | 0.1–3.9 |

---

## Authentication & Access Control

| Feature | Details |
|---------|---------|
| **Two-Factor Auth (2FA)** | TOTP-based; enforce per organization |
| **Azure AD SSO** | OAuth2/OIDC integration for enterprise login |
| **Password Policy** | Minimum length, complexity, and rotation requirements |
| **Session Timeout** | Configurable idle timeout per organization |
| **IP Allowlist** | Restrict login to specific IP ranges |
| **Account Lockout** | Temporary lockout after N failed login attempts (via django-axes) |

### Enabling 2FA

1. Go to *Profile → Security → Enable Two-Factor Auth*
2. Scan the QR code with an authenticator app
3. Enter the 6-digit code to confirm
4. Save your backup codes in a secure location

Admins can **require 2FA** for all members of an organization at *Settings → Security → Require 2FA*.

---

## Role-Based Access Control (RBAC)

Four built-in roles cover most use cases:

| Role | Permissions |
|------|-------------|
| **Owner** | Everything including org deletion and billing |
| **Admin** | All data + user management; no billing |
| **Editor** | Create and edit all data; read-only for settings |
| **Read-Only** | View all data; no write access |

### Custom Roles

Create custom roles with any combination of 42 granular permissions:

- `assets.view`, `assets.create`, `assets.edit`, `assets.delete`
- `vault.view`, `vault.create`, `vault.edit`, `vault.reveal`
- `vehicles.view`, `vehicles.create`, `vehicles.edit`
- `monitoring.view`, `monitoring.create`, `monitoring.edit`
- `users.view`, `users.invite`, `users.manage`
- … and more

Custom roles are assigned per-organization, just like built-in roles.

---

## Audit Logging

Every significant action is recorded in an immutable audit log:

| Field | Details |
|-------|---------|
| **Timestamp** | Exact date and time |
| **User** | Who performed the action |
| **Action** | Created / Updated / Deleted / Viewed / Exported |
| **Object** | What was acted on (asset, password, user, etc.) |
| **Before / After** | Field-level diff for updates |
| **IP Address** | Source IP of the request |

### Filtering the Audit Log

Filter by user, date range, action type, and object type. Export filtered results to CSV.

Retention: audit logs are kept indefinitely by default (configurable).

---

## Data Protection

| Layer | Details |
|-------|---------|
| **Encryption at Rest** | AES-256 for vault credentials; database-level encryption optional |
| **Encryption in Transit** | TLS 1.2+ required; HTTP automatically redirected to HTTPS |
| **Backups** | Automated database backups with configurable retention |
| **File Uploads** | Stored outside web root; served through authenticated views only |
| **GDPR** | Data export and deletion tools available for compliance |

---

*Previous: [WAN Monitoring](wan-monitoring.md) · Next: [API & Integrations](api.md)*
