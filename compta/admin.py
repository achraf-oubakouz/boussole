from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import UploadedFile, FinancialEntry, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


def admin_stats_context(request):
    """Provide statistics for admin templates"""
    from datetime import datetime
    from django.db.models import Count
    from django.core.cache import cache
    
    if request.path.startswith('/admin/'):
        # Use cache key for admin stats but with a short timeout
        cache_key = 'admin_stats_context'
        stats = cache.get(cache_key)
        
        if stats is None:
            total_entries = FinancialEntry.objects.count()
            processed_files = UploadedFile.objects.filter(processed=True).count()
            
            # Get current month entries
            current_month = datetime.now().month
            current_year = datetime.now().year
            monthly_entries = FinancialEntry.objects.filter(
                date__month=current_month,
                date__year=current_year
            ).count()
            
            stats = {
                'total_entries': total_entries,
                'processed_files': processed_files,
                'monthly_entries': monthly_entries,
            }
            
            # Cache for only 30 seconds to ensure fresh data
            cache.set(cache_key, stats, 30)
        
        return stats
    return {}


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
    list_display = ['date_display', 'description', 'amount', 'entry_type', 'uploaded_file', 'created_at']
    list_filter = ['entry_type', 'date', 'created_at', 'uploaded_file']
    search_fields = ['description']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    actions_on_top = True
    actions_on_bottom = True
    list_select_related = ['uploaded_file']
    
    # Enable mass selection
    def get_actions(self, request):
        actions = super().get_actions(request)
        return actions
    
    def changelist_view(self, request, extra_context=None):
        """Override changelist view to ensure fresh count"""
        extra_context = extra_context or {}
        # Force a fresh count of all entries
        extra_context['total_entries'] = FinancialEntry.objects.count()
        return super().changelist_view(request, extra_context=extra_context)
    
    def date_display(self, obj):
        """Custom date display method to ensure proper formatting"""
        if obj.date:
            return obj.date.strftime('%Y-%m-%d')
        return '-'
    date_display.short_description = 'Date'
    date_display.admin_order_field = 'date'
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('date', 'description', 'amount', 'entry_type')
        }),
    )
    readonly_fields = ['created_at', 'uploaded_file']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'created_at', 'last_login_code']
    list_filter = ['created_at', 'last_login_code']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'code']
    readonly_fields = ['created_at', 'last_login_code']
    exclude = ['created_at', 'last_login_code']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user', 'code')
        }),
    )


# Inline UserProfile in User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'
    fields = ['code']
    readonly_fields = ['created_at', 'last_login_code']
    exclude = ['created_at', 'last_login_code']


# Extend User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_code', 'is_staff', 'date_joined')
    list_filter = BaseUserAdmin.list_filter + ('profile__created_at',)
    actions_on_top = True
    actions_on_bottom = True
    
    def get_code(self, obj):
        return obj.profile.code if hasattr(obj, 'profile') else 'Aucun code'
    get_code.short_description = 'Code de connexion'
    get_code.admin_order_field = 'profile__code'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

