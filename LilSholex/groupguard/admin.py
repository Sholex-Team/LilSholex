from django.contrib import admin
from groupguard import models
from groupguard.functions import get_chat, get_chat_administrators
from django.http import JsonResponse


@admin.register(models.User)
class User(admin.ModelAdmin):
    list_display = ('chat_id', 'status', 'username', 'phone_number', 'register_date')
    date_hierarchy = 'register_date'
    search_fields = ('menu', 'chat_id', 'username', 'phone_number')
    readonly_fields = ('chat_id', 'register_date', 'last_activity')
    fieldsets = (
        ('Information', {'fields': ('chat_id', 'register_date', 'lang', 'username', 'phone_number')}),
        ('Status', {'fields': ('status', 'rank', 'menu', 'last_activity', 'mutes', 'number_pass')})
    )
    list_filter = ('status', 'menu', 'rank')
    list_per_page = 15


@admin.register(models.Group)
class Group(admin.ModelAdmin):
    list_display = ['chat_id', 'status', 'register_date']
    date_hierarchy = 'register_date'
    search_fields = ['chat_id', 'owner__chat_id', 'owner__username']
    readonly_fields = ['chat_id', 'register_date']
    actions = ['get_group', 'get_admins', 'promote', 'demote']
    fieldsets = [
        ('Information', {'fields': ('chat_id', 'register_date', 'owner', 'channel', 'rules', 'lang', 'promoted')}),
        ('Status', {'fields': ('status', 'white_list', 'last_permissions')}),
        ('Punishing', {'fields': ('punish', ('max_warn', 'max_warn_punish'), 'clear_days')}),
        ('Locks', {'fields': (
            ('id_lock', 'link_lock', 'curse_lock'),
            ('sharp_lock', 'text_lock', 'forward_lock'),
            ('image_lock', 'video_lock', 'sticker_lock'),
            ('location_lock', 'phone_number_lock', 'voice_message_lock'),
            ('video_message_lock', 'document_lock', 'gif_lock'),
            ('poll_lock', 'game_lock', 'english_lock'),
            ('persian_lock', 'contact_lock', 'bot_lock'),
            ('services_lock', 'inline_keyboard_lock')
        )}),
        ('Welcoming', {'fields': ('is_welcome_message', 'welcome_message')}),
        ('Anti Spam', {'fields': ('anti_spam', 'max_messages', 'spam_punish', 'spam_time')}),
        ('Reporting', {'fields': ('reporting', 'max_reports')}),
        ('Bot Messages', {'fields': ('deleting', 'delete_time')}),
        ('Validation', {'fields': ('anti_tabchi', 'tabchi_time', 'number_range')}),
        ('Forced Add', {'fields': ('force_count',)}),
        ('Filters', {'fields': ('words',)}),
        ('Auto Lock', {'fields': ('auto_lock', 'auto_lock_on', 'auto_lock_off', 'is_checking')})
    ]
    list_filter = ('status', 'promoted', 'auto_lock', 'anti_spam')
    list_per_page = 15

    def get_group(self, request, queryset):
        return JsonResponse([get_chat(group.chat_id) for group in queryset], safe=False)

    def get_admins(self, request, queryset):
        return JsonResponse([get_chat_administrators(group.chat_id) for group in queryset], safe=False)

    def promote(self, request, queryset):
        if (result := queryset.update(promoted=True)) == 0:
            self.message_user(request, 'There is no need to promote these groups !')
        elif result == 1:
            self.message_user(request, '1 Group has been promoted !')
        else:
            self.message_user(request, f'{result} Groups have been promoted !')

    def demote(self, request, queryset):
        if (result := queryset.update(promoted=False)) == 0:
            self.message_user(request, 'There is no need to demote these groups !')
        elif result == 1:
            self.message_user(request, '1 Group has been demoted !')
        else:
            self.message_user(request, f'{result} Groups have been demoted !')

    get_admins.short_descriptions = 'Get Group Admins'
    promote.short_descriptions = 'Promote Groups'
    demote.short_descriptions = 'Demote Groups'
    get_chat.short_description = 'Get Group Info'


@admin.register(models.Warn)
class Warn(admin.ModelAdmin):
    list_display = ['warn_id', 'count', 'last_edit']
    date_hierarchy = 'last_edit'
    search_fields = ['user__chat_id', 'group__chat_id']
    readonly_fields = ['warn_id', 'last_edit']
    fieldsets = [('Information', {'fields': ('warn_id', ('user', 'group'), 'count', 'last_edit')})]
    list_per_page = 15


@admin.register(models.Login)
class Login(admin.ModelAdmin):
    list_display = ['login_token', 'user', 'ip']
    date_hierarchy = 'login_date'
    search_fields = ('ip', 'login_token', 'user__username', 'group__chat_id', 'user__chat_id')
    readonly_fields = ['login_token', 'ip', 'login_date', 'creation_date']
    fieldsets = [('Information', {'fields': ('login_token', ('user', 'group'), ('login_date', 'creation_date'), 'ip')})]
    list_per_page = 15


@admin.register(models.Word)
class Word(admin.ModelAdmin):
    list_display = ['text']
    search_fields = ['text']
    fieldsets = [('Information', {'fields': ('text',)})]
    list_per_page = 15


@admin.register(models.Activity)
class Activity(admin.ModelAdmin):
    list_display = ['activity_id', 'count', 'last_message']
    readonly_fields = ['last_message', 'activity_id']
    date_hierarchy = 'last_message'
    search_fields = ['user', 'activity_id']
    fieldsets = [('Information', {'fields': (
        'activity_id', 'user', 'group', 'count', 'last_message', 'messages', 'restricted'
    )})]
    list_per_page = 15


@admin.register(models.Curse)
class Curse(admin.ModelAdmin):
    list_display = ('curse_id',)
    readonly_fields = ('curse_id',)
    search_fields = ('word',)
    fieldsets = (('Information', {'fields': ('curse_id', 'word')}),)
    list_per_page = 15


@admin.register(models.Ad)
class Ad(admin.ModelAdmin):
    list_display = ('ad_id', 'chat_id')
    readonly_fields = ('ad_id',)
    search_fields = ('chat_id', 'message_id')
    list_filter = ('chat_id',)
    fieldsets = (('Information', {'fields': ('ad_id', 'chat_id', 'message_id', 'seen')}),)
    list_per_page = 15


@admin.register(models.Command)
class Command(admin.ModelAdmin):
    list_display = ('command_id', 'cmd', 'permission')
    readonly_fields = ('command_id',)
    search_fields = ('cmd', 'answer', 'group__chat_id')
    list_filter = ('permission',)
    fieldsets = (('Information', {'fields': ('command_id', 'cmd', 'group', 'answer')}),)
    list_per_page = 15


@admin.register(models.Message)
class Message(admin.ModelAdmin):
    list_display = ('message_id', 'message_unique_id', 'reports')
    search_fields = ('message_id', 'message_unique_id', 'user__chat_id', 'group__chat_id')
    readonly_fields = ('message_id',)
    fieldsets = (('Information', {'fields': (
        'message_id', 'message_unique_id', ('reports', 'reporters'), ('group', 'user')
    )}),)
    list_per_page = 15


@admin.register(models.Verify)
class Verify(admin.ModelAdmin):
    list_display = ('verify_id', 'validated', 'valid_until')
    readonly_fields = ('verify_id',)
    search_fields = ('verify_id', 'user__chat_id', 'group__chat_id')
    list_filter = ('validated',)
    date_hierarchy = 'valid_until'
    list_per_page = 15
    fieldsets = (('Information', {'fields': ('verify_id', 'validated', 'user', 'group')}),)


@admin.register(models.ForcedAdd)
class ForcedAdd(admin.ModelAdmin):
    list_display = ('add_id', 'user', 'group', 'added_number')
    readonly_fields = ('add_id',)
    list_filter = ('promoted',)
    search_fields = ('add_id', 'user__chat_id', 'group__chat_id')
    list_per_page = 15
    fieldsets = (('Information', {'fields': ('add_id', 'added_number', 'user', 'group', 'promoted')}),)
