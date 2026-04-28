from django.contrib import admin

from .models import (
    ClientPSASettings,
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
