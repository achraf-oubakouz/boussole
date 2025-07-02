from django.contrib import admin
from .models import UploadedFile, FinancialEntry, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_type', 'uploaded_by', 'uploaded_at', 'processed', 'entries_count']
    list_filter = ['file_type', 'processed', 'uploaded_at']
    search_fields = ['name', 'uploaded_by__username']
    readonly_fields = ['uploaded_at', 'processed_at']
    ordering = ['-uploaded_at']
    
    def entries_count(self, obj):
        return obj.entries.count()
    entries_count.short_description = 'Nombre d\'entrées'


@admin.register(FinancialEntry)
class FinancialEntryAdmin(admin.ModelAdmin):
    list_display = ['date', 'description', 'amount', 'entry_type', 'category', 'uploaded_file', 'created_at']
    list_filter = ['entry_type', 'date', 'created_at', 'uploaded_file']
    search_fields = ['description', 'category']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('date', 'description', 'amount', 'entry_type')
        }),
        ('Catégorisation', {
            'fields': ('category',)
        }),
        ('Métadonnées', {
            'fields': ('uploaded_file', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
