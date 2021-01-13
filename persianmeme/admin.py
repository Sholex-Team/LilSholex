from django.contrib import admin
from persianmeme import models
from django.http import HttpResponse
from django.core.serializers import serialize
from persianmeme.functions import delete_vote_sync


def export_json(costume_admin, request, queryset):
    return HttpResponse(serialize('json', queryset), content_type='application/json')


def count_playlists(obj: models.User):
    return obj.playlists.count()


def count_voices(obj: models.Playlist):
    return obj.voices.count()


def current_playlist(obj: models.User):
    return obj.current_playlist.name if obj.current_playlist else None


def current_voice(obj: models.User):
    return obj.current_voice.name if obj.current_voice else None


count_playlists.short_description = 'Playlists Count'
export_json.short_description = 'Export as Json'
count_voices.short_description = 'Voices Count'
current_playlist.short_description = 'Current Playlist'


@admin.register(models.User)
class User(admin.ModelAdmin):
    def ban_user(self, request, queryset):
        result = queryset.update(status='b')
        if result == 0:
            self.message_user(request, 'There is no need to banned these users !')
        elif result == 1:
            self.message_user(request, '1 User has been banned !')
        else:
            self.message_user(request, f'{result} Users have been banned !')

    def full_ban(self, request, queryset):
        result = queryset.update(status='f')
        if result == 0:
            self.message_user(request, 'There is no need to full banned these users !')
        elif result == 1:
            self.message_user(request, '1 User has been full banned !')
        else:
            self.message_user(request, f'{result} Users have been banned !')

    def unban_user(self, request, queryset):
        result = queryset.update(status='a')
        if result == 0:
            self.message_user(request, 'There is no need to unbanned these users !')
        elif result == 1:
            self.message_user(request, '1 User has been unbanned .')
        else:
            self.message_user(request, f'{result} Users have been unbanned .')

    unban_user.short_description = 'Unban'
    full_ban.short_description = 'Full Ban'
    ban_user.short_description = 'Ban'
    date_hierarchy = 'last_usage_date'
    list_display = (
        'user_id',
        'chat_id',
        'menu',
        'rank',
        'status',
        'date',
        'username',
        'menu_mode',
        count_playlists,
        current_playlist,
        current_voice
    )
    list_filter = ('status', 'rank', 'sent_message', 'vote', 'started', 'voice_order', 'menu_mode')
    list_per_page = 15
    search_fields = ('chat_id', 'username')
    readonly_fields = ('user_id', 'date', 'last_usage_date')
    actions = [export_json, ban_user, full_ban, unban_user]
    fieldsets = [
        ('Information', {'fields': ('user_id', 'chat_id', 'rank', 'vote', 'username', 'date', 'voice_order')}),
        ('Status', {'fields': (
            'menu', 'status', 'sent_message', 'started', 'last_usage_date', 'last_start', 'menu_mode'
        )})
    ]


@admin.register(models.Voice)
class Voice(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('voice_id', 'file_id', 'name', 'sender', 'votes', 'status')
    list_filter = ('status', 'voice_type')
    search_fields = ('name', 'sender__chat_id', 'file_id', 'file_unique_id', 'voice_id')
    actions = (export_json, 'accept_vote', 'deny_vote')
    list_per_page = 15
    readonly_fields = ('voice_id', 'date', 'last_check')
    fieldsets = (
        ('Information', {'fields': ('voice_id', 'file_id', 'name', 'file_unique_id', 'date')}),
        ('Status', {'fields': ('status', 'votes', 'voice_type', 'last_check')})
    )

    def accept_vote(self, request, queryset):
        result = [
            (target_voice, target_voice.accept(), delete_vote_sync(target_voice))
            for target_voice in queryset if target_voice.status == 'p'
        ]
        result_len = len(result)
        if result_len == 0:
            self.message_user(request, 'There is no need to accept these voices !')
        elif result_len == 1:
            self.message_user(request, f'{result[0][0]} has been accepted !')
        else:
            self.message_user(request, f'{result_len} Voices have been accepted !')

    def deny_vote(self, request, queryset):
        result = [
            (target_voice, target_voice.deny(), delete_vote_sync(target_voice))
            for target_voice in queryset if target_voice.status == 'p'
        ]
        result_len = len(result)
        if result_len == 0:
            self.message_user(request, 'There is no need to deny these voices !')
        else:
            queryset.delete()
            if result_len == 1:
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


@admin.register(models.Broadcast)
class Broadcast(admin.ModelAdmin):
    list_display = ('id', 'message_id', 'sender', 'sent')
    list_filter = ('sent',)
    search_fields = ('id', 'message_id', 'sender__chat_id', 'sender__username')
    list_per_page = 15
    readonly_fields = ('id',)
    fieldsets = (('Information', {'fields': ('id', 'message_id')}), ('Status', {'fields': ('sent',)}))


@admin.register(models.Playlist)
class Playlist(admin.ModelAdmin):
    list_display = ('id', 'name', count_voices, 'creator', 'date')
    date_hierarchy = 'date'
    list_filter = ('creator__rank', 'creator__status')
    search_fields = ('name', 'id', 'creator__username', 'creator__chat_id')
    list_per_page = 15
    readonly_fields = ('id', 'date')
    fieldsets = (('Information', {'fields': ('id', 'name', 'date')}),)
