from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views import View
from django.contrib import messages
from django.http import HttpResponse
from .forms import CustomUserCreationForm, TaskForm, TaskCollabForm
from .models import Task, TaskCollabRequest
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from datetime import datetime
from .utils import TaskCalendar

# Create your views here.
def index(request):
	form = AuthenticationForm()
	if request.method == 'POST':
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			return redirect("task_view")

	return render(request, 'index.html', {'form': form})

def register(request):
	form = CustomUserCreationForm()
	
	if request.method == "POST":
		form = CustomUserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('index')
	
	return render(request, "register.html", {"form": form} )

# Index class for handling the forms on profile settings
class ProfileSettings(View):
	def get(self, request):
		return render(request, "profile_settings.html")

	def post(self, request):
		print("Logging out")
		if "logout" in request.POST:
				logout(request)
				messages.success(request, "You have been logged out.")
				return redirect("index")

def task_view(request):
    tasks = Task.objects.filter(creator=request.user)
    task_requests = TaskCollabRequest.objects.filter(to_user=request.user)
    shared_tasks = Task.objects.filter(assigned_users=request.user) 
    return render(request, 'task_view.html', {
	    'tasks': tasks, 
	    'task_requests': task_requests, 
	    'shared_tasks': shared_tasks, 
	    'vapid_key': settings.VAPID_PUBLIC_KEY})

def add_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.creator = request.user
            task.save()
            form.save_m2m()
            return redirect('task_view')
    else:
        form = TaskForm()

    return render(request, 'add_task.html', {'form': form})


def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    task.delete()

    return redirect('task_view')  # Redirect back to task list

def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)


    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save(commit=False)
            updated_task.creator = request.user
            updated_task.save()
            form.save_m2m()  # for ManyToMany like categories
            return redirect('task_view')
    else:
        form = TaskForm(instance=task)

    return render(request, 'add_task.html', {'form': form, 'edit_mode': True})


def share_task(request, task_id):
	task = get_object_or_404(Task, id=task_id)
	if request.method == 'POST':
		form = TaskCollabForm(request.POST, user=request.user, task=task)

		if form.is_valid():
			from_user = request.user
			task_collab_obj = form.save(commit=False)
			
			# Filter requests for user, prevent another request from being made
			# if a request was already made
			request_filter = TaskCollabRequest.objects.filter(task_id=task.id, to_user=request.user)

			# Add the from user and task to the request object
			if not request_filter.exists():
				task_collab_obj.from_user = from_user
				task_collab_obj.task = task
				task_collab_obj.save()
				messages.success(request, 'Task collaboration request sent')
				return redirect('task_view')
			else:
				return HttpResponse('Request was already sent')
	
	else:
		task = get_object_or_404(Task, id=task_id)
		form = TaskCollabForm(user=request.user, task=task)

	return render(request, 'share_task.html', {'form': form, 'task': task})


def accept_task(request, request_id):
	if request.method == 'POST':
		collab_request = get_object_or_404(TaskCollabRequest, id=request_id)
		if 'accept_request' in request.POST:
			collab_request.task.assigned_users.add(collab_request.to_user)
			collab_request.delete()
			messages.success(request, 'Task collaboration requeset was accepted')

		elif 'decline_request' in request.POST:
			collab_request.delete()
			messages.success(request, 'Task collaboration request not accepted')
		
		return redirect('task_view')


def exit_task(request, task_id):
	task = get_object_or_404(Task, id=task_id)
	task.assigned_users.remove(request.user)
	return redirect('task_view')


@csrf_exempt
def save_subscription(request):
    if request.method == 'POST':
        subscription_data = json.loads(request.body.decode('utf-8'))

        from webpush.models import PushInformation
        from webpush import save_info

        save_info(
            request.user,
            subscription_data
        )

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def calender_view(request, year=None, month=None):
    if year is None or month is None:
        today = datetime.today()
        year = today.year
        month = today.month
    else:
        year, month = int(year), int(month)
    
    # Fetch tasks for the month (using your due_date field)
    tasks = Task.objects.filter(
    creator=request.user,
    due_date__year=year,
    due_date__month=month
    ).order_by('due_date')

    
    # Create a TaskCalendar instance and generate the HTML
    cal = TaskCalendar(tasks, year, month)
    html_calendar = cal.formatmonth(year, month)
    
    context = {
        'calendar': html_calendar,
        'tasks': tasks,
        'year': year,
        'month': month,
    }
    return render(request, 'home.html', context)

