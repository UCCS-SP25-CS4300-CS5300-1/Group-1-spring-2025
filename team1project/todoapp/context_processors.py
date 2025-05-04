"""Configure WebPush Notifications"""
from django.conf import settings

def vapid_key(request):
    """Function to get the vapid key and pass it"""
    return {
        'vapid_key': settings.VAPID_PUBLIC_KEY
    }
