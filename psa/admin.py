from django.contrib import admin

from .models import (
    ClientPSASettings,
    EmailMessage,
    EmailRoutingRule,
    Queue,
    Ticket,
    TicketAttachment,
    TicketComment,
    TicketPriority,
    TicketStatus,
    TicketType,
)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'organization', 'subject', 'status', 'priority', 'queue', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'queue', 'ticket_type', 'source', 'organization')
    search_fields = ('ticket_number', 'subject', 'description', 'requester_name', 'requester_email')
    raw_id_fields = ('contact', 'related_asset', 'related_documentation', 'related_kb_article',
                     'related_calendar_event', 'parent_ticket', 'duplicate_of', 'assigned_to',
                     'created_by', 'updated_by')
    date_hierarchy = 'created_at'


admin.site.register(ClientPSASettings)
admin.site.register(Queue)
admin.site.register(TicketStatus)
admin.site.register(TicketPriority)
admin.site.register(TicketType)
admin.site.register(TicketComment)
admin.site.register(TicketAttachment)


@admin.register(EmailRoutingRule)
class EmailRoutingRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'sender_domain_glob',
                    'target_client_org', 'queue_override', 'priority_override',
                    'enabled', 'order')
    list_filter = ('enabled', 'organization', 'target_client_org')
    search_fields = ('name', 'sender_domain_glob', 'notes')
    list_editable = ('enabled', 'order')
    ordering = ('order', 'name')


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'direction', 'organization', 'ticket',
                    'from_email', 'subject', 'was_quarantined', 'received_at')
    list_filter = ('direction', 'was_quarantined', 'organization')
    search_fields = ('message_id', 'in_reply_to', 'from_email', 'subject',
                     'quarantine_reason')
    date_hierarchy = 'received_at'
    raw_id_fields = ('ticket', 'ingestion_config')
    readonly_fields = ('received_at',)
