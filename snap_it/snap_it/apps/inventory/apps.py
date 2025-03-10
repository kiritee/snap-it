from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'snap_it.apps.inventory'

    def ready(self):
        """Import and connect signals when the app is ready."""
        import snap_it.apps.inventory.signals  # Import the signals module