from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    RegisterConfirmView,
    RegisterCheckView,
    CustomTokenObtainPairView
)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('register/confirm/', RegisterConfirmView.as_view(), name='register_confirm'),
    path('register/check/', RegisterCheckView.as_view(), name='register_check'),
]
