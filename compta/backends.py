from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile


class CodeAuthenticationBackend(BaseBackend):
    """
    Custom authentication backend that authenticates users with their unique code
    """
    
    def authenticate(self, request, code=None, **kwargs):
        if code is None:
            return None
        
        try:
            # Find user profile with matching code
            profile = UserProfile.objects.select_related('user').get(code=code)
            user = profile.user
            
            # Check if user is active
            if user.is_active:
                # Update last login time
                profile.last_login_code = timezone.now()
                profile.save()
                return user
                
        except UserProfile.DoesNotExist:
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
