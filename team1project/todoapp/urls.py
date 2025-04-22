from django.urls import path, include
from .views import index, ProfileSettings, EditProfile, register, task_archive
from django.contrib.auth.views import LogoutView
from . import views


urlpatterns = [
	path('', index, name='index'),
	path('select2/', include('django_select2.urls')),
	path('profile_settings/', ProfileSettings.as_view(), name='profile_settings'),
	path('logout/', LogoutView.as_view(), name='logout'),
	path('register/', register, name='register'),
	path('tasks/', views.task_view, name='task_view'),
	path('task_archive/', task_archive, name='task_archive'),
	path('tasks/delete/<int:task_id>/', views.delete_task, name='delete_task'),
	path('tasks/archive/<int:task_id>/', views.archive_task, name='archive_task'),
	path('tasks/restore/<int:task_id>/', views.restore_task, name='restore_task'),
	path('tasks/add/', views.add_task, name='add_task'),
	path('tasks/edit/<int:task_id>/', views.edit_task, name='edit_task'),
	path('tasks/share/<int:task_id>', views.share_task, name='share_task'),
	path('shared_task/<int:task_id>', views.shared_task_view, name='shared_task_view'),
	path('shared_task/accept_request_link/<int:task_id>', views.accept_task_link, name='accept_request_link'),
	path('tasks/accept/<int:request_id>/', views.accept_task, name='accept_task'),
	path('tasks/exit/<int:task_id>/', views.exit_task, name='exit_task'),
	path('webpush/', include('webpush.urls')),
	path('home/', views.calender_view , name='home'),
	path('edit_profile/', EditProfile.as_view(), name="edit_profile"),
	path('webpush-sw.js', views.service_worker, name='service_worker'),
	path('save-subscription/', views.save_subscription, name='save_subscription'),
	path('service-worker.js', views.service_worker, name='service_worker'),
	path('about/', views.about, name='about'),
]
