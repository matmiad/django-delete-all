from django.apps import AppConfig


class DjangoDeleteAllConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_delete_all'
    verbose_name = 'Django Delete All'

    def ready(self):
        # Import admin to register our custom actions
        from . import admin  # noqa
