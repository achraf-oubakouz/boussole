from django import forms
from django.contrib.auth import authenticate
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


class CodeLoginForm(forms.Form):
    """Custom login form using authentication code"""
    
    code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Entrez votre code de connexion',
            'autocomplete': 'off',
            'autofocus': True
        }),
        label='Code de connexion'
    )
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        
        if code:
            # Authenticate using the code
            self.user_cache = authenticate(
                self.request, 
                code=code
            )
            
            if self.user_cache is None:
                raise forms.ValidationError(
                    'Code de connexion invalide.',
                    code='invalid_code'
                )
            elif not self.user_cache.is_active:
                raise forms.ValidationError(
                    'Ce compte utilisateur est désactivé.',
                    code='inactive'
                )
        
        return code
    
    def get_user(self):
        return self.user_cache
