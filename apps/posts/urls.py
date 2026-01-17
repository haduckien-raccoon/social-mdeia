from django.urls import path
from apps.posts.views import *

app_name = "posts"

urlpatterns = [
    path("", feed_view, name="feed"),
    path("public/", public_feed_view, name="public_feed"),

    path("create/", create_post_view, name="create"),
    path("<int:post_id>/", post_detail_view, name="post_detail"),
    path("<int:post_id>/edit/", edit_post_view),
    path("<int:post_id>/delete/", delete_post_view),

    path("<int:post_id>/comment/", create_comment_view),
    path("comment/<int:comment_id>/edit/", edit_comment_view),
    path("comment/<int:comment_id>/delete/", delete_comment_view),

    path("<int:post_id>/reaction/", toggle_post_reaction_view),
    path("comment/<int:comment_id>/reaction/", toggle_comment_reaction_view),

    path("<int:post_id>/share/", share_post_view),

    path("report/", report_view),
]
