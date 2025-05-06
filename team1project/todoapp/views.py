"""This is a module that contains web requests and returns responses"""

# disabling django specific stuff and ambiguous suggestions
# pylint: disable=W0613,R0914,R1710,R0911
import os
from datetime import datetime
import json
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache

import holidays
import requests
from openai import OpenAI

from .forms import CustomUserCreationForm, TaskForm, TaskCollabForm, FilterTasksForm
from .models import Task, TaskCollabRequest, Category, WebPushSubscription
from .utils import TaskCalendar
from .forms import CustomAuthenticationForm

User = get_user_model()
logger = logging.getLogger(__name__)
TRUSTED_ORIGINS = ['https://todolistapp.tech']

# Retrieves user data and sends to OpenAI API to facilitate task suggestions
def get_ai_task_suggestion(request):
    """ Helper view for task_view: if ?generate-task= in the URL, call GPT-4 and
    return {'name':…, 'description':…, 'categories':[…], 'due_date':…} else return None. """

    if 'generate-task' not in request.GET:
        return None

    tasks = Task.objects.filter(creator=request.user)
    if not tasks.exists():
        return None

    # build the prompt
    task_data_str = "\n".join(
        f"Task: {t.name}\n"
        f"Description: {t.description}\n"
        f"Due Date: {t.due_date.isoformat() if t.due_date else None}\n"
        f"Categories: {', '.join(c.name for c in t.categories.all())}"
        for t in tasks
    )

    prompt = f"""
    Based on the user's previous tasks and patterns, suggest a new task.
    Return **only** a JSON object with keys: name, description, due_date, categories.

    User's Tasks:
    {task_data_str}
    """

    client = OpenAI(api_key=settings.OPENAI_TASK_SUGGESTION)
    try:
        resp = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role":"system","content":"You are an intelligent task suggestion assistant."},
                {"role":"user","content":prompt}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        content = resp.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        raise e


def index(request):
    """This is a function to show tasks to an authenticated user"""
    form = CustomAuthenticationForm()
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("task_view")

    return render(request, 'index.html', {'form': form})

def register(request):
    """Function to register a user and store info in the DB"""
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
    """Class that contains the settings page and login information"""
    login_url = '/'

    def get(self, request):
        """Getter function to render a page"""
        return render(request, "profile_settings.html")


    def post(self, request):
        """Function to log out the user"""
        print("Logging out")
        if "logout" in request.POST:
            logout(request)
            messages.success(request, "You have been logged out.")
            return redirect("index")

class EditProfile(LoginRequiredMixin, View):
    """Class that contains settings to change password, email, dark/light mode"""
    login_url = '/'

    def get(self, request):
        """Getter function to render a page to edit the profile"""
        return render(request, "edit_profile.html")

    def post(self, request):
        """Function to store edits to the profile in the DB"""
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
    """Function that returns tasks that were creted by the user.

    Returns:
        tasks with the user ID, form, suggested tasks."""
    task_requests = TaskCollabRequest.objects.filter(to_user=request.user)

    has_task = Task.objects.filter(creator=request.user).exists()

    # Render the tasks based on current filters set
    form, filtered_tasks, shared_filtered_tasks, _ = get_filtered_tasks(request)

    suggestion = get_ai_task_suggestion(request)
    suggested_name        = suggestion.get('name','')        if suggestion else ''
    suggested_description = suggestion.get('description','') if suggestion else ''
    suggested_categories  = suggestion.get('categories',[])  if suggestion else []

    return render(request, 'task_view.html', {
        'my_tasks':             filtered_tasks,
        'shared_tasks':         shared_filtered_tasks,
        'task_requests':        task_requests,
        'form':                 form,
        'has_task':             has_task,
        'suggested_name':       suggested_name,
        'suggested_description':suggested_description,
        'suggested_categories': suggested_categories,
    })

def get_filtered_tasks(request):
    '''
    Return the form and filtered tasks for user

    Parameters:
    request: User request to check for a get request or None

    Returns:
    form for processing the request and filtered
    tasks that are the user's, shared, or archived in that order
    - form, my_filtered_tasks, shared_filtered_tasks, filtered_archived_tasks
    '''
    form = FilterTasksForm(request.GET or None)
    my_filtered_tasks = Task.objects.filter(
        creator=request.user,
        is_archived=False
    )
    shared_filtered_tasks = Task.objects.filter(
        assigned_users=request.user,
        is_archived=False
    )

    filtered_archived_tasks = Task.objects.filter(
        is_archived=True
    ).filter(
        Q(creator=request.user) | Q(assigned_users=request.user)
    ).distinct()

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
                filtered_archived_tasks = filtered_archived_tasks.filter(
                    Q(categories__in=user_filter) | Q(categories=None)
                ).distinct()

    return form, my_filtered_tasks, shared_filtered_tasks, filtered_archived_tasks

def show_quote():
    '''
    Return today's quote from ZenQuotes API

    Returns:
    string: Pre-formatted html quote
    '''
    # If quote is stashed, use that stashed quote
    quote = cache.get('zenquote_today')

    if quote:
        return quote

    url = 'https://zenquotes.io/api/today/'
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        quote = data[0]["h"]

        # Cache quote for ten minutes
        cache.set('zenquote_today', quote, timeout=60 * 10)
        return quote
    except requests.exceptions.RequestException as _:
        return "Could not fetch today's quote."

@login_required(login_url='/')
def add_task(request):
    """Function to add the tast for a logged in user and store it in
    the DB.

    Returns:
        task and task form."""
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.creator = request.user

            # Handle notification type manually (since we customized it in the template)
            notification_type = request.POST.get('notification_type')
            if notification_type in dict(Task.NOTIFICATION_TYPES):  # safe check
                task.notification_type = notification_type

            task.save()
            form.save_m2m()
            return redirect('task_view')
    else:
        # Pre-fill form if suggestions were passed
        name = request.GET.get('name')
        description = request.GET.get('description')
        categories = request.GET.getlist('categories')
        due_date = request.GET.get('due_date')

        initial = {}

        if name:
            initial['name'] = name
        if description:
            initial['description'] = description
        if categories:
            initial['categories'] = list(
                Category.objects.filter(name__in=categories).values_list('id', flat=True))
        if due_date:
            try:
                initial['due_date'] = datetime.strptime(due_date, "%Y-%m-%d").date()
            except ValueError:
                pass  # ignore bad format safely

        form = TaskForm(initial=initial)

    return render(request, 'add_task.html', {'form': form})


@login_required(login_url='/')
def delete_task(request, task_id):
    """Function to deleted a task from the DB for a logged in user."""
    task = get_object_or_404(Task, id=task_id)

    task.delete()

    return redirect('task_view')  # Redirect back to task list

@login_required(login_url = '/')
def edit_task(request, task_id):
    """Function to edit the task info and store updates in the DB."""
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
    """Function to share a task with other users.

    Returns:
        task url, task form"""
    task = get_object_or_404(Task, id=task_id)
    share_url = f"{request.get_host()}/shared_task/{task_id}"

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

            return HttpResponse('Request was already sent')

    else:
        task = get_object_or_404(Task, id=task_id)
        form = TaskCollabForm(user=request.user, task=task)

    return render(request, 'share_task.html', {'form': form, 'task': task, 'url': share_url, })

@login_required(login_url='/')
def accept_task(request, request_id):
    """Function to accept a shared task from a task page.

    Returns:
        task page render."""
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
        task_collab_filter = TaskCollabRequest.objects.filter(
            task_id = task_id, to_user=request.user)
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
    """Function that allows the user to accept a shred task using only a link."""
    task = get_object_or_404(Task, id=task_id)
    task_collab_filter = TaskCollabRequest.objects.filter(task_id = task_id, to_user=request.user)

	# anonymous users do not have requests,
    # but check if authenticated users have an outstanding request
    no_requests = True
    if request.user.is_authenticated:
        task_collab_filter = TaskCollabRequest.objects.filter(
            task_id = task_id, to_user=request.user)
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
    """Function t exit a task if the users doesn't want to add a shared task
        to their tasks.

    Returns:
        task view page."""
    task = get_object_or_404(Task, id=task_id)
    task.assigned_users.remove(request.user)
    return redirect('task_view')


def archive_task(request, task_id):
    """Function to archive a task."""
    task = get_object_or_404(Task, id=task_id)
    task.ignore_archive = False
    task.is_archived = True
    task.save()
    return redirect('task_view')


def restore_task(request, task_id):
    """Function to restore a page from a task archive."""
    task = get_object_or_404(Task, id=task_id)
    if task.creator == request.user or request.user in task.assigned_users.all():
        task.ignore_archive = True
        task.is_archived = False
        task.save()
    return redirect('task_archive')


def task_archive(request):
    """Function to render a task archive page."""
    form, _, _, filtered_archived_tasks = get_filtered_tasks(request)

    return render(request, 'task_archive.html', {
        'archived_tasks': filtered_archived_tasks,
        'form': form,
    })


@csrf_exempt
def save_subscription(request):
    """Securely save a push subscription for an authenticated user."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=403)

    origin = request.META.get('HTTP_ORIGIN', '')
    if origin not in TRUSTED_ORIGINS:
        return JsonResponse({'success': False, 'error': 'Invalid origin'}, status=403)

    try:
        subscription_data = json.loads(request.body.decode('utf-8'))
        save_info(request.user, subscription_data)
        return JsonResponse({'success': True})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    except ValueError as e:
        logger.error("ValueError in save_subscription: %s", e)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

    except KeyError as e:
        logger.error("KeyError in save_subscription: %s", e)
        return JsonResponse({'success': False, 'error': f"Missing field: {str(e)}"}, status=400)

    except Exception as e:
        logger.error("Unexpected error in save_subscription: %s", e)
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)



def save_info(user, subscription_data):
    """Function to save the push subscription for a user."""
    WebPushSubscription.objects.update_or_create(
        user=user,
        defaults={'subscription_info': subscription_data}
    )


@require_GET
@csrf_exempt
def service_worker(request):
    """Function to handle service worker.

    Returns:
        HttpResponse with subscription."""
    file_path = os.path.join(settings.BASE_DIR, 'todoapp', 'static', 'webpush-sw.js')

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return HttpResponse(content, content_type='application/javascript')


def about(request):
    """Function to render an about page"""
    return render(request, 'about.html')


@login_required(login_url='index')
@require_GET
def calender_view(request):
    """Function to show tasks on the calendar on the calendar page."""
    # A) Category‑filter form
    form = FilterTasksForm(request.GET or None)

    # B) Figure out year & month (GET or today)
    year  = request.GET.get('year')
    month = request.GET.get('month')
    if year and month:
        year, month = int(year), int(month)
    else:
        today = datetime.today()
        year, month = today.year, today.month

    # C) Base querysets
    monthly_tasks = Task.objects.filter(
        Q(creator=request.user) | Q(assigned_users=request.user),
        due_date__year=year,
        due_date__month=month,
    ).distinct().order_by('due_date')

    sidebar_tasks = Task.objects.filter(
        Q(creator=request.user) | Q(assigned_users=request.user),
        is_completed=False,
        is_archived=False,
    ).distinct().order_by('due_date')

    selected_day = request.GET.get('day')
    if selected_day and selected_day.isdigit():
        sidebar_tasks = sidebar_tasks.filter(due_date__day=int(selected_day))

    # D) Apply category filter if submitted
    if 'make-filter' in request.GET and form.is_valid():
        cats = form.cleaned_data['user_category_filter']
        if cats:
            monthly_tasks = monthly_tasks.filter(
                Q(categories__in=cats) | Q(categories=None)
            ).distinct()
            sidebar_tasks = sidebar_tasks.filter(
                Q(categories__in=cats) | Q(categories=None)
            ).distinct()

    # E) Prev/next pointers
    prev_month = 12 if month == 1 else month - 1
    prev_year  = year - 1 if month == 1 else year
    next_month = 1  if month == 12 else month + 1
    next_year  = year + 1 if month == 12 else year

    # F) Holiday dict
    us_hols = holidays.CountryHoliday('US', years=[year])
    holiday_dict = {
        dt.day: name
        for dt, name in us_hols.items()
        if dt.month == month
    }

    # G) Build calendar HTML
    cal = TaskCalendar(
        monthly_tasks,
        year=year,
        month=month,
        holidays=holiday_dict,
        user=request.user
    )
    html_calendar = cal.formatmonth(year, month)

    today_quote = show_quote()
    # H) Render once with all context
    return render(request, 'home.html', {
        'calendar':     html_calendar,
        'year':         year,
        'month':        month,
        'prev_year':    prev_year,
        'prev_month':   prev_month,
        'next_year':    next_year,
        'next_month':   next_month,
        'form':         form,           # your FilterTasksForm
        'all_tasks':    sidebar_tasks,  # template loops over all_tasks
        'holiday_dict': holiday_dict,
        'today_quote': today_quote
    })
