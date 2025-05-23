from django.contrib import admin
from django.contrib.admin import helpers
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.template.response import TemplateResponse
from django.utils.html import format_html
from .safety import check_deletion_safety, log_deletion_attempt, log_deletion_success, SafetyError, safety


def delete_all_action(modeladmin, request, queryset):
    """
    Admin action to delete all objects of the selected model.
    """
    opts = modeladmin.model._meta

    # Check permissions
    if not modeladmin.has_delete_permission(request):
        raise PermissionDenied

    # Get all objects for this model
    all_objects = modeladmin.model.objects.all()
    object_count = all_objects.count()

    # Safety checks
    try:
        check_deletion_safety(modeladmin.model, object_count)
    except SafetyError as e:
        # Handle safety violations gracefully
        from django.contrib import messages

        messages.error(
            request,
            format_html(
                '<strong>Deletion Blocked for Safety:</strong><br/>'
                '{}<br/><br/>'
                '<strong>Current limits:</strong><br/>'
                '• Maximum objects without confirmation: {}<br/>'
                '• Objects found: {}<br/><br/>'
                'To adjust these limits, contact your administrator or '
                'modify DJANGO_DELETE_ALL settings.',
                str(e),
                safety.max_objects_without_confirmation,
                object_count
            )
        )

        # Return None to redirect back to changelist with error message
        return None
    except Exception as e:
        # Handle any other unexpected errors
        from django.contrib import messages
        messages.error(
            request,
            f"Unexpected error during safety check: {e}"
        )
        return None

    # Log the attempt
    log_deletion_attempt(modeladmin.model, object_count, request.user)

    # Check if this is the confirmation POST request
    if request.POST.get('post') == 'yes':
        # Perform the deletion
        if object_count > 0:
            try:
                with transaction.atomic():
                    deleted_count, deleted_details = all_objects.delete()

                # Log successful deletion
                log_deletion_success(modeladmin.model, deleted_count, request.user)

                # Send success message
                modeladmin.message_user(
                    request,
                    format_html(
                        "Successfully deleted <strong>{}</strong> {}.",
                        deleted_count,
                        opts.verbose_name_plural if deleted_count != 1 else opts.verbose_name
                    )
                )
            except Exception as e:
                modeladmin.message_user(
                    request,
                    format_html(
                        "Error during deletion: <strong>{}</strong>",
                        str(e)
                    ),
                    level='ERROR'
                )
                return None
        else:
            modeladmin.message_user(
                request,
                "No %s to delete." % opts.verbose_name_plural
            )

        # Return None to redirect back to changelist
        return None

    # Show confirmation page
    context = {
        'title': 'Delete all %s' % opts.verbose_name_plural,
        'object_name': opts.verbose_name,
        'object_count': object_count,
        'queryset': all_objects,
        'opts': opts,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'media': modeladmin.media,
        'is_large_deletion': object_count > 100,  # Show extra warning for large deletions
        'safety_info': {
            'max_without_confirmation': safety.max_objects_without_confirmation,
            'requires_confirmation': safety.requires_confirmation(object_count),
        }
    }

    return TemplateResponse(
        request,
        'admin/delete_all_confirmation.html',
        context
    )


delete_all_action.short_description = "Delete ALL objects (use with caution!)"


def delete_selected_batch(modeladmin, request, queryset):
    """
    Enhanced version of Django's delete_selected that shows more info.
    """
    return admin.actions.delete_selected(modeladmin, request, queryset)


delete_selected_batch.short_description = "Delete selected objects"


# Auto-register the actions with all ModelAdmin classes
def register_delete_actions():
    """
    Register our delete actions with Django admin.
    """
    # Add to default actions
    admin.site.add_action(delete_all_action)
    admin.site.add_action(delete_selected_batch)


# Call the registration function
register_delete_actions()