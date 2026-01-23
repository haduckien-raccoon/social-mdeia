from django.urls import path
from . import views
from apps.posts.views import *

urlpatterns = [
    path('', feed_view, name='home'),
]
