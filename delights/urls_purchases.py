from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.PurchaseListView.as_view(), name='list'),
    path('add/', views.purchase_create, name='add'),
    path('confirm/', views.purchase_confirm, name='confirm'),
    path('confirm/final/', views.purchase_finalize, name='finalize'),
    path('<int:pk>/', views.PurchaseDetailView.as_view(), name='detail'),
]

