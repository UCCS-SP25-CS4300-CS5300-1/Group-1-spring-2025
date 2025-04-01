from django.urls import path, include
from .views import index, ProfileSettings, register
from django.contrib.auth.views import LogoutView
from . import views


urlpatterns = [
	path('', index, name='index'),
	path('select2/', include('django_select2.urls')),
	path('profile_settings/', ProfileSettings.as_view(), name='profile_settings'),
	path('logout/', LogoutView.as_view(), name='logout'),
	path('register/', register, name='register'),
	path('tasks/', views.task_view, name='task_view'),
	path('tasks/delete/<int:task_id>/', views.delete_task, name='delete_task'),
	path('tasks/add/', views.add_task, name='add_task'),
	path('tasks/share/<int:task_id>', views.share_task, name='share_task'),
	path('tasks/accept/<int:request_id>/', views.accept_task, name='accept_task'),
]