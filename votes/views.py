from django.views.generic import ListView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import Idea, Vote

class IdeaCreate(LoginRequiredMixin, CreateView):
    model = Idea
    fields = ['title', 'description']

    success_url = reverse_lazy('idea_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class IdeaDetail(LoginRequiredMixin, DetailView):
    model = Idea

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Idea.objects.filter(user=self.request.user)
        else:
            return Idea.objects.none()

class IdeaList(LoginRequiredMixin, ListView):
    model = Idea

class IdeaUpdate(LoginRequiredMixin, UpdateView):
    model = Idea
    fields = ['title', 'description']

class IdeaDelete(LoginRequiredMixin, DeleteView):
    model = Idea
    success_url = reverse_lazy('idea_list')


class VoteCreate(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            if self.request.user.available_votes() > 0:
                idea = Idea.objects.get(id=self.request.POST['id'])
                if idea is not None:
                    Vote.objects.create(
                        idea=idea,
                        user=self.request.user,
                    )
                    user_available_votes = self.request.user.available_votes()
                    idea_total_votes = idea.votes.count()

                    return JsonResponse({
                        'success': True,
                        'user_available_votes': user_available_votes, 
                        'idea_total_votes': idea_total_votes,
                        })
        
        # Arrives here if anything above goes wrong
        return JsonResponse({'error': 'Error'})

class VoteDetail(LoginRequiredMixin, DetailView):
    model = Vote

class VoteList(LoginRequiredMixin, ListView):
    model = Vote

class VoteUpdate(LoginRequiredMixin, UpdateView):
    model = Vote
    fields = ['idea']

class VoteDelete(LoginRequiredMixin, DeleteView):
    model = Vote
    success_url = reverse_lazy('idea_list')
