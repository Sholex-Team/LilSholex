from django.contrib import admin
from . import models
from django.http import HttpRequest
from .functions import fake_deny_vote

change_permission = ('change',)


@admin.display(description='Playlists Count')
def count_playlists(obj: models.User):
    return obj.playlists.count()


@admin.display(description='Voices Count')
def count_voices(obj: models.Playlist):
    return obj.voices.count()


def current_playlist(obj: models.User):
    return obj.current_playlist.name if obj.current_playlist else None


def current_meme(obj: models.User):
    return obj.current_meme.name if obj.current_meme else None


@admin.display(description='Deny Votes Count')
def count_deny_votes(obj: models.Meme):
    return obj.deny_vote.count()


@admin.display(description='Accept Votes Count')
def count_accept_votes(obj: models.Meme):
    return obj.accept_vote.count()


@admin.display(description='Reporters Count')
def count_reporters(obj: models.Report):
    return obj.reporters.count()


class UsernameInline(admin.TabularInline):
    extra = 0
    model = models.Username
    readonly_fields = ('creation_date',)


class RecentMemeInline(admin.TabularInline):
    extra = 0
    model = models.RecentMeme
    raw_id_fields = ('meme',)


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    @admin.display(description='Ban')
    def ban_user(self, request: HttpRequest, queryset):
        result = queryset.update(status=models.User.Status.BANNED)
        if result == 0:
            self.message_user(request, 'There is no need to banned these users !')
        elif result == 1:
            self.message_user(request, '1 User has been banned !')
        else:
            self.message_user(request, f'{result} Users have been banned !')

    @admin.display(description='Full Ban')
    def full_ban(self, request: HttpRequest, queryset):
        result = queryset.update(status=models.User.Status.FULL_BANNED)
        if result == 0:
            self.message_user(request, 'There is no need to full banned these users !')
        elif result == 1:
            self.message_user(request, '1 User has been full banned !')
        else:
            self.message_user(request, f'{result} Users have been banned !')

    @admin.display(description='Unban')
    def unban_user(self, request: HttpRequest, queryset):
        result = queryset.update(status=models.User.Status.ACTIVE)
        if result == 0:
            self.message_user(request, 'There is no need to unbanned these users !')
        elif result == 1:
            self.message_user(request, '1 User has been unbanned .')
        else:
            self.message_user(request, f'{result} Users have been unbanned.')

    unban_user.allowed_permissions = change_permission
    ban_user.allowed_permissions = change_permission
    full_ban.allowed_permissions = change_permission
    date_hierarchy = 'last_usage_date'
    list_display = (
        'user_id',
        'chat_id',
        'last_usage_date',
        'rank',
        'status',
        'date',
        'menu_mode'
    )
    list_filter = (
        'status', 'rank', 'vote', 'started', 'meme_ordering', 'menu_mode', 'use_recent_memes', 'search_items'
    )
    list_per_page = 15
    search_fields = ('user_id', 'chat_id')
    readonly_fields = ('user_id', 'date', 'last_usage_date')
    actions = (unban_user, full_ban, ban_user)
    raw_id_fields = (
        'last_broadcast',
        'playlists',
        'current_playlist',
        'current_meme',
        'recent_memes'
    )
    fieldsets = (
        ('Information', {'fields': (
            'user_id', 'chat_id', 'rank', 'vote', 'date', 'meme_ordering', 'search_items'
        )}),
        ('Status', {'fields': (
            'menu',
            'status',
            'started',
            'last_usage_date',
            'last_start',
            'menu_mode',
            'current_playlist',
            'current_meme',
            'last_broadcast',
            'use_recent_memes',
            'report_violation_count'
        )}),
        ('Memes', {'fields': ('playlists',)}),
        ('Temporary Values', {'fields': ('temp_meme_name', 'temp_user_id', 'temp_meme_tags', 'temp_meme_type')})
    )
    inlines = (UsernameInline, RecentMemeInline)


@admin.register(models.NewMeme)
class NewMemeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'sender', 'type', 'status', 'visibility', 'usage_count'
    )
    list_filter = ('status', 'visibility', 'type')
    search_fields = ('name', 'sender__chat_id', 'file_id', 'file_unique_id', 'id', 'sender__user_id', 'description')
    list_per_page = 15
    readonly_fields = ('id',)
    raw_id_fields = ('sender', 'playlist_voice')


@admin.register(models.Meme)
class MemeAdmin(NewMemeAdmin):
    @admin.display(description='Add Fake Deny Votes')
    def add_fake_deny_votes(self, request: HttpRequest, queryset):
        if (faked_count := fake_deny_vote(queryset)) == 0:
            self.message_user(request, 'There is no need to add fake votes !')
        elif faked_count == 1:
            self.message_user(request, 'Fake votes have been added to a meme !')
        else:
            self.message_user(request, f'Fake votes has been added to {faked_count} memes !')

    @admin.display(description='Recover Memes')
    def recover_memes(self, request: HttpRequest, queryset):
        if not (recovered_memes_count := queryset.filter(status=models.Meme.Status.DELETED).update(
                status=models.Meme.Status.ACTIVE
        )):
            self.message_user(request, 'There isn\'t any meme to recover !')
        elif recovered_memes_count == 1:
            self.message_user(request, 'One meme has been recovered.')
        else:
            self.message_user(request, f'{recovered_memes_count} memes have been recovered.')

    @admin.display(description='Ban Senders')
    def ban_senders(self, request: HttpRequest, queryset):
        if not (banned_senders_count := models.User.objects.filter(user_id__in=tuple(queryset.filter(
                sender__status=models.User.Status.ACTIVE
        ).values_list('sender', flat=True).distinct())).update(status=models.User.Status.BANNED)):
            self.message_user(request, 'There isn\'t any sender to ban !')
        elif banned_senders_count == 1:
            self.message_user(request, 'One sender has been banned.')
        else:
            self.message_user(request, f'{banned_senders_count} senders have been banned.')

    add_fake_deny_votes.allowed_permissions = change_permission
    recover_memes.allowed_permissions = change_permission
    ban_senders.allowed_permissions = change_permission
    date_hierarchy = 'date'
    list_display = (*NewMemeAdmin.list_display, count_deny_votes, count_accept_votes)
    list_filter = (*NewMemeAdmin.list_filter, 'reviewed', 'previous_status')
    actions = (add_fake_deny_votes, recover_memes, ban_senders)
    readonly_fields = (*NewMemeAdmin.readonly_fields, 'date')
    raw_id_fields = (*NewMemeAdmin.raw_id_fields, 'voters', 'accept_vote', 'deny_vote', 'review_admin')
    fieldsets = (
        ('Information', {'fields': (
            'id',
            'file_id',
            'name',
            'file_unique_id',
            'description',
            'date',
            'sender',
            'tags',
            'review_admin',
            'message_id',
            'type'
        )}),
        ('Status', {'fields': (
            'status',
            'votes',
            'visibility',
            'voters',
            'accept_vote',
            'deny_vote',
            'usage_count',
            'reviewed',
            'previous_status',
            'task_id'
        )})
    )


@admin.register(models.Delete)
class DeleteAdmin(admin.ModelAdmin):
    list_display = ('id', 'meme', 'user')
    readonly_fields = ('id',)
    search_fields = (
        'id', 'user__user_id', 'user__chat_id', 'meme__id', 'meme__file_id', 'meme__file_unique_id'
    )
    raw_id_fields = ('meme', 'user')
    fieldsets = (('Information', {'fields': ('id', 'meme', 'user')}),)


@admin.register(models.Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ('id', 'message_id', 'sender', 'sent')
    list_filter = ('sent',)
    search_fields = ('id', 'message_id', 'sender__chat_id', 'sender__user_id')
    list_per_page = 15
    readonly_fields = ('id',)
    raw_id_fields = ('sender',)
    fieldsets = (('Information', {'fields': ('id', 'message_id', 'sender')}), ('Status', {'fields': ('sent',)}))


@admin.register(models.PlaylistVoice)
class PlaylistVoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'playlist', 'voice')
    search_fields = ('id', 'playlist__name', 'voice__name', 'voice__file_unique_id', 'playlist__invite_link')
    list_per_page = 20
    raw_id_fields = ('playlist', 'voice')


@admin.register(models.Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', count_voices, 'creator',)
    list_filter = ('creator__rank', 'creator__status')
    search_fields = ('name', 'id', 'creator__user_id', 'creator__chat_id')
    list_per_page = 15
    raw_id_fields = ('creator',)


@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'status')
    list_filter = ('status',)
    raw_id_fields = ('sender',)
    search_fields = ('id', 'sender__user_id', 'sender__chat_id')
    list_per_page = 15
    readonly_fields = ('id',)
    fieldsets = (('Information', {'fields': ('id', 'sender')}), ('Status', {'fields': ('status',)}))


@admin.register(models.RecentMeme)
class RecentMemeAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', 'meme')
    readonly_fields = ('id',)
    list_display = ('id', 'user', 'meme')
    list_per_page = 30
    search_fields = (
        'id',
        'user__user_id',
        'meme__id'
    )
    fieldsets = (('Information', {'fields': ('id', 'user', 'meme')}),)


@admin.register(models.Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('meme', count_reporters, 'status', 'report_date', 'reviewer', 'review_date')
    list_filter = ('status',)
    list_per_page = 20
    search_fields = (
        'reporters__user_id',
        'reporters__chat_id',
        'meme__id',
        'meme__name',
        'meme__file_unique_id'
    )
    readonly_fields = ('report_date',)
    raw_id_fields = ('meme', 'reporters', 'reviewer')
    fieldsets = (
        ('Information', {'fields': ('meme', 'reporters', 'report_date', 'reviewer', 'review_date')}),
        ('Status', {'fields': ('status',)})
    )


@admin.register(models.Username)
class UsernameAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'username', 'creation_date')
    date_hierarchy = 'creation_date'
    search_fields = ('user__chat_id', 'user__user_id', 'username')
    list_per_page = 30
    raw_id_fields = ('user',)
    readonly_fields = ('id', 'creation_date')
    fieldsets = (('Information', {'fields': ('id', 'user', 'username', 'creation_date')}),)
