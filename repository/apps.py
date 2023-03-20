from django.apps import AppConfig


class RepositoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'repository'

    def ready(self):
        from jobs import updater
        updater.start()