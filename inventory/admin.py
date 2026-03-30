from django.contrib import admin
from .models import InventoryCategory, InventoryLocation, InventoryItem, InventoryTransaction

admin.site.register(InventoryCategory)
admin.site.register(InventoryLocation)
admin.site.register(InventoryItem)
admin.site.register(InventoryTransaction)
