import os
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.db import transaction
from django.conf import settings


class Command(BaseCommand):
    help = 'Delete all objects from specified model or app'

    def add_arguments(self, parser):
        parser.add_argument(
            'app_label',
            type=str,
            help='The app label (e.g., "testapp")'
        )
        parser.add_argument(
            'model_name',
            type=str,
            nargs='?',
            help='The model name (e.g., "TestModel"). If not provided, shows available models.'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--production-override',
            action='store_true',
            help='Allow deletion in production (use with extreme caution!)'
        )

    def handle(self, *args, **options):
        app_label = options['app_label']
        model_name = options['model_name']
        force = options['force']
        dry_run = options['dry_run']
        production_override = options['production_override']

        # Safety check: prevent accidental production usage
        if not self._is_safe_environment() and not production_override:
            raise CommandError(
                "This command is disabled in production environments. "
                "Use --production-override if you really need to run this in production."
            )

        # Get the app
        try:
            app_config = apps.get_app_config(app_label)
        except LookupError:
            raise CommandError(f'App "{app_label}" not found.')

        # If no model specified, list available models
        if not model_name:
            self._list_models(app_config)
            return

        # Get the model
        try:
            model = app_config.get_model(model_name)
        except LookupError:
            raise CommandError(
                f'Model "{model_name}" not found in app "{app_label}". '
                f'Run command without model name to see available models.'
            )

        # Get objects count
        object_count = model.objects.count()

        if object_count == 0:
            self.stdout.write(
                self.style.WARNING(f'No {model._meta.verbose_name_plural} found to delete.')
            )
            return

        # Show what will be deleted
        self.stdout.write(
            self.style.WARNING(
                f'Found {object_count} {model._meta.verbose_name_plural} to delete.'
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('DRY RUN: No objects were actually deleted.')
            )
            return

        # Confirmation
        if not force:
            confirm = input(
                f'Are you sure you want to delete ALL {object_count} '
                f'{model._meta.verbose_name_plural}? This cannot be undone! (yes/no): '
            )
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS('Operation cancelled.'))
                return

        # Perform deletion
        try:
            # Final safety check
            from django_delete_all.safety import check_deletion_safety, SafetyError
            check_deletion_safety(model, object_count)

            with transaction.atomic():
                deleted_count, deleted_details = model.objects.all().delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} {model._meta.verbose_name_plural}.'
                )
            )

            # Show deletion details if verbose
            if self.verbosity > 1:
                for model_name, count in deleted_details.items():
                    if count > 0:
                        self.stdout.write(f'  - {model_name}: {count}')

        except SafetyError as e:
            raise CommandError(
                f'Deletion blocked for safety: {e}\n\n'
                'To adjust safety limits, modify DJANGO_DELETE_ALL settings in your Django configuration.'
            )
        except Exception as e:
            raise CommandError(f'Error during deletion: {e}')

    def _list_models(self, app_config):
        """List all models in the app."""
        models = app_config.get_models()
        if not models:
            self.stdout.write(f'No models found in app "{app_config.label}".')
            return

        self.stdout.write(f'Available models in "{app_config.label}":')
        for model in models:
            count = model.objects.count()
            self.stdout.write(
                f'  - {model.__name__} ({count} objects)'
            )

    def _is_safe_environment(self):
        """Check if we're in a safe environment for deletion."""
        # Check DEBUG setting
        if hasattr(settings, 'DEBUG') and not settings.DEBUG:
            return False

        # Check environment variables
        env = os.environ.get('DJANGO_ENV', '').lower()
        if env in ['production', 'prod']:
            return False

        # Check database name (common production indicators)
        db_name = settings.DATABASES.get('default', {}).get('NAME', '')
        if any(indicator in str(db_name).lower() for indicator in ['prod', 'production']):
            return False

        return True