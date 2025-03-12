from django.urls import path, include
from .views import index, ProfileSettings, register
from django.contrib.auth.views import LogoutView

urlpatterns = [
	path('', index, name='index'),
	path('profile_settings/', ProfileSettings.as_view(), name='profile_settings'),
	path('logout/', LogoutView.as_view(), name='logout'),
	path('register/', register, name='register'),
]