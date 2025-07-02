from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
        verbose_name = "Fichier uploadé"
        verbose_name_plural = "Fichiers uploadés"
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
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="Catégorie")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Écriture comptable"
        verbose_name_plural = "Écritures comptables"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.date} - {self.description} ({self.amount} DH)"


class Category(models.Model):
    """Model to manage expense/income categories"""
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    color = models.CharField(max_length=7, default='#007bff', verbose_name="Couleur", help_text="Code couleur hexadécimal pour les graphiques")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
