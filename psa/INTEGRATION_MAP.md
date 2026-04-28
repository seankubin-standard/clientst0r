# PSA Integration Map

Output of Phase 0 repo discovery — the canonical reference for which existing
models the native PSA hooks into and how. Update this document when the
upstream models change.

## Distinction from `integrations.PSATicket`

There are TWO PSA-related model namespaces and they must NOT be conflated:

| | `integrations/` | `psa/` (this app) |
|---|---|---|
| Purpose | Mirror tickets synced FROM external PSAs (Halo, Autotask, ConnectWise, …) | The native, in-product service desk |
| Owner of source-of-truth | Third-party PSA platform | This app |
| `db_table` | `psa_tickets`, `psa_companies`, `psa_contacts`, `psa_connections` | `psa_native_tickets`, `psa_ticket_*`, `psa_queues`, `psa_client_settings` |
| `Organization` related_name | `psa_tickets`, `psa_companies`, `psa_contacts` | `native_psa_tickets` |

## Foreign-key targets

| PSA field | Existing model | File | Related-name on the existing model |
|---|---|---|---|
| `Ticket.organization` | `core.Organization` | `core/models.py:10` | `native_psa_tickets` |
| `Ticket.contact` | `assets.Contact` | `assets/models.py:10` | `native_psa_tickets` |
| `Ticket.assigned_to` / `created_by` / `updated_by` | `auth.User` (no AUTH_USER_MODEL override) | django builtin | `psa_assigned_tickets`, `psa_tickets_created`, `psa_tickets_updated` |
| `Ticket.related_asset` | `assets.Asset` | `assets/models.py:77` | `native_psa_tickets` |
| `Ticket.related_documentation` | `docs.Document` | `docs/models.py:43` | `native_psa_doc_tickets` |
| `Ticket.related_kb_article` | `docs.Document` (with `is_global=True`) | same | `native_psa_kb_tickets` |
| `Ticket.related_calendar_event` | `scheduling.ScheduledTask` | `scheduling/models.py:12` | `native_psa_tickets` |

## Tenant isolation

- `core.middleware.CurrentOrganizationMiddleware` sets `request.current_organization`.
- `core.middleware.get_request_organization(request)` is the canonical helper.
- All PSA querysets must be scoped via `_scoped_ticket_qs(request)` (see `psa/views.py`) to enforce per-org visibility.
- Superusers and `request.is_staff_user` users can cross tenants in "global view"; org users cannot.

## RBAC

- Roles live on `accounts.Membership` (`role` choices: `admin`, `editor`, `owner`, `readonly`).
- Decorators in `core/decorators.py`:
  - `@require_write` — Editor and above
  - `@require_admin` — Admin and above
  - `@require_owner` — Owner only
  - `@require_organization_context` — ensures `request.current_organization` is set
- PSA Phase 1 uses `@require_write` for ticket creation. Phase 2 will introduce per-PSA-action permissions on `accounts.RoleTemplate`.

## Audit log

- Model: `audit.AuditLog` (`audit/models.py:9`)
- Helper: `AuditLog.log(user, action, organization=..., object_type='psa.Ticket', object_id=..., object_repr=..., description=..., ip_address=..., path=..., extra_data=...)`
- Every PSA mutation must call `AuditLog.log(...)` — verified by `psa/tests.py::test_audit_log_written_on_create_via_view`.
- The project also has `audit.middleware.AuditLoggingMiddleware`, which auto-logs request-level events; PSA tests assert ≥1 explicit PSA-scoped log rather than exact count to coexist with it.

## Vault integration (Phase 1 wiring; Phase 5+ deepens it)

- Model: `vault.Password` (`vault/models.py:59`), tenant FK `organization`.
- Encryption: `vault/encryption_v2.py` (AES-256-GCM, HKDF, AAD bound).
- Permission model: per-org via `OrganizationManager`; per-user "personal vault" via `is_personal` + `personal_owner`.
- Audit hook: `vault/views.py:226` writes `AuditLog(action='read', ...)` on every reveal.
- Detail URL: `vault:password_detail` (`<int:pk>/`).
- **Rule:** secret values are NEVER serialised into PSA models, comments, or notifications. PSA surfaces vault entries as deep-link references to the existing `vault:password_detail` view, which enforces its own permission stack.

## Feature flags

- System-wide: `core.SystemSetting.psa_enabled` (default `False`).
- Per-tenant: `psa.ClientPSASettings.enabled` (default `False`) plus per-surface flags (portal, anonymous form, email-to-ticket, SMS, desktop alerts, external alert ingest — all default `False`).
- Helpers: `psa.feature_flags.is_psa_enabled()`, `is_psa_enabled_for_client(org)`.
- Decorators: `@require_psa_enabled`, `@require_client_psa_enabled` — both 404 (not redirect) when disabled.
- Template flag: `psa_enabled` exposed via `core/context_processors.py:organization_context`.
- Sidebar entry in `templates/base.html` is wrapped in `{% if psa_enabled %}`.

## API

- Framework: DRF (`djangorestframework==3.15.*`).
- Auth: custom `APIKeyAuthentication` + `SessionAuthentication`, defined in `api/authentication.py`.
- Base viewset: `api/views.py:OrganizationScopedViewSet` — auto-filters by `request.current_organization`.
- PSA API endpoints land in `api/psa/` in Phase 7+.

## Calendar

- Model: `scheduling.ScheduledTask` (`scheduling/models.py:12`), tenant FK `organization`.
- Recurrence: `recurrence` + `recurrence_interval_days` + `spawn_next_occurrence()`.
- Reminder fields: `alert_email`, `alert_sms`, `alert_before_hours`, `last_alert_sent_at`.
- Already has a `psa_ticket` FK toward `integrations.PSATicket` — the native FK to `psa.Ticket` is added by `Ticket.related_calendar_event`.

## Notifications

- No general user-notification model exists today.
- Email: Django `send_mail()` (see `core/management/commands/run_scheduler.py` vault password expiry path for the canonical pattern).
- Webhooks: `core.Webhook` + `core.WebhookDelivery`.
- Audit trail: every action records to `audit.AuditLog`.

## Phase boundaries

This map covers Phase 1 only. Each subsequent phase will append a new section.
