from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .forms import CustomUserCreationForm, TaskForm, TaskCollabForm, FilterTasksForm
from .models import Task, TaskCollabRequest
from .utils import TaskCalendar
from datetime import datetime
import openai
import json

# Create your views here.

# Retrieves user data and sends to OpenAI API to faciliate task suggestions
import openai
from django.conf import settings

# Retrieves user data and sends to OpenAI API to facilitate task suggestions
def get_ai_task_suggestion(user):
    tasks = Task.objects.filter(creator=user)

    task_data = []
    for task in tasks:
        task_data.append({
            'name': task.name,
            'description': task.description,
            'due_date': task.due_date,
            'categories': [category.name for category in task.categories.all()]
        })

    task_data_str = "\n".join([
        f"Task: {task['name']}\nDescription: {task['description']}\nCategories: {', '.join(task['categories'])}"
        for task in task_data
    ])

    prompt = f"""
    Based on the user's previous tasks and patterns, suggest a new task for the user. Return the response in JSON format with the following keys: name, description, due date, and categories.

    User's Tasks:
    {task_data_str}

    Respond only with the JSON object.
    """

    client = openai.OpenAI(api_key=settings.OPENAI_TASK_SUGGESTION)

    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=100,
        temperature=0.7,
    )

    try:
        return json.loads(response.choices[0].text.strip())
    except json.JSONDecodeError:
        return None

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
class ProfileSettings(LoginRequiredMixin, View):
	login_url = '/'

	def get(self, request):
		return render(request, "profile_settings.html")


	def post(self, request):
		print("Logging out")
		if "logout" in request.POST:
				logout(request)
				messages.success(request, "You have been logged out.")
				return redirect("index")

class EditProfile(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):
        return render(request, "edit_profile.html")

    def post(self, request):
        # get data from POST request
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # update appropriate fields for the currently logged in user
        user = request.user
        if username and username != user.username:
            user.username = username
        if email and email != user.email:
            user.email = email
        if password and password != "************":
            user.set_password(password) # ensure to hash
            update_session_auth_hash(request, user) # keeps user logged in after changing password

        user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("profile_settings")

@login_required(login_url='/')
def task_view(request):
    tasks = Task.objects.filter(
        Q(creator=request.user) | Q(assigned_users=request.user),
        Q(is_completed=False) | Q(is_completed=True, due_date__gte=timezone.now())
    ).distinct()

    task_requests = TaskCollabRequest.objects.filter(to_user=request.user)
    shared_tasks = Task.objects.filter(assigned_users=request.user) 
    archived_tasks = Task.objects.filter(
        is_completed=True,
        due_date__lt=timezone.now()
    ).filter(
        Q(creator=request.user) | Q(assigned_users=request.user)
    ).distinct().order_by('-due_date')[:10]

    form, filtered_tasks, shared_filtered_tasks = get_filtered_tasks(request)

    task_suggestion = get_ai_task_suggestion(request.user)
    suggested_name = task_suggestion.get('name', '') if task_suggestion else ''
    suggested_description = task_suggestion.get('description', '') if task_suggestion else ''
    suggested_categories = task_suggestion.get('categories', []) if task_suggestion else []

    return render(request, 'task_view.html', {
        'my_tasks': filtered_tasks, 
        'task_requests': task_requests, 
        'shared_tasks': shared_filtered_tasks, 
        'vapid_key': settings.VAPID_PUBLIC_KEY,
        'archived_tasks': archived_tasks,
		'form': form,
        'suggested_name': suggested_name,
        'suggested_description': suggested_description,
        'suggested_categories': suggested_categories,
    })

def get_filtered_tasks(request):
    form = FilterTasksForm(request.GET or None)
    my_filtered_tasks = Task.objects.filter(creator=request.user)
    shared_filtered_tasks = Task.objects.filter(assigned_users=request.user)

    if 'make-filter' in request.GET:
        if form.is_valid():
            user_filter = form.cleaned_data['user_category_filter']
            if user_filter:
                my_filtered_tasks = my_filtered_tasks.filter(
                    Q(categories__in=user_filter) | Q(categories=None)
                ).distinct()
                shared_filtered_tasks = shared_filtered_tasks.filter(
                    Q(categories__in=user_filter) | Q(categories=None)
                ).distinct()
            
    return form, my_filtered_tasks, shared_filtered_tasks

@login_required(login_url='/')
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

        suggested_task = request.GET.get('suggested_task')
        if suggested_task:
            form.initial = {'name': suggested_task}

    return render(request, 'add_task.html', {'form': form})

@login_required(login_url='/')
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    task.delete()

    return redirect('task_view')  # Redirect back to task list

@login_required(login_url = '/')
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

@login_required(login_url='/')
def share_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    share_url = f"{request.get_host()}/shared task/{task_id}"

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

    return render(request, 'share_task.html', {'form': form, 'task': task, 'url': share_url, })

@login_required(login_url='/')
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

def shared_task_view(request, task_id):
	'''
	This function allows users to view shared task and accept it without creating a request object

	Args: 
		request: Detect type of request.
		task_id: Pass the shared task id with other users
	
	Returns: 
		If successful, redirects user back to task view page
	'''
	task = get_object_or_404(Task, id=task_id)
	no_requests = True
	if request.user.is_authenticated:
		task_collab_filter = TaskCollabRequest.objects.filter(task_id = task_id, to_user=request.user)
		if task_collab_filter.exists():
			no_requests = False

	can_accept = (
		request.user.is_authenticated and 
		request.user.username != task.creator.username and 
		request.user not in task.assigned_users.all() 
		and no_requests
		)
	context = {
		"task": task,
		"show_button": can_accept
	}

	return render(request, 'shared_task_view.html', context)

@login_required(login_url='/')
def accept_task_link(request, task_id):
	task = get_object_or_404(Task, id=task_id)
	task_collab_filter = TaskCollabRequest.objects.filter(task_id = task_id, to_user=request.user)
	
	# anonymous users do not have requests, but check if authenticated users have an outstanding request
	no_requests = True
	if request.user.is_authenticated:
		task_collab_filter = TaskCollabRequest.objects.filter(task_id = task_id, to_user=request.user)
		if task_collab_filter.exists():
			no_requests = False

	can_accept = (
		request.user.is_authenticated and 
		request.user.username != task.creator.username and 
		request.user not in task.assigned_users.all() 
		and no_requests
		)
	
	# Check if user is valid for accepting the task
	if request.method =='POST' and 'accept_task_link' in request.POST:
		if can_accept:	
			task.assigned_users.add(request.user)
			return redirect('task_view')
	return redirect('shared_task_view', task_id=task.id)

@login_required(login_url='/')
def exit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.assigned_users.remove(request.user)
    return redirect('task_view')

def archive_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.is_completed = True
    task.save()
    return redirect('task_view')  

def task_archive(request):
    archived_tasks = Task.objects.filter(is_completed=True, due_date__lt=timezone.now()).filter(
        Q(creator=request.user) | Q(assigned_users=request.user)
    ).distinct()

    return render(request, 'task_archive.html', {
        'archived_tasks': archived_tasks
    })

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


@login_required(login_url='/')
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
