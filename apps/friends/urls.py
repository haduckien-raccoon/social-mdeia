from django.urls import path
from .views import *

app_name = "friends"

urlpatterns = [
    path("", friend_list_view, name="list"),
    path("send/<int:user_id>/", send_request_view, name="send_request"),
    path("accept/<int:request_id>/", accept_request_view, name="accept_request"),
    path("reject/<int:request_id>/", reject_request_view, name="reject_request"),
    path("unfriend/<int:user_id>/", unfriend_view, name="unfriend"),
]