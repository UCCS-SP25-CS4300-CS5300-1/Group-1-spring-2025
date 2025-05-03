'''
Configure WebPush Notifications
'''

from django.conf import settings

def vapid_key(request):
    return {
        'vapid_key': settings.VAPID_PUBLIC_KEY
    }
