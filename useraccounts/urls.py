from django.urls import path
from .views import register_view, login_view, change_password, change_username, logout_view,  confirm_users
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('change-username/', change_username, name='change_username'),
    path('change-password/', change_password, name='change_password'),
    path('confirm-users/', confirm_users, name='confirm_users'),

]