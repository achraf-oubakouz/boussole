from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class UploadedFile(models.Model):
    """Model to store information about uploaded Excel/CSV files"""
    
    FILE_TYPES = [
        ('excel', 'Excel (.xlsx, .xls)'),
        ('csv', 'CSV (.csv)'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Nom du fichier")
    file = models.FileField(upload_to='uploads/', verbose_name="Fichier")
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, verbose_name="Type de fichier")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Uploadé par")
    uploaded_at = models.DateTimeField(default=timezone.now, verbose_name="Date d'upload")
    processed = models.BooleanField(default=False, verbose_name="Traité")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de traitement")
    
    class Meta:
        verbose_name = "Fichier importé"
        verbose_name_plural = "Fichiers importés"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_file_type_display()})"


class FinancialEntry(models.Model):
    """Model to store individual financial entries from uploaded files"""
    
    ENTRY_TYPES = [
        ('income', 'Recette'),
        ('expense', 'Dépense'),
    ]
    
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='entries', verbose_name="Fichier source")
    date = models.DateField(verbose_name="Date")
    description = models.CharField(max_length=500, verbose_name="Description")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES, verbose_name="Type")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Écriture comptable"
        verbose_name_plural = "Écritures comptables"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.date} - {self.description} ({self.amount} DH)"


class UserProfile(models.Model):
    """Extended user profile with login code"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    code = models.CharField(max_length=20, unique=True, verbose_name="Code de connexion")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    last_login_code = models.DateTimeField(null=True, blank=True, verbose_name="Dernière connexion")
    
    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateur"
    
    def __str__(self):
        return f"{self.user.username} - {self.code}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)


