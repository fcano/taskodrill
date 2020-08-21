from django.urls import path
from votes import views as votes_views

urlpatterns = [
    path('votes/', votes_views.VoteList.as_view(), name='vote_list'),
    path('votes/<int:pk>/', votes_views.VoteDetail.as_view(), name='vote_detail'),
    path('votes/add/', votes_views.VoteCreate.as_view(), name='vote_add'),
    path('votes/<int:pk>/edit/', votes_views.VoteUpdate.as_view(), name='vote_update'),
    path('votes/<int:pk>/delete/', votes_views.VoteDelete.as_view(), name='vote_delete'),
    path('ideas/', votes_views.IdeaList.as_view(), name='idea_list'),
    path('ideas/<int:pk>/', votes_views.IdeaDetail.as_view(), name='idea_detail'),
    path('ideas/add/', votes_views.IdeaCreate.as_view(), name='idea_add'),
    path('ideas/<int:pk>/edit/', votes_views.IdeaUpdate.as_view(), name='idea_update'),
    path('ideas/<int:pk>/delete/', votes_views.IdeaDelete.as_view(), name='idea_delete'),
]
