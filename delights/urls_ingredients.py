from django.urls import path
from . import views

app_name = 'ingredients'

urlpatterns = [
    path('', views.IngredientListView.as_view(), name='list'),
    path('add/', views.IngredientCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.IngredientUpdateView.as_view(), name='edit'),
    path('<int:pk>/adjust/', views.inventory_adjust, name='adjust'),
]

