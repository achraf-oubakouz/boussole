from django.urls import path
from . import views

app_name = 'compta'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_file, name='upload'),
    path('entries/', views.entries_list, name='entries_list'),
    path('delete/<int:upload_id>/', views.delete_upload, name='delete_upload'),
]
