from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.views import View
from django.contrib import messages

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

class ProfileSettings(View):
	def get(self, request):
		return render(request, "profile_settings.html")


	def post(self, request):
		print("Logging out")
		if "logout" in request.POST:
				logout(request)
				messages.success(request, "You have been logged out.")
				return redirect("index")