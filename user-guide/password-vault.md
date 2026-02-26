# Password Vault

Encrypted credential storage for teams — AES-256 encryption, TOTP, breach detection, and sharing controls.

---

## Security Features

| Feature | Details |
|---------|---------|
| **Encryption** | AES-256 at rest; TLS in transit |
| **Zero-Knowledge Design** | Passwords are only decrypted server-side for the requesting user |
| **Access Control** | Vault entries scoped to your organization and role |
| **Audit Log** | Every view, copy, create, edit, and delete is recorded |
| **Session Security** | Configurable timeout; all sessions invalidated on password change |

---

## Breach Detection

ClientSt0r integrates with **Have I Been Pwned (HIBP)** to flag compromised passwords:

- Checks stored passwords against the HIBP database using k-anonymity (only a partial hash is sent — the plaintext password never leaves your server)
- Breached entries are flagged with a red **Breached** badge
- Reused passwords across entries are also detected and warned
- Scan runs automatically; also available on demand

---

## Password Management

| Feature | Details |
|---------|---------|
| **Store** | Title, username, password, URL, notes, tags |
| **Search** | Full-text search across all fields |
| **Copy** | Copy username or password to clipboard with one click |
| **Reveal** | Show password inline (requires explicit click, logged) |
| **Tags** | Organize entries with custom labels |
| **Expiry** | Set password expiration date; alerts 30 days before |
| **Favorites** | Pin frequently-used entries |

---

## Password Generator

Built-in cryptographically secure password generator:

| Option | Details |
|--------|---------|
| **Length** | 8–128 characters |
| **Character Sets** | Uppercase, lowercase, numbers, symbols (each toggleable) |
| **Passphrase Mode** | Generates pronounceable word-based passphrases |
| **Strength Meter** | Visual entropy indicator |

---

## TOTP / Two-Factor Auth

Store TOTP secrets alongside credentials and generate one-time codes without a separate authenticator app:

1. Paste the TOTP secret (or scan QR code URI) into the vault entry
2. A live 6-digit OTP is displayed and refreshes every 30 seconds
3. Copy the code with one click — automatically refreshed before expiry
4. QR code export is available for migrating to a hardware token

---

## Sharing & Collaboration

| Feature | Details |
|---------|---------|
| **Organization Scope** | All org members with Editor+ role can see shared entries |
| **Read-Only Sharing** | Limit specific entries to view-only for certain roles |
| **Entry History** | View all previous values and who changed them |
| **Access Log** | See exactly who viewed or copied each credential |

---

## Import & Export

| Format | Import | Export |
|--------|:------:|:------:|
| CSV (generic) | ✓ | ✓ |
| LastPass CSV | ✓ | — |
| 1Password CSV | ✓ | — |
| Bitwarden JSON | ✓ | — |
| Encrypted backup | ✓ | ✓ |

> **Note:** Exported files contain plaintext passwords. Store exports securely and delete after use.

---

*Previous: [Service Vehicles](service-vehicles.md) · Next: [WAN Monitoring](wan-monitoring.md)*
