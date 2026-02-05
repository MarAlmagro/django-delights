from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.UserListView.as_view(), name='list'),
    path('add/', views.UserCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.UserUpdateView.as_view(), name='edit'),
    path('<int:pk>/toggle-active/', views.user_toggle_active, name='toggle_active'),
    path('<int:pk>/reset-password/', views.user_reset_password, name='reset_password'),
]

