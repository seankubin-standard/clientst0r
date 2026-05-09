# Play Console — Data Safety Form Answers

This is a fill-in guide for Play Console's **App content → Data safety** questionnaire. Answers are based on what the current AAB (`v3.17.446` / `versionCode 3170446`) actually does. If you ship a future version that adds GPS, camera, or push notifications, revisit this doc and update the form.

The questionnaire is six sections in Play Console; this doc mirrors them.

---

## Section 1 — Data collection and security

> Does your app collect or share any of the required user data types?
**Answer: Yes.**

(The app sends auth credentials and basic profile info to the user-configured server, so even though *you* don't centrally collect anything, Play Console counts that as "collected.")

> Is all of the user data collected by your app encrypted in transit?
**Answer: Yes.** All API traffic uses TLS (HTTPS) to the user-configured server.

> Do you provide a way for users to request that their data is deleted?
**Answer: Yes — through their Client St0r administrator.**

In the free-text "How users can request data deletion": *"Client St0r is self-hosted; contact your organization's Client St0r administrator to request export or deletion of data on the server. On-device app data is cleared by signing out, clearing app data in Android Settings, or uninstalling the app."*

---

## Section 2 — Data types collected

For each row below, mark **Collected** if listed, **Not collected** otherwise. Anything marked "Collected" requires the follow-up answers in Section 3.

### Personal info
| Type | Status | Notes |
|---|---|---|
| Name | **Collected** | User's full name returned by the server's `/auth/me/` endpoint, cached locally |
| Email address | **Collected** | Used for login (sent to server), cached locally |
| User IDs | **Collected** | Auth token + user ID returned by server, cached locally |
| Address | Not collected | |
| Phone number | Not collected | |
| Race and ethnicity | Not collected | |
| Political or religious beliefs | Not collected | |
| Sexual orientation | Not collected | |
| Other personal info | Not collected | |

### Financial info
| Type | Status |
|---|---|
| User payment info | Not collected |
| Purchase history | Not collected |
| Credit score | Not collected |
| Other financial info | Not collected |

### Health and fitness
All **Not collected**.

### Messages
| Type | Status | Notes |
|---|---|---|
| Emails | Not collected | |
| SMS or MMS | Not collected | |
| Other in-app messages | **Collected** | Ticket comments the user types are sent to the server |

### Photos and videos
All **Not collected**.

### Audio files
All **Not collected**.

### Files and docs
| Type | Status |
|---|---|
| Files and docs | Not collected |

(KB articles and ticket attachments are *displayed* but not collected as user data — they are content the server already has.)

### Calendar
**Not collected.**

### Contacts
**Not collected.**

### App activity
| Type | Status | Notes |
|---|---|---|
| App interactions | **Collected** | The server's audit log records actions like ticket views, vault reveals |
| In-app search history | **Collected** | KB and ticket search queries are sent to the server |
| Installed apps | Not collected | |
| Other user-generated content | **Collected** | Ticket comments and updates the user creates |
| Other actions | Not collected | |

### Web browsing
**Not collected.**

### App info and performance
| Type | Status | Notes |
|---|---|---|
| Crash logs | **Collected** | Google Play collects these from signed AABs by default; we ship R8 mapping for symbolication |
| Diagnostics | **Collected** | Same — collected by Play Console, not by the app code |
| Other app performance data | Not collected | |

### Device or other IDs
| Type | Status | Notes |
|---|---|---|
| Device or other IDs | **Collected** | The server's audit log records the request IP address (treated as a device identifier under Play's broad definition) |

### Authentication info (covered separately below — note: not in the standard "user data" categories but Play asks)
- Passwords: **transmitted to user-configured server**, **not stored on device**

---

## Section 3 — For each "Collected" data type

Play Console asks the same four questions per type. The answers below apply to **every** collected type unless noted:

| Question | Answer |
|---|---|
| Is this data collected, shared, or both? | **Collected** (the app does not share with third parties; it sends data only to the server URL the user enters, which is the user's own infrastructure) |
| Is this data processed ephemerally? | **No** (it's stored on the user's server) |
| Is this data required or optional for the user? | **Required** (the app does not function without authentication) |
| Why is this data collected? | **App functionality** + **Account management** for personal info / IDs / messages / app activity. **Analytics** is also OK to check for crash logs and diagnostics. **Do not** check Advertising, Personalization, Fraud prevention, Compliance, or Developer communications — none of those apply. |

### Specifically for Crash logs and Diagnostics
- Collected: **Yes**
- Shared: **No**
- Processed ephemerally: **No**
- Required or optional: **Optional** (Play allows users to opt out of usage and diagnostics in Android Settings)
- Why collected: **App functionality** + **Analytics**

### Specifically for Device or other IDs (IP address)
- Collected: **Yes**
- Shared: **No**
- Processed ephemerally: **No**
- Required or optional: **Required**
- Why collected: **App functionality** + **Fraud prevention, security, and compliance** (the audit log exists for security/compliance purposes)

---

## Section 4 — Security practices

| Question | Answer |
|---|---|
| Is all data encrypted in transit? | **Yes** (TLS/HTTPS to the user-configured server) |
| Do you provide a way for users to request data deletion? | **Yes** (deletion request flow described in Section 1 above) |
| Have you committed to following Google Play's Families Policy? | **No** (the app is not directed at children) |
| Has your app been independently validated against a global security standard? | **No** (leave unchecked unless you actually have a SOC 2 / ISO 27001 attestation specifically for this app) |

---

## Section 5 — Data sharing

> Does your app share any of the required user data with third parties?
**Answer: No.**

The app sends data only to the server URL the user enters at login. That server is operated by the user's organization, not by a third party. The app does not include any third-party SDKs that exfiltrate data (no analytics, no advertising, no crash reporting beyond what Google Play provides automatically).

---

## Section 6 — Data deletion

> How can users request that you delete their data?

**Answer (free-text):**
*"Client St0r is a self-hosted application. The mobile app does not store user data on any infrastructure operated by the developer — all data is held by the user's organization on the Client St0r server they have deployed. To request deletion of data the organization holds, the user contacts their Client St0r administrator. To clear app data on the device, the user signs out of the app, clears app data through Android Settings, or uninstalls the app."*

---

## What to paste into "Privacy policy URL"

If you wire up the privacy policy as a Django route on huduglue (next step), use:
```
https://huduglue.agit8or.net/privacy-policy/
```

If you host it elsewhere (GitHub Pages, static site, Notion public page), paste that URL instead. The URL must:
- Be reachable without authentication
- Be reachable from outside your network
- Stay live for as long as the app is on Play Store

---

## When you have to revisit this

Update this doc and re-fill the Play Console questionnaire whenever:
- You ship a build that adds **location** (GPS-based timeclock — Sub-phase 8.2)
- You ship a build that adds **camera** (asset-photo capture, signature capture, etc.)
- You ship a build that adds **push notifications** (FCM)
- You add a third-party SDK (analytics, error tracking like Sentry, ad networks)
- The app starts collecting any of the "Not collected" data types above
