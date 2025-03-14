from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views import View
from django.contrib import messages
from .forms import CustomUserCreationForm, TaskForm
from .models import Task


# Create your views here.
def index(request):
	form = AuthenticationForm()
	if request.method == 'POST':
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			return redirect("index")

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
    return render(request, 'task_view.html', {'tasks': tasks})

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
