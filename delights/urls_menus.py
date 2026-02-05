from django.urls import path
from . import views

app_name = 'menus'

urlpatterns = [
    path('', views.MenuListView.as_view(), name='list'),
    path('add/', views.MenuCreateView.as_view(), name='add'),
    path('<int:pk>/', views.MenuDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.MenuUpdateView.as_view(), name='edit'),
    path('<int:pk>/items/', views.manage_menu_items, name='items'),
]

