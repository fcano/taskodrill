from django.urls import path
from . import views

urlpatterns = [
    #path('accounts/signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/<int:pk>/', views.MyUserProfileDetail.as_view(), name='myuserprofile_detail'),
    path('profile/<int:pk>/edit/', views.MyUserProfileUpdate.as_view(), name='myuserprofile_update'),
]
