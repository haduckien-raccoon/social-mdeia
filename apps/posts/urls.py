# apps/posts/urls.py
from django.urls import path
from . import views

app_name = "posts"

urlpatterns = [
    path("", views.feed_view, name="feed"),
    path("<int:post_id>/", views.post_detail_view, name="post_detail"),
    path("<int:post_id>/delete/", views.delete_post_view, name="delete_post"),
    path("<int:post_id>/react/", views.react_post_view, name="react_post"),

    path("<int:post_id>/comment/", views.create_comment_view, name="create_comment"),
    path("comment/<int:comment_id>/delete/", views.delete_comment_view, name="delete_comment"),
    path("comment/<int:comment_id>/react/", views.react_comment_view, name="react_comment"),
]
