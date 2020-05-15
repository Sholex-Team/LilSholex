from django.contrib import admin
from support import models


@admin.register(models.User)
class User(admin.ModelAdmin):
    list_display = ('chat_id', 'menu', 'register_date')
    readonly_fields = ('chat_id', 'register_date', 'last_activity')
    search_fields = ('chat_id', 'menu')
    list_filter = ('rank',)
    date_hierarchy = 'register_date'
    fieldsets = (
        ('Information', {'fields': ('chat_id', 'register_date', 'last_activity')}),
        ('Status', {'fields': ('status', 'menu', 'rank', 'current_message')})
    )


@admin.register(models.Message)
class Message(admin.ModelAdmin):
    list_display = ('message_id', 'webapp', 'sending_date', 'admin')
    readonly_fields = ('message_id', 'sending_date')
    search_fields = ('text',)
    list_filter = ('webapp', 'admin')
    date_hierarchy = 'sending_date'
    fieldsets = (
        ('Information', {'fields': ('message_id', 'sending_date')}),
        ('Message', {'fields': ('text', 'message_unique_id', ('message_type', 'webapp'))}),
        ('Answered', {'fields': ('admin', 'answering_date')})
    )
