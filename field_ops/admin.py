"""
Admin registration for field_ops models.
"""
from django.contrib import admin

from .models import ClientSiteGeofence, TechnicianLocation


@admin.register(TechnicianLocation)
class TechnicianLocationAdmin(admin.ModelAdmin):
    list_display = ('tech', 'lat', 'lon', 'accuracy', 'timestamp', 'source', 'retention_until')
    list_filter = ('source',)
    search_fields = ('tech__username', 'tech__email')
    date_hierarchy = 'timestamp'
    readonly_fields = ('tech', 'lat', 'lon', 'accuracy', 'timestamp', 'source', 'retention_until')


@admin.register(ClientSiteGeofence)
class ClientSiteGeofenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'kind', 'radius_meters', 'active')
    list_filter = ('kind', 'active')
    search_fields = ('name', 'organization__name')
