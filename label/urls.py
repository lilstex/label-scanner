from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('register/', views.registerPage, name="register"),

    path('', views.home, name="home"),
    path('capture-label/', views.capture_label, name="captureLabel"),
    # path('label/<str:pk>/', views.label, name="label"),
    # path('info/<str:pk>/', views.label_info, name="labelInfo"),

    # path('capture-label/', views.capture_label, name="captureLabel"),
    # path('delete-label/<str:pk>/', views.delete_label, name="deleteLabel")
]
