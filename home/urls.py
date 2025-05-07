from django.urls import path,include
from home import views
urlpatterns = [
    path("",views.index,name='main'),
    path('send-command/', views.send_command_view, name='send-command'),
    path('visualize_data/', views.visualize_data, name='visualize_data'),
     path('manualedit/', views.manual_edit, name='manualedit'),]