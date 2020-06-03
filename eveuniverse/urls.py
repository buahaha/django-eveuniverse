from django.urls import path
from . import views


app_name = 'eveuniverse'

urlpatterns = [
    path('', views.index, name='index'),
]