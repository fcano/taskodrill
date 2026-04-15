from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.authtoken.models import Token

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


class APITokenView(LoginRequiredMixin, View):
    template_name = 'myauth/api_token.html'

    def get(self, request):
        token = Token.objects.filter(user=request.user).first()
        return render(request, self.template_name, {'token': token})

    def post(self, request):
        action = request.POST.get('action')
        if action == 'generate':
            token, created = Token.objects.get_or_create(user=request.user)
            if created:
                messages.success(request, 'API token generated.')
            else:
                messages.info(request, 'You already have an API token.')
        elif action == 'revoke':
            deleted, _ = Token.objects.filter(user=request.user).delete()
            if deleted:
                messages.success(request, 'API token revoked.')
            else:
                messages.info(request, 'No token to revoke.')
        return redirect('api_token_manage')
