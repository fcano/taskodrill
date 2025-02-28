from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import MyUser, MyUserProfile
from .forms import SignUpForm

class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

    class Meta:
        model = MyUser

class MyUserProfileDetail(LoginRequiredMixin, DetailView):
    model = MyUserProfile

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return MyUserProfile.objects.filter(user=self.request.user)
        else:
            return MyUserProfile.objects.none()

class MyUserProfileUpdate(LoginRequiredMixin,UpdateView):
	model = MyUserProfile
	fields = ['work_hours_start', 'work_hours_end', 'timezone']
