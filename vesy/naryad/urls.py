from django.urls import path
from naryad import views

urlpatterns = [
    path('data_sync/get', views.data_sync, name='data_sync'),
    path('data_sync/post', views.data_sync, name='data_sync')
    #path('data_sync/connect', views.connect, name='connect')
]
