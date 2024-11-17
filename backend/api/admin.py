from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'product_name', 'price', 'rating', 'created_at')
    list_filter = ('company_name', 'created_at')
    search_fields = ('company_name', 'product_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20

    fieldsets = (
        ('Product Information', {
            'fields': ('company_name', 'product_name', 'price', 'rating')
        }),
        ('Reviews', {
            'fields': ('reviews',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
