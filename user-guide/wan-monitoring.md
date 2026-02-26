# WAN Monitoring

Monitor external, internet-facing endpoints — HTTP/S, TCP ports, ICMP, DNS, and SSL certificate expiry — with automatic alerting.

> **Scope:** WAN monitoring checks **outbound** connectivity from the ClientSt0r server to public or remotely-accessible endpoints. It is not an internal infrastructure monitoring tool.

---

## Overview

| Feature | Details |
|---------|---------|
| **Check interval** | Configurable per monitor (1–60 minutes) |
| **Multi-org** | Each organization has its own monitors |
| **Status dashboard** | Green/red status with 30-day uptime percentage |
| **History** | Full response-time and status history |
| **Alerting** | Email and webhook notifications on state change |

---

## Monitor Types

| Type | What It Checks |
|------|---------------|
| **HTTP** | Returns 2xx/3xx; optionally match body keyword |
| **HTTPS** | Same as HTTP + validates SSL certificate |
| **TCP Port** | Connection accepted on specified port |
| **ICMP Ping** | Host responds to ping |
| **DNS** | DNS resolution succeeds; optionally validate resolved IP |
| **SSL Certificate** | Certificate validity and expiry countdown |

### Creating a Monitor

1. Go to *Monitoring → New Monitor*
2. Select the monitor type
3. Enter the target URL, hostname, or IP
4. Set check interval and alert threshold (e.g., 3 consecutive failures before alert)
5. Add notification recipients (email) or webhook URLs

---

## Alerting

| Alert Channel | Configuration |
|--------------|---------------|
| **Email** | Enter recipient addresses per monitor |
| **Webhook** | POST to any URL on state change (Slack, Teams, PagerDuty, custom) |

Alert events:
- `DOWN` — monitor failed (after N consecutive failures)
- `UP` — monitor recovered
- `SSL_WARNING` — certificate expires within 30 days
- `SSL_CRITICAL` — certificate expires within 7 days

### Webhook Payload

```json
{
  "event": "DOWN",
  "monitor": "Main Website",
  "url": "https://example.com",
  "status_code": null,
  "error": "Connection timed out",
  "timestamp": "2025-11-15T14:32:00Z",
  "organization": "Acme Corp"
}
```

---

## Status Dashboard

The dashboard shows all monitors for the current organization:

```
Monitor             Type    Status   Uptime (30d)   Last Check
──────────────────────────────────────────────────────────────
Main Website        HTTPS   ● UP     99.8%          2m ago
API Endpoint        HTTPS   ● UP     100%           2m ago
Customer Portal     HTTPS   ● DOWN   97.2%          just now
Mail Server         TCP     ● UP     99.9%          5m ago
Backup VPN          TCP     ● UP     100%           5m ago
```

Color coding: **green** = UP, **red** = DOWN, **amber** = degraded / warning

---

## SSL Certificate Checks

SSL monitors track certificate health independently of HTTP checks:

| Status | Condition |
|--------|-----------|
| **Valid** | Certificate is valid; shows days remaining |
| **Warning** | Expires within 30 days |
| **Critical** | Expires within 7 days |
| **Expired** | Certificate has expired |
| **Error** | Cannot validate (invalid chain, self-signed without trust) |

Certificate details shown: issuer, subject, SANs, chain validity.

---

## Incident Management

Each DOWN event creates an incident record:

| Field | Details |
|-------|---------|
| **Started** | Timestamp of first failure |
| **Resolved** | Timestamp of recovery |
| **Duration** | Total outage length |
| **Error** | HTTP status code or connection error |
| **Notes** | Free-text field for runbook links or RCA notes |

Incidents are listed per monitor and searchable across the organization. Scheduled maintenance windows suppress alerting for known downtime.

---

*Previous: [Password Vault](password-vault.md) · Next: [Security](security.md)*
