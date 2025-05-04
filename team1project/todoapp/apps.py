'''
Configure todoapp
'''

from django.apps import AppConfig

class TodoappConfig(AppConfig):
    ''' This is just the app config class '''
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'todoapp'
