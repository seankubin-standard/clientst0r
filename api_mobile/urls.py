"""
Mobile API URL config — `/api/mobile/v1/`.
"""
from django.urls import path

from . import (
    views_assets,
    views_auth,
    views_dashboard,
    views_field_ops,
    views_kb,
    views_tickets,
    views_vault,
)

app_name = 'api_mobile'

urlpatterns = [
    # Auth (v3.17.346)
    path('auth/login/', views_auth.login_view, name='login'),
    path('auth/mfa/', views_auth.mfa_view, name='mfa'),
    path('auth/logout/', views_auth.logout_view, name='logout'),
    path('auth/me/', views_auth.me_view, name='me'),
    path('auth/refresh/', views_auth.refresh_view, name='refresh'),

    # Dashboard + organizations (v3.17.347)
    path('dashboard/', views_dashboard.dashboard_view, name='dashboard'),
    path('organizations/', views_dashboard.organization_list_view, name='org_list'),
    path('organizations/<int:pk>/', views_dashboard.organization_detail_view, name='org_detail'),

    # Assets (v3.17.348)
    path('assets/', views_assets.asset_list_view, name='asset_list'),
    path('assets/<int:pk>/', views_assets.asset_detail_view, name='asset_detail'),

    # Tickets (v3.17.349)
    path('tickets/', views_tickets.ticket_list_view, name='ticket_list'),
    path('tickets/<int:pk>/', views_tickets.ticket_detail_view, name='ticket_detail'),
    path('tickets/<int:pk>/comments/', views_tickets.ticket_comment_view, name='ticket_comment'),
    path('tickets/<int:pk>/time/', views_tickets.ticket_time_view, name='ticket_time'),

    # KB / docs (v3.17.350)
    path('kb/', views_kb.kb_list_view, name='kb_list'),
    path('kb/<int:pk>/', views_kb.kb_detail_view, name='kb_detail'),

    # Vault (v3.17.449)
    path('vault/', views_vault.vault_list_view, name='vault_list'),
    path('vault/<int:pk>/', views_vault.vault_detail_view, name='vault_detail'),
    path('vault/<int:pk>/reveal/', views_vault.vault_reveal_view, name='vault_reveal'),

    # Field Ops — Phase 8 (v3.17.410)
    path('locations/', views_field_ops.location_ping_view, name='location_ping'),
    path('timeclock/clock-in/', views_field_ops.clock_in_view, name='clock_in'),
    path('timeclock/clock-out/', views_field_ops.clock_out_view, name='clock_out'),
    path('timeclock/me/', views_field_ops.timeclock_me_view, name='timeclock_me'),
    path('active-ticket/', views_field_ops.active_ticket_view, name='active_ticket'),
]
