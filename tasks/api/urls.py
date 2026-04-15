from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from tasks.api.views import TaskViewSet, GoalViewSet, ContextViewSet
from tasks.api.auth import ObtainTokenView, RevokeTokenView

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'goals', GoalViewSet, basename='goal')
router.register(r'contexts', ContextViewSet, basename='context')

urlpatterns = [
    path('auth/token/', ObtainTokenView.as_view(), name='api_token_obtain'),
    path('auth/token/revoke/', RevokeTokenView.as_view(), name='api_token_revoke'),
    path('schema/', SpectacularAPIView.as_view(), name='api_schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api_schema'), name='api_docs'),
    path('', include(router.urls)),
]
