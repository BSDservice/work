from django.urls import path, re_path, include
from naryad import views
from django.views.generic import RedirectView


urlpatterns = [
    path('data_sync/get', views.data_sync, name='data_sync'),
    path('data_sync/post', views.data_sync, name='data_sync'),
    path('', views.naryad, name='naryad'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('update_task/<int:task_id>', views.update_task, name='update_task'),
    path('list_hide_tasks', views.show_hide_tasks, name='show_hide_tasks'),
]
