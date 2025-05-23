# Django Delete All

A powerful Django package for bulk deletion operations with built-in safety features, admin integration, and CLI support.

## Features

- 🔥 **Admin Integration**: Bulk delete actions automatically available in Django admin
- 🛡️ **Safety First**: Built-in protections against accidental production deletions
- 💻 **CLI Support**: Both Django management commands and standalone CLI
- 📊 **Smart Confirmations**: Enhanced warnings for large deletions
- 📝 **Audit Logging**: Track all deletion operations
- ⚙️ **Configurable**: Flexible settings for different environments

## Installation

```bash
pip install django-delete-all
```

## Quick Setup

1. **Install the package**:
   ```bash
   pip install django-delete-all
   ```

2. **Add to Django settings**:
   ```python
   INSTALLED_APPS = [
       # ... your other apps
       'django_delete_all',
   ]
   ```

3. **Optional: Configure safety settings**:
   ```python
   DJANGO_DELETE_ALL = {
       'ENABLED': True,
       'PRODUCTION_ENABLED': False,  # Disable in production by default
       'EXCLUDED_APPS': ['auth', 'admin', 'contenttypes'],
       'MAX_OBJECTS_WITHOUT_CONFIRMATION': 100,
       'AUDIT_DELETIONS': True,
   }
   ```

## Usage

### Django Admin

Once installed, you'll see new bulk actions in your Django admin:

- **"Delete ALL objects (use with caution!)"** - Deletes all objects of a model
- **"Delete selected objects"** - Enhanced version of Django's default delete action

The admin integration includes:
- Custom confirmation pages with object counts
- Safety warnings for large deletions
- Protection against accidental clicks

### Management Commands

```bash
# List all models in an app
python manage.py delete_all myapp

# Delete all objects from a specific model
python manage.py delete_all myapp MyModel

# Dry run (see what would be deleted)
python manage.py delete_all myapp MyModel --dry-run

# Force deletion without confirmation
python manage.py delete_all myapp MyModel --force

# Override production safety
python manage.py delete_all myapp MyModel --production-override
```

### Standalone CLI

```bash
# Initialize in your Django project
django-delete-all init

# Delete objects using standalone CLI
django-delete-all delete myapp MyModel

# With custom settings
django-delete-all delete myapp MyModel --settings=myproject.settings
```

## Safety Features

### Environment Protection

By default, django-delete-all is **disabled in production environments**. It detects production by:

- `DEBUG = False` in settings
- `DJANGO_ENV=production` environment variable
- Database names containing "prod" or "production"

### Configurable Exclusions

```python
DJANGO_DELETE_ALL = {
    # Exclude sensitive apps
    'EXCLUDED_APPS': ['auth', 'admin', 'contenttypes', 'sessions'],
    
    # Exclude specific models
    'EXCLUDED_MODELS': ['myapp.ImportantModel'],
    
    # Require confirmation for deletions above this count
    'REQUIRE_CONFIRMATION_ABOVE': 10,
    
    # Maximum objects allowed in single operation
    'MAX_OBJECTS_WITHOUT_CONFIRMATION': 100,
}
```

### Audit Logging

All deletion operations are logged when `AUDIT_DELETIONS` is enabled:

```python
LOGGING = {
    'loggers': {
        'django_delete_all.safety': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

## Configuration Reference

### Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `ENABLED` | `True` | Enable/disable the package globally |
| `PRODUCTION_ENABLED` | `False` | Allow usage in production environments |
| `EXCLUDED_APPS` | `['auth', 'admin', ...]` | Apps to exclude from deletion |
| `EXCLUDED_MODELS` | `[]` | Specific models to exclude |
| `MAX_OBJECTS_WITHOUT_CONFIRMATION` | `100` | Max objects for bulk operations |
| `REQUIRE_CONFIRMATION_ABOVE` | `10` | Object count requiring confirmation |
| `AUDIT_DELETIONS` | `True` | Enable deletion logging |

### Environment Variables

- `DJANGO_DELETE_ALL_DISABLED=true` - Disable the package entirely
- `DJANGO_ENV=production` - Indicates production environment

## Examples

### Basic Admin Usage

1. Go to Django admin
2. Select any model's change list
3. Choose objects (or none for "delete all")
4. Select "Delete ALL objects" from actions dropdown
5. Confirm on the warning page

### Programmatic Usage

```python
from django_delete_all.safety import check_deletion_safety, SafetyError
from myapp.models import MyModel

try:
    # Check if deletion is safe
    check_deletion_safety(MyModel, MyModel.objects.count())
    
    # Perform deletion
    deleted_count, _ = MyModel.objects.all().delete()
    print(f"Deleted {deleted_count} objects")
    
except SafetyError as e:
    print(f"Deletion blocked: {e}")
```

## Development

### Setup

```bash
git clone https://github.com/matmiad/django-delete-all.git
cd django-delete-all
pip install -e .
```

### Testing

```bash
cd tests
python manage.py test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- 📚 [Documentation](https://github.com/matmiad/django-delete-all)
- 🐛 [Bug Reports](https://github.com/matmiad/django-delete-all/issues)
- 💬 [Discussions](https://github.com/matmiad/django-delete-all/discussions)

## Changelog

### 0.1.0
- Initial release
- Admin integration
- CLI support
- Safety features
- Audit logging