from django.contrib import admin
from persianmeme import models
from django.http import HttpResponse
from django.core.serializers import serialize
from persianmeme.functions import delete_vote_sync
from django.conf import settings
from random import randint
change_permission = ('change',)


@admin.display(description='Export as Json')
def export_json(costume_admin, request, queryset):
    return HttpResponse(serialize('json', queryset), content_type='application/json')


@admin.display(description='Playlists Count')
def count_playlists(obj: models.User):
    return obj.playlists.count()


@admin.display(description='Voices Count')
def count_voices(obj: models.Playlist):
    return obj.voices.count()


def current_playlist(obj: models.User):
    return obj.current_playlist.name if obj.current_playlist else None


def current_voice(obj: models.User):
    return obj.current_voice.name if obj.current_voice else None


@admin.display(description='Deny Votes Count')
def count_deny_votes(obj: models.Voice):
    return obj.deny_vote.count()


@admin.display(description='Accept Votes Count')
def count_accept_votes(obj: models.Voice):
    return obj.accept_vote.count()


@admin.display(description='Tags Count')
def count_tags(obj: models.Voice):
    return obj.tags.count()


@admin.register(models.User)
class User(admin.ModelAdmin):
    @admin.display(description='Ban')
    def ban_user(self, request, queryset):
        result = queryset.update(status='b')
        if result == 0:
            self.message_user(request, 'There is no need to banned these users !')
        elif result == 1:
            self.message_user(request, '1 User has been banned !')
        else:
            self.message_user(request, f'{result} Users have been banned !')

    @admin.display(description='Full Ban')
    def full_ban(self, request, queryset):
        result = queryset.update(status='f')
        if result == 0:
            self.message_user(request, 'There is no need to full banned these users !')
        elif result == 1:
            self.message_user(request, '1 User has been full banned !')
        else:
            self.message_user(request, f'{result} Users have been banned !')

    @admin.display(description='Unban')
    def unban_user(self, request, queryset):
        result = queryset.update(status='a')
        if result == 0:
            self.message_user(request, 'There is no need to unbanned these users !')
        elif result == 1:
            self.message_user(request, '1 User has been unbanned .')
        else:
            self.message_user(request, f'{result} Users have been unbanned .')

    unban_user.allowed_permissions = change_permission
    ban_user.allowed_permissions = change_permission
    full_ban.allowed_permissions = change_permission
    date_hierarchy = 'last_usage_date'
    list_display = (
        'user_id',
        'chat_id',
        'menu',
        'rank',
        'status',
        'date',
        'username',
        'menu_mode'
    )
    list_filter = ('status', 'rank', 'vote', 'started', 'voice_order', 'menu_mode')
    list_per_page = 15
    search_fields = ('user_id', 'chat_id', 'username')
    readonly_fields = ('user_id', 'date', 'last_usage_date')
    actions = (unban_user, full_ban, ban_user, export_json)
    raw_id_fields = (
        'favorite_voices',
        'last_broadcast',
        'playlists',
        'current_playlist',
        'current_voice',
        'current_ad',
        'temp_voice_tags'
    )
    fieldsets = (
        ('Information', {'fields': ('user_id', 'chat_id', 'rank', 'vote', 'username', 'date', 'voice_order')}),
        ('Status', {'fields': (
            'menu',
            'status',
            'started',
            'last_usage_date',
            'last_start',
            'menu_mode',
            'current_playlist',
            'current_voice',
            'current_ad',
            'last_broadcast'
        )}),
        ('Voices', {'fields': ('favorite_voices', 'playlists')}),
        ('Temporary Values', {'fields': ('temp_voice_name', 'temp_user_id', 'temp_voice_tags')})
    )


@admin.register(models.Voice)
class Voice(admin.ModelAdmin):
    @admin.display(description='Accept Votes')
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

    @admin.display(description='Deny Vote')
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

    @admin.display(description='Add Fake Deny Votes')
    def add_fake_deny_votes(self, request, queryset):
        if (user_count := models.User.objects.count()) < settings.MIN_FAKE_VOTE:
            fake_min = user_count
            fake_max = user_count
        else:
            fake_min = settings.MIN_FAKE_VOTE
            if user_count < settings.MAX_FAKE_VOTE:
                fake_max = user_count
            else:
                fake_max = settings.MAX_FAKE_VOTE
        faked_count = 0
        for voice in queryset:
            if voice.status == voice.Status.PENDING and \
                    voice.deny_vote.count() < (random_fake := randint(fake_min, fake_max)):
                faked_count += 1
                voice.deny_vote.set(models.User.objects.all()[:random_fake])
        if faked_count == 0:
            self.message_user(request, 'There is no need to add fake votes !')
        elif faked_count == 1:
            self.message_user(request, 'Fake votes have been added to a voice !')
        else:
            self.message_user(request, f'Fake votes has been added to {faked_count} voices !')

    add_fake_deny_votes.allowed_permissions = change_permission
    date_hierarchy = 'date'
    list_display = ('voice_id', 'name', 'sender', 'votes', 'status', count_deny_votes, count_accept_votes, count_tags)
    list_filter = ('status', 'voice_type')
    search_fields = ('name', 'sender__chat_id', 'file_id', 'file_unique_id', 'voice_id', 'sender__user_id')
    actions = (export_json, accept_vote, deny_vote, add_fake_deny_votes)
    list_per_page = 15
    readonly_fields = ('voice_id', 'date', 'last_check')
    raw_id_fields = ('sender', 'voters', 'accept_vote', 'deny_vote', 'tags')
    fieldsets = (
        ('Information', {'fields': ('voice_id', 'file_id', 'name', 'file_unique_id', 'date', 'sender', 'tags')}),
        ('Status', {'fields': (
            'status', 'votes', 'voice_type', 'last_check', 'voters', 'accept_vote', 'deny_vote'
        )})
    )


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
    raw_id_fields = ('voice', 'user')
    fieldsets = (('Information', {'fields': ('delete_id', 'voice', 'user')}),)


@admin.register(models.Broadcast)
class Broadcast(admin.ModelAdmin):
    list_display = ('id', 'message_id', 'sender', 'sent')
    list_filter = ('sent',)
    search_fields = ('id', 'message_id', 'sender__chat_id', 'sender__username')
    list_per_page = 15
    readonly_fields = ('id',)
    raw_id_fields = ('sender',)
    fieldsets = (('Information', {'fields': ('id', 'message_id', 'sender')}), ('Status', {'fields': ('sent',)}))


@admin.register(models.Playlist)
class Playlist(admin.ModelAdmin):
    list_display = ('id', 'name', count_voices, 'creator', 'date')
    date_hierarchy = 'date'
    list_filter = ('creator__rank', 'creator__status')
    search_fields = ('name', 'id', 'creator__username', 'creator__chat_id')
    list_per_page = 15
    readonly_fields = ('id', 'date')
    raw_id_fields = ('voices', 'creator')
    fieldsets = (('Information', {'fields': ('id', 'name', 'date', 'voices', 'creator')}),)


@admin.register(models.Message)
class Message(admin.ModelAdmin):
    list_display = ('id', 'sender', 'status')
    list_filter = ('status',)
    raw_id_fields = ('sender',)
    search_fields = ('id', 'sender__username', 'sender__user_id', 'sender__chat_id')
    list_per_page = 15
    readonly_fields = ('id',)
    fieldsets = (('Information', {'fields': ('id', 'sender')}), ('Status', {'fields': ('status',)}))


@admin.register(models.VoiceTag)
class VoiceTag(admin.ModelAdmin):
    list_display = ('tag',)
    search_fields = ('tag',)
    list_per_page = 30
    fieldsets = (('Information', {'fields': ('tag',)}),)
