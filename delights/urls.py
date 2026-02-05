from django.urls import path
from . import views

# Units URLs
app_name = 'units'

urlpatterns = [
    path('', views.UnitListView.as_view(), name='list'),
    path('add/', views.UnitCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.UnitUpdateView.as_view(), name='edit'),
    path('<int:pk>/toggle-active/', views.unit_toggle_active, name='toggle_active'),
]

