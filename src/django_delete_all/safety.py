import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class SafetyConfig:
    """Configuration for django-delete-all safety features."""

    def __init__(self):
        self.load_settings()

    def load_settings(self):
        """Load safety settings from Django settings."""
        django_delete_all_settings = getattr(settings, 'DJANGO_DELETE_ALL', {})

        # Default safety settings
        self.enabled = django_delete_all_settings.get('ENABLED', True)
        self.production_enabled = django_delete_all_settings.get('PRODUCTION_ENABLED', False)
        self.excluded_apps = set(django_delete_all_settings.get('EXCLUDED_APPS', [
            'auth',
            'admin',
            'contenttypes',
            'sessions',
            'messages',
            'staticfiles',
        ]))
        self.excluded_models = set(django_delete_all_settings.get('EXCLUDED_MODELS', []))
        self.max_objects_without_confirmation = django_delete_all_settings.get('MAX_OBJECTS_WITHOUT_CONFIRMATION', 100)
        self.require_confirmation_above = django_delete_all_settings.get('REQUIRE_CONFIRMATION_ABOVE', 10)
        self.audit_deletions = django_delete_all_settings.get('AUDIT_DELETIONS', True)
        self.backup_before_delete = django_delete_all_settings.get('BACKUP_BEFORE_DELETE', False)

        # Environment-based overrides
        self._apply_environment_overrides()

    def _apply_environment_overrides(self):
        """Apply environment-based safety overrides."""
        env = os.environ.get('DJANGO_ENV', '').lower()

        if env in ['production', 'prod']:
            if not self.production_enabled:
                self.enabled = False
                logger.warning("django-delete-all disabled in production environment")

        # Check for explicit disable
        if os.environ.get('DJANGO_DELETE_ALL_DISABLED', '').lower() in ['true', '1']:
            self.enabled = False

    def is_enabled(self):
        """Check if django-delete-all is enabled."""
        return self.enabled

    def can_delete_model(self, model):
        """Check if a model can be deleted."""
        if not self.is_enabled():
            return False, "django-delete-all is disabled"

        app_label = model._meta.app_label
        model_name = f"{app_label}.{model.__name__}"

        if app_label in self.excluded_apps:
            return False, f"App '{app_label}' is in excluded apps list"

        if model_name in self.excluded_models:
            return False, f"Model '{model_name}' is in excluded models list"

        return True, "OK"

    def requires_confirmation(self, object_count):
        """Check if deletion requires explicit confirmation."""
        return object_count > self.require_confirmation_above

    def allows_bulk_delete(self, object_count):
        """Check if bulk deletion is allowed for this count."""
        if object_count > self.max_objects_without_confirmation:
            return False, f"Too many objects ({object_count}). Maximum allowed: {self.max_objects_without_confirmation}"

        return True, "OK"


# Global instance
safety = SafetyConfig()


def check_deletion_safety(model, object_count):
    """Comprehensive safety check for deletion operations."""
    # Check if model can be deleted
    can_delete, reason = safety.can_delete_model(model)
    if not can_delete:
        raise SafetyError(f"Deletion not allowed: {reason}")

    # Check bulk deletion limits
    can_bulk_delete, reason = safety.allows_bulk_delete(object_count)
    if not can_bulk_delete:
        raise SafetyError(f"Bulk deletion not allowed: {reason}")

    return True


def log_deletion_attempt(model, object_count, user=None):
    """Log deletion attempts for audit purposes."""
    if not safety.audit_deletions:
        return

    logger.info(
        f"Deletion attempt: {model._meta.label} "
        f"({object_count} objects) by {user or 'CLI'}"
    )


def log_deletion_success(model, deleted_count, user=None):
    """Log successful deletions for audit purposes."""
    if not safety.audit_deletions:
        return

    logger.info(
        f"Deletion completed: {model._meta.label} "
        f"({deleted_count} objects deleted) by {user or 'CLI'}"
    )


class SafetyError(Exception):
    """Exception raised when safety checks fail."""
    pass