from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('search/', views.search, name='search'),
    path('industries/', views.industries, name='industries'),
    path('experts/', views.experts, name='experts'),
    path('experts/<str:expert_id>/', views.expert_detail, name='expert-detail'),
]
