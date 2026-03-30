"""
Inventory forms
"""
from django import forms
from .models import InventoryItem, InventoryCategory, InventoryLocation, InventoryTransaction


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            'name', 'sku', 'manufacturer_part_number', 'item_type',
            'category', 'storage_location', 'description', 'notes',
            'quantity', 'unit', 'min_quantity', 'reorder_quantity',
            'reorder_link', 'unit_cost',
        ]

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org', None)
        super().__init__(*args, **kwargs)
        if org:
            self.fields['category'].queryset = InventoryCategory.objects.for_organization(org)
            self.fields['storage_location'].queryset = InventoryLocation.objects.for_organization(org)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class InventoryAdjustForm(forms.Form):
    transaction_type = forms.ChoiceField(choices=InventoryTransaction.TRANSACTION_TYPES)
    quantity_change = forms.IntegerField(
        help_text='Use positive number to add stock, negative to remove.'
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    reference = forms.CharField(max_length=255, required=False, help_text='Reference number, ticket, PO, etc.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class InventoryCategoryForm(forms.ModelForm):
    class Meta:
        model = InventoryCategory
        fields = ['name', 'description', 'color']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class InventoryLocationForm(forms.ModelForm):
    class Meta:
        model = InventoryLocation
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
