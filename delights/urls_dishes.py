from django.urls import path
from . import views

app_name = 'dishes'

urlpatterns = [
    path('', views.DishListView.as_view(), name='list'),
    path('add/', views.DishCreateView.as_view(), name='add'),
    path('<int:pk>/', views.DishDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.DishUpdateView.as_view(), name='edit'),
    path('<int:pk>/requirements/', views.manage_recipe_requirements, name='requirements'),
]

