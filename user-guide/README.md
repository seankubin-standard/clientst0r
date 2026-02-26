# ClientSt0r User Guide

ClientSt0r is a self-hosted IT management platform for MSPs and IT teams — combining asset inventory, a password vault, fleet management, WAN monitoring, and security tooling, all scoped per organization.

> **In-app help** is also available at `/help/` once logged in.

---

## Sections

| Section | Description |
|---------|-------------|
| [Getting Started](getting-started.md) | Organizations, users, roles, API keys |
| [Asset Management](asset-management.md) | Hardware inventory, networks, racks, port configuration |
| [Service Vehicles](service-vehicles.md) | Fleet tracking, maintenance, fuel logs, damage reports |
| [Password Vault](password-vault.md) | AES-256 encrypted credentials, TOTP, breach detection |
| [WAN Monitoring](wan-monitoring.md) | HTTP/TCP/ICMP checks, SSL expiry, alerting |
| [Security](security.md) | Vulnerability scanning, RBAC, audit logs, 2FA |
| [Reports & Analytics](reports.md) | Custom dashboards, report templates, scheduled reports |
| [Workflows](workflows.md) | Step-by-step checklists and process executions |
| [Documentation & KB](documentation.md) | Runbooks, knowledge base, diagrams, AI assistant |
| [Locations & WAN](locations.md) | Physical sites and WAN connection management |
| [API & Integrations](api.md) | REST API, webhooks, RMM integrations |

---

## Architecture

```
All data is organization-scoped.
Every asset, password, vehicle, and monitor belongs to one organization.
Users can belong to multiple organizations with different roles in each.
```

## Role Overview

| Role | Create/Edit | Delete | Manage Users | Org Settings |
|------|:-----------:|:------:|:------------:|:------------:|
| **Owner** | ✓ | ✓ | ✓ | ✓ |
| **Admin** | ✓ | ✓ | ✓ | — |
| **Editor** | ✓ | — | — | — |
| **Read-Only** | — | — | — | — |

Custom roles with granular permissions are also supported.

## API Authentication

```http
Authorization: Bearer itdocs_live_<your_api_key>
```

Generate keys at **Profile → API Keys**. Keys inherit your organization membership and role permissions.

---

*For installation and deployment, see [INSTALL.md](../INSTALL.md).*
