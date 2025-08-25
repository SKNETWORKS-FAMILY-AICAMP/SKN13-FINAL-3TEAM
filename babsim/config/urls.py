from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    
    path('api/', include('JJACKLETTE.urls')),
    
    path('auth/', include('dj_rest_auth.urls')),
    
    path('auth/google/', include('allauth.socialaccount.providers.google.urls')),

]