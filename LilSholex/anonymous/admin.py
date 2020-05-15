from django.contrib import admin
from anonymous import models, functions
from django.http import JsonResponse


@admin.register(models.User)
class User(admin.ModelAdmin):
    date_hierarchy = 'last_usage_date'
    list_display = ('chat_id', 'username', 'nick_name', 'menu', 'status', 'rank')
    list_filter = ('menu', 'status', 'rank')
    readonly_fields = ('chat_id', 'last_usage_date')
    list_per_page = 15
    search_fields = ('chat_id', 'token', 'username')
    actions = ['get_chat']
    fieldsets = (
        ('Information', {'fields': ('chat_id', ('username', 'nick_name'), 'token', 'rank', 'last_usage_date')}),
        ('Status', {'fields': ('menu', 'status', 'black_list')})
    )

    def get_chat(self, request, queryset):
        return JsonResponse([functions.get_chat(group.chat_id) for group in queryset], safe=False)

    get_chat.short_description = 'Get Chat Info'


@admin.register(models.Message)
class Message(admin.ModelAdmin):
    date_hierarchy = 'sending_date'
    list_display = ('message_id', 'sender', 'receiver', 'sending_date')
    readonly_fields = ('message_id', 'sending_date', 'reading_date')
    list_per_page = 15
    list_filter = ('is_read',)
    search_fields = ('text', 'message_id')
    fieldsets = (
        ('Information', {'fields': ('message_id', 'text')}),
        ('Status', {'fields': ('sender', 'receiver', 'sending_date', 'reading_date', 'is_read')})
    )
