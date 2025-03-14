from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views import View
from django.contrib import messages
from .forms import CustomUserCreationForm
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
    tasks = Task.objects.all()  # Get all tasks (no filtering for now)
    return render(request, 'task_view.html', {'tasks': tasks})
