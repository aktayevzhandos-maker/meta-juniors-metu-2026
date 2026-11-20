from django.urls import path
from . import views
from .analytics import analytics
from .csv_views import csv_import, template
from .comparison import compare

urlpatterns = [
    path('analytics/', analytics, name='analytics'),
    path('import/template/', template, name='csv-template'),
    path('import/', csv_import, name='csv-import'),
    path('compare/', compare, name='compare'),
    path('health/', views.health, name='health'),
    path('search/', views.search, name='search'),
    path('cities/', views.cities, name='cities'),
    path('industries/', views.industries, name='industries'),
    path('experts/', views.experts, name='experts'),
    path('experts/<str:expert_id>/', views.expert_detail, name='expert-detail'),
]
