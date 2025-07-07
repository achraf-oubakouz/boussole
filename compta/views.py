from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
import json
from .models import UploadedFile, FinancialEntry
from .forms import FileUploadForm, CodeLoginForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import user_passes_test


@login_required
def dashboard(request):
    """Main dashboard view showing financial data overview"""
    # Get recent uploads
    recent_uploads = UploadedFile.objects.filter(processed=True)[:5]
    
    # Get summary statistics
    total_entries = FinancialEntry.objects.count()
    total_income = FinancialEntry.objects.filter(entry_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = FinancialEntry.objects.filter(entry_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses
    
    # Get monthly data for charts (last 12 months)
    twelve_months_ago = timezone.now() - timedelta(days=365)
    
    try:
        # Use TruncMonth for better database compatibility
        from django.db.models.functions import TruncMonth
        
        monthly_data = FinancialEntry.objects.filter(
            date__gte=twelve_months_ago
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            income=Sum('amount', filter=Q(entry_type='income')),
            expenses=Sum('amount', filter=Q(entry_type='expense'))
        ).order_by('month')
        
        # Prepare chart data
        chart_data = {
            'labels': [item['month'].strftime('%Y-%m') if item['month'] else '' for item in monthly_data],
            'income': [float(item['income'] or 0) for item in monthly_data],
            'expenses': [float(item['expenses'] or 0) for item in monthly_data],
        }
        
        # Debug: print the query results
        print(f"Monthly data query returned {len(monthly_data)} months")
        print(f"Chart data: {chart_data}")
        
    except Exception as e:
        # Fallback data if there's an error with the query
        print(f"Error getting chart data: {e}")
        
        # Let's try a simpler approach as fallback
        try:
            # Get all entries for chart (simplified)
            all_entries = FinancialEntry.objects.filter(date__gte=twelve_months_ago)
            print(f"Found {all_entries.count()} entries for chart")
            
            # Group by month manually
            monthly_summary = {}
            for entry in all_entries:
                month_key = entry.date.strftime('%Y-%m')
                if month_key not in monthly_summary:
                    monthly_summary[month_key] = {'income': 0, 'expenses': 0}
                
                if entry.entry_type == 'income':
                    monthly_summary[month_key]['income'] += float(entry.amount)
                else:
                    monthly_summary[month_key]['expenses'] += float(entry.amount)
            
            # Sort by month
            sorted_months = sorted(monthly_summary.keys())
            
            chart_data = {
                'labels': sorted_months,
                'income': [monthly_summary[month]['income'] for month in sorted_months],
                'expenses': [monthly_summary[month]['expenses'] for month in sorted_months],
            }
            print(f"Fallback chart data: {chart_data}")
            
        except Exception as e2:
            print(f"Even fallback failed: {e2}")
            chart_data = {
                'labels': [],
                'income': [],
                'expenses': [],
            }
    
    context = {
        'recent_uploads': recent_uploads,
        'total_entries': total_entries,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'chart_data': json.dumps(chart_data),
    }
    
    return render(request, 'compta/dashboard.html', context)


@login_required
def upload_file(request):
    """Handle file upload and processing"""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save(commit=False)
            if request.user.is_authenticated:
                uploaded_file.uploaded_by = request.user
            else:
                # For testing purposes, use the first superuser
                from django.contrib.auth.models import User
                uploaded_file.uploaded_by = User.objects.filter(is_superuser=True).first()
            
            # Determine file type
            file_name = uploaded_file.file.name.lower()
            if file_name.endswith(('.xlsx', '.xls')):
                uploaded_file.file_type = 'excel'
            elif file_name.endswith('.csv'):
                uploaded_file.file_type = 'csv'
            
            uploaded_file.save()
            
            # Process the file
            try:
                process_uploaded_file(uploaded_file)
                messages.success(request, f'Fichier "{uploaded_file.name}" importé et traité avec succès!')
                return redirect('compta:dashboard')
            except Exception as e:
                messages.error(request, f'Erreur lors du traitement du fichier: {str(e)}')
                uploaded_file.delete()  # Clean up failed import
        else:
            messages.error(request, 'Erreur dans le formulaire. Veuillez vérifier les données.')
    else:
        form = FileUploadForm()
    
    return render(request, 'compta/upload.html', {'form': form})


def process_uploaded_file(uploaded_file):
    """Process uploaded Excel/CSV file and create FinancialEntry objects"""
    file_path = uploaded_file.file.path
    
    try:
        # Read file based on type
        if uploaded_file.file_type == 'excel':
            df = pd.read_excel(file_path)
        else:  # CSV
            df = pd.read_csv(file_path)
        
        # Expected columns (case insensitive matching)
        expected_columns = {
            'date': ['date', 'Date', 'DATE', 'date_operation', 'Date_operation'],
            'description': ['description', 'Description', 'DESCRIPTION', 'libelle', 'Libelle', 'LIBELLE'],
            'amount': ['amount', 'Amount', 'AMOUNT', 'montant', 'Montant', 'MONTANT'],
            'type': ['type', 'Type', 'TYPE', 'sens', 'Sens', 'SENS']
        }
        
        # Map actual columns to expected ones
        column_mapping = {}
        for expected, variants in expected_columns.items():
            for variant in variants:
                if variant in df.columns:
                    column_mapping[expected] = variant
                    break
        
        if len(column_mapping) < 3:  # At least date, description, amount
            raise ValueError("Le fichier doit contenir au moins les colonnes: Date, Description, Montant")
        
        # Process each row
        entries_created = 0
        for index, row in df.iterrows():
            try:
                # Parse date
                date_value = pd.to_datetime(row[column_mapping['date']]).date()
                
                # Get description
                description = str(row[column_mapping['description']])
                
                # Get amount
                amount = float(row[column_mapping['amount']])
                
                # Determine entry type
                entry_type = 'expense'  # Default
                if 'type' in column_mapping:
                    type_value = str(row[column_mapping['type']]).lower()
                    if type_value in ['recette', 'income', 'credit', 'crédit']:
                        entry_type = 'income'
                elif amount > 0:
                    entry_type = 'income'
                else:
                    amount = abs(amount)  # Make amount positive
                    entry_type = 'expense'
                
                # Create FinancialEntry
                FinancialEntry.objects.create(
                    uploaded_file=uploaded_file,
                    date=date_value,
                    description=description,
                    amount=abs(amount),
                    entry_type=entry_type
                )
                entries_created += 1
                
            except Exception as row_error:
                print(f"Erreur ligne {index + 2}: {row_error}")
                continue
        
        # Mark file as processed
        uploaded_file.processed = True
        uploaded_file.processed_at = timezone.now()
        uploaded_file.save()
        
        # Clear admin cache to update counters
        from django.core.cache import cache
        cache.delete('admin_financialentry_count')
        cache.delete('admin_stats_context')
        
        print(f"Fichier traité: {entries_created} entrées créées")
        
    except Exception as e:
        raise Exception(f"Erreur lors du traitement du fichier: {str(e)}")


@login_required
def entries_list(request):
    """Display list of all financial entries"""
    entries = FinancialEntry.objects.select_related('uploaded_file').order_by('-date')
    
    # Filter by type if requested
    entry_type = request.GET.get('type')
    if entry_type in ['income', 'expense']:
        entries = entries.filter(entry_type=entry_type)
    
    # Filter by date range if requested
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        entries = entries.filter(date__gte=date_from)
    if date_to:
        entries = entries.filter(date__lte=date_to)
    
    context = {
        'entries': entries,
        'entry_type': entry_type,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'compta/entries_list.html', context)


@login_required
def delete_upload(request, upload_id):
    """Delete an uploaded file and all its entries"""
    if request.method == 'POST':
        uploaded_file = get_object_or_404(UploadedFile, id=upload_id)
        file_name = uploaded_file.name
        uploaded_file.delete()  # This will also delete related entries due to CASCADE
        messages.success(request, f'Fichier "{file_name}" supprimé avec succès!')
    
    return redirect('compta:dashboard')


def code_login(request):
    """Custom login view using authentication codes"""
    # Redirect to dashboard if already authenticated
    if request.user.is_authenticated:
        return redirect('compta:dashboard')
    
    if request.method == 'POST':
        form = CodeLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Redirect to next URL or dashboard
            next_url = request.GET.get('next', 'compta:dashboard')
            return redirect(next_url)
    else:
        form = CodeLoginForm(request)
    
    return render(request, 'compta/login.html', {'form': form})


@login_required
def user_logout(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('compta:login')
