from django.urls import path
from . import views

urlpatterns = [
    path('', views.home.as_view(), name='home'),
    path('posts/', views.posts.as_view(), name='posts'),
    path('posts/<slug:slug>/', views.post_detail.as_view(), name='post_detail'),
    path('saved-posts', views.Saved.as_view(), name='saved-posts'),
]
