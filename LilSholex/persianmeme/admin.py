from django.contrib import admin
from persianmeme import models
from django.http import HttpResponse
from django.core.serializers import serialize
from persianmeme.functions import delete_vote


def export_json(costume_admin, request, queryset):
    return HttpResponse(serialize('json', queryset), content_type='application/json')


def ban_user(costume_admin, request, queryset):
    if (result := queryset.update(status='b')) == 0:
        costume_admin.message_user(request, 'There is no need to banned these users !')
    elif result == 1:
        costume_admin.message_user(request, '1 User has been banned !')
    else:
        costume_admin.message_user(request, f'{result} Users have been banned !')


def full_ban(costume_admin, request, queryset):
    if (result := queryset.update(status='f')) == 0:
        costume_admin.message_user(request, 'There is no need to full banned these users !')
    elif result == 1:
        costume_admin.message_user(request, '1 User has been full banned !')
    else:
        costume_admin.message_user(request, f'{result} Users have been banned !')


def unban_user(costume_admin, request, queryset):
    if (result := queryset.update(status='a')) == 0:
        costume_admin.message_user(request, 'There is no need to unbanned these users !')
    elif result == 1:
        costume_admin.message_user(request, '1 User has been unbanned .')
    else:
        costume_admin.message_user(request, f'{result} Users have been unbanned .')


def not_sent_voice(costume_admin, request, queryset):
    result = queryset.update(sent_voice=False)
    if result == 0:
        costume_admin.message_user(request, 'Nothing changed ...')
    elif result == 1:
        costume_admin.message_user(request, '1 User has been updated .')
    else:
        costume_admin.message_user(request, f'{result} users have been updated .')


export_json.short_description = 'Export as Json'
unban_user.short_description = 'Unban'
full_ban.short_description = 'Full Ban'
ban_user.short_description = 'Ban'
not_sent_voice.short_description = 'Turn off Sent Voice'


@admin.register(models.User)
class User(admin.ModelAdmin):
    date_hierarchy = 'last_usage_date'
    list_display = ('user_id', 'chat_id', 'menu', 'rank', 'status', 'date', 'username')
    list_filter = ('status', 'rank', 'sent_message', 'sent_voice', 'vote')
    list_per_page = 15
    search_fields = ('chat_id', 'username')
    actions = [export_json, ban_user, full_ban, unban_user, not_sent_voice]
    fieldsets = [
        ('Information', {'fields': ('chat_id', 'rank', 'last_date', 'vote', 'username')}),
        ('Status', {'fields': ('count', 'menu', 'status', 'sent_message', 'sent_voice')})
    ]


@admin.register(models.Voice)
class Voice(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ['voice_id', 'file_id', 'name', 'sender', 'votes', 'status']
    list_filter = ['status', 'voice_type']
    search_fields = ['name', 'sender__chat_id', 'file_id', 'file_unique_id', 'voice_id']
    actions = [export_json, 'accept_vote', 'deny_vote']
    list_per_page = 15
    fieldsets = [
        ('Information', {'fields': ('file_id', 'name', 'file_unique_id')}),
        ('Status', {'fields': ('status', 'votes', 'voice_type')})
    ]

    def accept_vote(self, request, queryset):
        result = [
            (target_voice, target_voice.accept(), delete_vote(target_voice))
            for target_voice in queryset if target_voice.status == 'p'
        ]
        if (result_len := len(result)) == 0:
            self.message_user(request, 'There is no need to accept these voices !')
        elif result_len == 1:
            self.message_user(request, f'{result[0][0]} has been accepted !')
        else:
            self.message_user(request, f'{result_len} Voices have been accepted !')

    def deny_vote(self, request, queryset):
        result = [
            (target_voice, target_voice.deny(), delete_vote(target_voice))
            for target_voice in queryset if target_voice.status == 'p'
        ]
        if (result_len := len(result)) == 0:
            self.message_user(request, 'There is no need to deny these voices !')
        elif result_len == 1:
            self.message_user(request, f'{result[0][0]} has been denied !')
        else:
            self.message_user(request, f'{result_len} Voices have been denied !')


@admin.register(models.Ad)
class Ad(admin.ModelAdmin):
    list_display = ('ad_id', 'chat_id', 'message_id')
    readonly_fields = ('ad_id',)
    search_fields = ('chat_id', 'message_id', 'seen__chat_id')
    list_filter = ('chat_id',)
    fieldsets = (('Information', {'fields': ('ad_id', 'chat_id', 'message_id', 'seen')}),)


@admin.register(models.Delete)
class Delete(admin.ModelAdmin):
    list_display = ('delete_id', 'voice', 'user')
    readonly_fields = ('delete_id',)
    search_fields = (
        'delete_id', 'user__username', 'user__chat_id', 'voice__voice_id', 'voice__file_id', 'voice__file_unique_id'
    )
    fieldsets = (('Information', {'fields': ('delete_id', 'voice', 'user')}),)
