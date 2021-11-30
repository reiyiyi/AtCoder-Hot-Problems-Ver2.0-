from django.urls import path
from . import views

app_name = 'ranking'

urlpatterns = [
    path('', views.RankingList.as_view(), name='ranking_list'),
]