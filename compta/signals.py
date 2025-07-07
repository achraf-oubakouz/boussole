from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import FinancialEntry


@receiver(post_save, sender=FinancialEntry)
def clear_admin_cache_on_entry_save(sender, instance, created, **kwargs):
    """Clear admin cache when a new entry is created"""
    if created:
        # Clear any cached counts
        cache.delete('admin_financialentry_count')
        cache.delete('admin_stats_context')


@receiver(post_delete, sender=FinancialEntry)
def clear_admin_cache_on_entry_delete(sender, instance, **kwargs):
    """Clear admin cache when an entry is deleted"""
    # Clear any cached counts
    cache.delete('admin_financialentry_count')
    cache.delete('admin_stats_context')
