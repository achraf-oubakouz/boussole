from django.core.management.base import BaseCommand
from django.core.cache import cache
from compta.models import FinancialEntry


class Command(BaseCommand):
    help = 'Refresh admin cache and update counters'

    def handle(self, *args, **options):
        """Clear admin cache and force fresh counts"""
        
        # Clear all admin-related cache keys
        cache.delete('admin_financialentry_count')
        cache.delete('admin_stats_context')
        
        # Get fresh count to trigger cache refresh
        total_entries = FinancialEntry.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Admin cache refreshed. Total entries: {total_entries}'
            )
        )
