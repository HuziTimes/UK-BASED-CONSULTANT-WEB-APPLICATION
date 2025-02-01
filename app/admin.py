from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import Person, User, Question, ConsultationRequest, Transaction, Contact
from .utils import send_question_answered_email


class UserAdmin(DefaultUserAdmin):
    # Add the fields you want to display in the list view
    list_display = (
        'email', 'first_name', 'last_name', 'verification_status', 'age', 'phone_number', 'country_of_origin', 'university',
        'course', 'is_staff'
    )

    # Enable filtering options
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'country_of_origin')

    # Enable search functionality
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')

    # Set the ordering to use the email field instead of username
    ordering = ('email',)  # Order by email field

    # Add fields for editing in the detail view
    fieldsets = (
        (None, {'fields': ('password',)}),
        ('Personal Info', {'fields': (
            'first_name', 'last_name', 'email', 'age', 'phone_number', 'country_of_origin', 'university', 'course',
            'government_id', 'profile_image','verification_status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields for creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'first_name', 'last_name', 'email', 'age', 'phone_number', 'country_of_origin',
                'university', 'course', 'government_id', 'password1', 'password2', 'is_staff', 'is_active'
            )}
         ),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly for staff users except verification_status"""
        if request.user.is_staff and not request.user.is_superuser:
            # If user is staff but not superuser, make all fields readonly except verification_status
            readonly_fields = [
                'first_name', 'last_name', 'email', 'age', 'phone_number',
                'country_of_origin', 'university', 'course', 'government_id', 'profile_image','is_active', 'is_staff',
                'is_superuser', 'last_login', 'date_joined', 'groups', 'user_permissions'
            ]
            return readonly_fields
        return super().get_readonly_fields(request, obj)

    def get_fieldsets(self, request, obj=None):
        """Limit the fields shown in the detail view for staff users"""
        if request.user.is_staff and not request.user.is_superuser:
            # If staff, show only the verification_status field in the form
            return (
                (None, {'fields': ('email','first_name', 'last_name','verification_status',)}),
            )
        return super().get_fieldsets(request, obj)

    def has_change_permission(self, request, obj=None):
        """Allow staff users to change users but restrict fields except for verification_status"""
        if request.user.is_staff and not request.user.is_superuser:
            # Allow change permission, but limit what they can actually edit (handled in get_fieldsets and get_readonly_fields)
            return True
        return super().has_change_permission(request, obj)

    def has_add_permission(self, request):
        """Prevent staff users from adding new users"""
        if request.user.is_staff and not request.user.is_superuser:
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        """Prevent staff users from deleting users"""
        if request.user.is_staff and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)



class AnsweredFilter(admin.SimpleListFilter):
    title = 'Answered Status'  # Filter title
    parameter_name = 'answered'  # URL parameter name for the filter

    def lookups(self, request, model_admin):
        """
        Return the options that should be available in the filter dropdown.
        """
        return (
            ('answered', 'Answered'),
            ('unanswered', 'Unanswered'),
        )

    def queryset(self, request, queryset):
        """
        Filter the queryset based on the selected filter value.
        """
        if self.value() == 'answered':
            return queryset.exclude(answer__exact='')  # Return questions that have a non-empty answer
        if self.value() == 'unanswered':
            return queryset.filter(answer__exact='')  # Return questions that have an empty answer
        return queryset


class QuestionAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = ('title', 'user', 'moderator', 'view_count', 'created_at', 'updated_at')

    # Enable search functionality
    search_fields = ('title', 'user__email', 'email')

    # Enable filtering by these fields
    list_filter = ('moderator', 'created_at', 'updated_at', AnsweredFilter)

    # Enable date hierarchy for better navigation
    date_hierarchy = 'created_at'

    # Allow ordering by certain fields
    ordering = ('-created_at',)

    # Add fields to be displayed when editing a question
    fields = ('title', 'message', 'user', 'moderator', 'answer', 'view_count')

    # Read-only fields (e.g., view_count should be automatically updated)
    readonly_fields = ('view_count', 'created_at', 'updated_at')

    # Set how many items to display per page
    list_per_page = 20

    def get_readonly_fields(self, request, obj=None):
        """
        Make all fields except 'answer' read-only for staff users.
        Once the question has been answered, 'answer' also becomes read-only.
        Superusers can edit all fields.
        """
        if request.user.is_staff and not request.user.is_superuser:
            if obj and obj.answer:  # If the question has already been answered, make 'answer' read-only
                return ['title', 'message', 'user', 'moderator', 'answer', 'view_count', 'created_at', 'updated_at']
            return ['title', 'message', 'user', 'moderator', 'view_count', 'created_at', 'updated_at']
        return super().get_readonly_fields(request, obj)

    def save_model(self, request, obj, form, change):
        """
        Override the save_model method to automatically assign the current user as the moderator
        if they provide an answer and the moderator is not already set.
        """
        is_answered = obj.answer and not obj.moderator
        if is_answered:  # If no moderator is set and there is an answer
            obj.moderator = request.user  # Set the current user as the moderator

        super().save_model(request, obj, form, change)

        if is_answered:
            send_question_answered_email(obj, request)

    def has_change_permission(self, request, obj=None):
        """
        Allow staff users to edit only if there is an existing question (obj is not None).
        """
        if request.user.is_staff and not request.user.is_superuser:
            return obj is not None  # Staff can only change existing questions, not create new ones
        return super().has_change_permission(request, obj)

    def has_add_permission(self, request):
        """
        Prevent staff users from adding new questions.
        """
        if request.user.is_staff and not request.user.is_superuser:
            return False  # No adding allowed for staff
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        """
        Prevent staff users from deleting questions.
        """
        if request.user.is_staff and not request.user.is_superuser:
            return False  # No deleting allowed for staff
        return super().has_delete_permission(request, obj)


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'time', 'status', 'moderator', 'created_at', 'updated_at')
    list_filter = ('status', 'date', 'moderator')  # Filter by status, date, and moderator
    search_fields = ('user__email', 'moderator__email', 'message')  # Enable search on usernames and message

    # Make the status editable directly from the list view
    list_editable = ('status',)

    def save_model(self, request, obj, form, change):
        # If the status has been updated, assign the current user as the moderator
        if 'status' in form.changed_data:
            obj.moderator = request.user
        super().save_model(request, obj, form, change)


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'amount_total', 'currency', 'payment_status', 'created_at')
    search_fields = ('transaction_id', 'customer_name', 'customer_email', 'user__email')
    list_filter = ('payment_status', 'currency', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'company', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'company')


admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(User, UserAdmin)
admin.site.site_header = "Edu Grow Consulting"
admin.site.site_title = "Edu Grow Consulting"
admin.site.index_title = "Welcome to the Admin Dashboard"
