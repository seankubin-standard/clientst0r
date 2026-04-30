from django import forms
from .models import SecurityVendorConnection, SecurityAlertRule


class SecurityVendorConnectionForm(forms.ModelForm):
    class Meta:
        model = SecurityVendorConnection
        fields = [
            'name', 'provider', 'category', 'client_org',
            'base_url', 'credentials_encrypted',
            'poll_interval_minutes', 'is_active', 'sync_enabled', 'notes',
        ]
        widgets = {
            'credentials_encrypted': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class SecurityAlertRuleForm(forms.ModelForm):
    class Meta:
        model = SecurityAlertRule
        fields = [
            'name', 'is_active', 'priority',
            'match_provider', 'match_category', 'match_severity_min',
            'match_client_org',
            'action', 'ticket_queue_id', 'ticket_priority_code', 'ticket_assignee',
            'suppress_start_hour', 'suppress_end_hour',
            'notes',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
