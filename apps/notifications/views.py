from django.shortcuts import render

# Create your views here.
import json
import time
from django.http import StreamingHttpResponse
from apps.notifications.models import Notification

def sse_notifications(request):
    def event_stream():
        last_id = 0
        while True:
            notifications = Notification.objects.filter(
                user=request.user,
                id__gt=last_id
            ).order_by("id")

            for n in notifications:
                last_id = n.id
                data = {
                    "id": n.id,
                    "verb": n.verb_code,
                    "actor": n.actor.username,
                    "target": n.target_repr,
                }
                yield f"data: {json.dumps(data)}\n\n"

            time.sleep(2)

    return StreamingHttpResponse(
        (b"data" + line.encode() for line in event_stream()),
        content_type="text/event-stream"
    )