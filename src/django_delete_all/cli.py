import os
import sys
import re
import click
import importlib.util
from pathlib import Path


@click.group()
@click.version_option()
def main():
    """Django Delete All - Bulk deletion utilities for Django projects."""
    pass


@main.command()
@click.argument('app_label')
@click.argument('model_name', required=False)
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
@click.option('--production-override', is_flag=True, help='Allow deletion in production (use with extreme caution!)')
@click.option('--settings', help='Django settings module (e.g., myproject.settings)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def delete(app_label, model_name, force, dry_run, production_override, settings, verbose):
    """Delete all objects from specified model or app.

    Examples:
        django-delete-all delete testapp TestModel
        django-delete-all delete testapp TestModel --dry-run
        django-delete-all delete testapp  # Lists available models
    """
    try:
        _setup_django(settings, verbose)
        _run_delete_command(app_label, model_name, force, dry_run, production_override)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def debug(verbose):
    """Debug Django settings detection."""
    click.echo("🔍 Django Delete All - Debug Information")
    click.echo(f"Current directory: {Path.cwd()}")
    click.echo(f"Python path: {sys.path[:3]}...")

    # Check for manage.py
    manage_py_dir = _find_manage_py_directory()
    if manage_py_dir:
        click.echo(f"✓ Found manage.py in: {manage_py_dir}")
    else:
        click.echo("✗ No manage.py found")

    # Check environment variable
    env_settings = os.environ.get('DJANGO_SETTINGS_MODULE')
    if env_settings:
        click.echo(f"✓ DJANGO_SETTINGS_MODULE: {env_settings}")
    else:
        click.echo("✗ DJANGO_SETTINGS_MODULE not set")

    # Try to detect settings
    try:
        settings_module = _detect_django_settings()
        if settings_module:
            click.echo(f"✓ Detected settings: {settings_module}")

            # Test if we can import it
            if _test_settings_module(settings_module):
                click.echo(f"✓ Settings module is importable")
            else:
                click.echo(f"✗ Settings module is NOT importable")
        else:
            click.echo("✗ Could not detect settings")
    except Exception as e:
        click.echo(f"✗ Error detecting settings: {e}")

    # List potential candidates
    click.echo("\n📋 Testing common settings patterns:")
    candidates = [
        'testsite.settings',
        'config.settings',
        'settings.settings',
        'settings',
    ]

    for candidate in candidates:
        if _test_settings_module(candidate):
            click.echo(f"  ✓ {candidate}")
        else:
            click.echo(f"  ✗ {candidate}")


@main.command()
def init():
    """Initialize django-delete-all in your Django project."""
    click.echo("Setting up django-delete-all...")

    # Check if we're in a Django project
    if not Path('manage.py').exists():
        click.echo("Error: No manage.py found. Run this command from your Django project root.", err=True)
        return

    click.echo("✓ Django project detected")

    # Try to find settings
    settings_candidates = [
        'settings.py',
        'mysite/settings.py',
        '*/settings.py'
    ]

    settings_file = None
    for candidate in settings_candidates:
        matches = list(Path('.').glob(candidate))
        if matches:
            settings_file = matches[0]
            break

    if settings_file:
        click.echo(f"✓ Settings file found: {settings_file}")

        # Read settings file
        content = settings_file.read_text()

        # Check if already installed
        if 'django_delete_all' in content:
            click.echo("✓ django-delete-all is already installed in INSTALLED_APPS")
        else:
            click.echo("Add 'django_delete_all' to your INSTALLED_APPS in settings.py")
            click.echo("\nExample:")
            click.echo("INSTALLED_APPS = [")
            click.echo("    'django.contrib.admin',")
            click.echo("    'django.contrib.auth',")
            click.echo("    # ... other apps ...")
            click.echo("    'django_delete_all',  # Add this line")
            click.echo("]")
    else:
        click.echo("⚠ Settings file not found. Make sure you're in the Django project root.")

    click.echo("\n🎉 Setup complete! You can now use:")
    click.echo("  • Django admin actions for bulk deletion")
    click.echo("  • python manage.py delete_all <app> <model>")
    click.echo("  • django-delete-all delete <app> <model>")
    click.echo("\nFor troubleshooting, run: django-delete-all debug")


def _setup_django(settings_module=None):
    """Setup Django environment."""
    import django
    from django.conf import settings

    # Try to detect Django settings
    if not settings_module:
        settings_module = _detect_django_settings()

        if not settings_module:
            raise click.ClickException(
                "Could not find Django settings. Either:\n"
                "1. Run from your Django project directory, or\n"
                "2. Use --settings option, or\n"
                "3. Set DJANGO_SETTINGS_MODULE environment variable"
            )

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

    try:
        django.setup()
    except Exception as e:
        raise click.ClickException(f"Failed to setup Django: {e}")


def _setup_django(settings_module=None, verbose=False):
    """Setup Django environment."""
    import django
    from django.conf import settings

    # Try to detect Django settings
    if not settings_module:
        if verbose:
            click.echo("Detecting Django settings...")

        settings_module = _detect_django_settings()

        if verbose and settings_module:
            click.echo(f"Found settings: {settings_module}")

        if not settings_module:
            raise click.ClickException(
                "Could not find Django settings. Either:\n"
                "1. Run from your Django project directory, or\n"
                "2. Use --settings option, or\n"
                "3. Set DJANGO_SETTINGS_MODULE environment variable\n"
                f"4. Current directory: {Path.cwd()}"
            )

    # Add current directory to Python path if it's not already there
    current_dir = str(Path.cwd())
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        if verbose:
            click.echo(f"Added to Python path: {current_dir}")

    # Also check if we need to add the directory containing manage.py
    manage_py_dir = _find_manage_py_directory()
    if manage_py_dir and str(manage_py_dir) != current_dir and str(manage_py_dir) not in sys.path:
        sys.path.insert(0, str(manage_py_dir))
        if verbose:
            click.echo(f"Added manage.py directory to Python path: {manage_py_dir}")

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

    try:
        django.setup()
        if verbose:
            click.echo("✓ Django setup successful")
    except Exception as e:
        if verbose:
            click.echo(f"Django setup failed. Python path: {sys.path[:3]}...")
        raise click.ClickException(f"Failed to setup Django: {e}")


def _find_manage_py_directory():
    """Find the directory containing manage.py."""
    current_path = Path.cwd()

    # Check current directory and up to 3 parent directories
    for i in range(4):
        manage_py = current_path / 'manage.py'
        if manage_py.exists():
            return current_path

        # Move up one directory
        parent = current_path.parent
        if parent == current_path:  # Reached filesystem root
            break
        current_path = parent

    return None


def _detect_django_settings():
    """Detect Django settings module."""
    # First, check environment variable
    env_settings = os.environ.get('DJANGO_SETTINGS_MODULE')
    if env_settings:
        return env_settings

    # Look for manage.py in current directory or parent directories
    manage_py_dir = _find_manage_py_directory()

    if manage_py_dir:
        manage_py = manage_py_dir / 'manage.py'
        try:
            content = manage_py.read_text()

            # Look for os.environ.setdefault in manage.py
            match = re.search(r'setdefault\(["\']DJANGO_SETTINGS_MODULE["\'],\s*["\']([^"\']+)["\']', content)
            if match:
                settings_module = match.group(1)
                return settings_module
        except Exception:
            pass

    # If no manage.py found, try common patterns in current directory
    current_dir = Path.cwd()
    project_name = current_dir.name

    # Common patterns for Django projects
    candidates = [
        'testsite.settings',  # For our specific test project
        f'{project_name}.settings',
        'config.settings',
        'settings.settings',
        'core.settings',
        'settings',
    ]

    # Test each candidate
    for candidate in candidates:
        if _test_settings_module(candidate):
            return candidate

    return None


def _test_settings_module(module_name):
    """Test if a settings module exists and is importable."""
    try:
        # Make sure current directory is in path
        current_dir = str(Path.cwd())
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        import importlib
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _run_delete_command(app_label, model_name, force, dry_run, production_override):
    """Run the delete command using Django's management system."""
    from django.core.management import call_command

    args = [app_label]
    if model_name:
        args.append(model_name)

    options = {
        'force': force,
        'dry_run': dry_run,
        'production_override': production_override,
    }

    call_command('delete_all', *args, **options)


if __name__ == '__main__':
    main()