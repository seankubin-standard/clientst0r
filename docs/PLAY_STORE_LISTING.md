# Play Console — Store Listing Copy

Pre-written copy for the Play Console **Main store listing** page. Lengths are inside Play Console limits. Edit freely; the wording rules in `CLAUDE.md` (no competitor name-dropping, "OPTIONAL AI" tag for AI-assisted features) apply if you change anything.

---

## App name (max 30 chars)
```
Client St0r Mobile
```

(If "Client St0r" is unavailable as a Play Store name due to similarity rules, alternative: `Client St0r MSP` — 16 chars.)

---

## Short description (max 80 chars)
```
Field companion for IT technicians using Client St0r — tickets, KB, vault, more.
```

(79 chars — counted.)

---

## Full description (max 4000 chars)

```
Client St0r Mobile is the on-the-go companion app for technicians using the Client St0r IT service-management platform. It connects to your organization's self-hosted Client St0r server so your team can work tickets, look up client documentation, and access vaulted credentials from the field.

The app is designed for IT service providers (MSPs) and internal IT teams who already run Client St0r on their own infrastructure. It is not a standalone product — you need a Client St0r server URL and an account on it to sign in.

WHAT YOU CAN DO

• Ticket queue: View, search, and update tickets assigned to you. Add comments and status changes from the field instead of waiting until you're back at a desk.

• Client lookup: Browse organizations and their assets — workstations, servers, network gear, IPs, MAC addresses, serial numbers — without VPN'ing back to the office.

• Knowledge base: Search and read your team's runbooks, how-tos, and client-specific docs. Markdown rendering with images.

• Vault access: Retrieve client credentials with the same approval gates, rate limits, and audit logging your web users get. Password reveals run through your server's policy — break-glass requests, per-credential approval, and reveal-rate limits all apply.

• Dashboard: Quick view of your active tickets, organization health, recent monitoring alerts, and security flags.

• Multi-factor auth: TOTP MFA support for accounts that require it.

PRIVACY AND SECURITY

This app is a thin client to the Client St0r server you operate. It does not send data to any third-party service. All traffic to your server is encrypted with TLS. On-device storage (auth token, server URL, basic profile cache) is encrypted with the Android Keystore. Vault secrets retrieved through the reveal flow are held in memory only — never written to disk.

The app does not collect location, photos, contacts, or any data not required to talk to your server.

WHAT YOU NEED

• A Client St0r server (self-hosted) reachable over HTTPS
• An account on that server with API access
• Android 7 (Nougat) or newer

For setup, contact your Client St0r administrator for your server URL.

LEARN MORE

Project home: https://github.com/agit8or1/clientst0r
Issues and feedback: https://github.com/agit8or1/clientst0r/issues
```

(Word-count this in Play Console — should land around 1900 chars, well under 4000.)

---

## What's new (per release, max 500 chars)

For **v3.17.446**:
```
Bug fixes for first internal-testing release:
• Login fix — the field was sending email instead of username on POST, causing "username and password are required" with credentials clearly entered.
• Build unblock — patched expo-modules-core for Android SDK 35 (PackageInfo.requestedPermissions became nullable, broke Kotlin compile).
```

(331 chars.)

---

## Graphic assets you still need to provide

Play Console requires these to publish (Internal Testing is more lenient but Production requires all):

| Asset | Required size | Required for Internal Testing? | Notes |
|---|---|---|---|
| App icon (high-res) | 512×512 PNG, 32-bit | Yes | You have `mobile/assets/icon.png` — check it's at least 512×512 |
| Feature graphic | 1024×500 PNG/JPG | Yes | This is *not* the icon; it's a wide banner shown above the listing. **You don't have one yet.** |
| Phone screenshots | 1080×1920 (or any 16:9 to 9:16) PNG/JPG, ≥2 | Yes | At least 2 phone screenshots required. Take them from a real device or emulator showing the dashboard, ticket list, and login screen |
| Tablet screenshots | Optional | No | Skip unless you tablet-test |
| Promo video (YouTube URL) | Optional | No | |

If you don't have a feature graphic, the simplest path is a 1024×500 image with the project logo on a colored background — Inkscape or Figma can produce one in 5 minutes. Or render one programmatically with PIL + the existing icon.

---

## App category, content rating, target audience

| Field | Suggested answer |
|---|---|
| App category | **Business** (Productivity is also valid) |
| Tags | "IT", "MSP", "service desk", "ticketing", "knowledge base" |
| Content rating | Run the IARC questionnaire — for a B2B IT app it should come back **Everyone** (3+) |
| Target audience age | **Ages 18+** (it's a tool for working professionals; no need to worry about Families Policy) |
| Are ads in your app? | **No** |
| Government app? | **No** |
| COVID-19 contact tracing app? | **No** |
| News app? | **No** |
| Health app? | **No** |
| Financial features? | **No** |

---

## App access (test login for Google's reviewer)

Play Console asks how their reviewer can log in to test the app. Since this is a self-hosted app that requires an account on a server you own, give them a test account:

**Suggested answer (free-text in Play Console):**

*"This app is a thin client to a self-hosted Client St0r server. To test, set the server URL to `https://huduglue.agit8or.net/api/mobile/v1` on the login screen and use the following credentials:*

*  Username: `play-reviewer`*
*  Password: `[generated, share via Play Console secure note]`*

*This is a read-only reviewer account scoped to a demo organization. The reviewer will be able to see tickets, KB articles, and the asset list, but will not have vault access or write permissions. The account is rate-limited to prevent abuse."*

(Translation: you'll want to actually create that `play-reviewer` user before submitting. It only needs to exist when Play's reviewer checks the app, which is during the first content-review pass.)
