# Privacy Policy — Client St0r Mobile

**Effective:** 2026-05-09
**Last updated:** 2026-05-09

This policy describes how the **Client St0r Mobile** Android app handles user data. Client St0r Mobile is a companion app for the Client St0r IT service-management platform. It is intended for use by IT technicians and staff at organizations that have deployed Client St0r on their own infrastructure.

## Who is the data controller

Client St0r is **self-hosted**. Each customer deploys the Client St0r server on their own infrastructure and is the data controller for everything stored on that server. The Client St0r Mobile app is a thin client that connects to the server URL its user enters at first launch.

The app developer **does not operate a centralized backend**, does not host any user data, and never receives data entered into the app. All network traffic from the app goes directly to the user-configured server URL and stays within the user's organization.

If you have questions about how data is processed inside your organization's Client St0r deployment, contact your Client St0r administrator. Their privacy policy applies to data on the server.

## What the app sends to your server

When you sign in, the app sends your email or username and password over HTTPS to the server URL you configured. The server returns an authentication token. From that point forward, every API request the app makes carries this token in an `Authorization` header.

While in use, the app may transmit the following data **to your configured server only**:
- Login credentials (email/username + password) at sign-in
- Multi-factor authentication codes if your server requires MFA
- Read requests for tickets, organizations, assets, knowledge-base articles, and vault entries that your server's permission model authorizes you to access
- Comments and updates you make on tickets
- Vault password reveal requests, which your server may rate-limit, audit, and require approval for

All transmission uses TLS (HTTPS). The app does not transmit data to any third-party service, advertising network, or analytics provider.

## What the app stores on your device

The app stores the following on-device, encrypted in the Android Keystore via the `expo-secure-store` library:
- Your authentication token
- The server URL you entered
- A small cached copy of your basic profile (user ID, username, email, full name, organization, role) used to populate the UI between launches

The app does **not** store passwords on the device. Vault secrets retrieved through the reveal flow are held in memory only and are not written to disk.

Signing out (or uninstalling the app) clears all on-device storage.

## What the app does not collect

The current version of the app does **not** request or collect:
- Precise or approximate location
- Camera, microphone, photo library, or media access
- Contacts, calendar, or call/SMS data
- Health, fitness, or financial data
- Advertising IDs

Future versions of the app may add an optional GPS-based timeclock feature for field technicians; that will be opt-in, will request the relevant Android location permission at runtime with an explanation, and will be governed by your organization's working-hours configuration on the server.

## Crash reporting

When you install the app from Google Play, Google may collect anonymized crash logs and performance diagnostics for the app, governed by Google's own policies. These are visible to the app developer through Play Console for debugging purposes only.

## Third parties

The app does not integrate any third-party SDKs that collect user data. Network traffic flows only between the device and the server URL you entered. The libraries used (React Native, Expo, axios, Tanstack Query, expo-secure-store) do not phone home.

## Data retention and deletion

- **On-device data** is retained until you sign out, clear app data through Android Settings, or uninstall the app.
- **Server-side data** is retained according to your organization's Client St0r configuration. Contact your Client St0r administrator to request export, correction, or deletion of data your organization holds about you.

## Children

The app is not intended for users under 13. We do not knowingly collect data from children.

## Permissions the app requests

| Android permission | Why |
|---|---|
| `INTERNET` | To reach the server URL you configured |
| `READ_EXTERNAL_STORAGE` / `WRITE_EXTERNAL_STORAGE` | Required by some Expo modules; the app does not read your photos or files |
| `SYSTEM_ALERT_WINDOW` | Required by some Expo modules; the app does not draw over other apps |
| `VIBRATE` | Haptic feedback on UI interactions |

## Changes to this policy

If we materially change how the app handles data, we will update this page and bump the "Last updated" date. The version of the policy that applies to your install is the one published at the time you obtained the app.

## Contact

For privacy questions about the **app itself** (not your organization's server data), open an issue at <https://github.com/agit8or1/clientst0r/issues>.

For privacy questions about **data your organization holds in its Client St0r server**, contact that organization directly.
