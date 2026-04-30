from django.contrib import admin
from .models import SecurityVendorConnection, SecurityAlert, SecurityAlertRule


@admin.register(SecurityVendorConnection)
class SecurityVendorConnectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'category', 'organization',
                    'client_org', 'is_active', 'last_sync_at', 'last_sync_status')
    list_filter = ('provider', 'category', 'is_active')
    search_fields = ('name', 'organization__name', 'client_org__name')


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'status', 'connection',
                    'client_org', 'seen_at', 'acknowledged_at')
    list_filter = ('severity', 'status', 'connection__provider')
    search_fields = ('title', 'asset_hint', 'description', 'external_id')


@admin.register(SecurityAlertRule)
class SecurityAlertRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'is_active', 'organization',
                    'match_provider', 'match_category', 'match_severity_min')
    list_filter = ('is_active', 'match_provider', 'match_category')
