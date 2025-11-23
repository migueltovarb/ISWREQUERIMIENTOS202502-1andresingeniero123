from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, Activity, Assignment, Attendance, Notification

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('role', 'document_id', 'phone', 'address', 'areas_of_interest', 'profile_image')}),
    )
    list_display = ('username', 'email', 'role', 'profile_image_display')
    list_filter = ('role',)

    def profile_image_display(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.profile_image.url)
        return '(Sin Imagen)'
    profile_image_display.short_description = 'Imagen de Perfil'

admin.site.register(Activity)
admin.site.register(Assignment)
admin.site.register(Attendance)
admin.site.register(Notification)
