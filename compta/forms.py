from django import forms
from .models import UploadedFile


class FileUploadForm(forms.ModelForm):
    """Form for uploading Excel/CSV files"""
    
    class Meta:
        model = UploadedFile
        fields = ['name', 'file']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du fichier (optionnel)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.xlsx,.xls,.csv'
            })
        }
        labels = {
            'name': 'Nom du fichier',
            'file': 'Fichier Excel ou CSV'
        }
        help_texts = {
            'file': 'Formats acceptés: .xlsx, .xls, .csv'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = False
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            allowed_extensions = ['.xlsx', '.xls', '.csv']
            file_name = file.name.lower()
            if not any(file_name.endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError('Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv')
            
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Le fichier est trop volumineux. Taille maximum: 10MB')
        
        return file
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        file = self.cleaned_data.get('file')
        
        # If no name provided, use file name
        if not name and file:
            name = file.name
        
        return name
