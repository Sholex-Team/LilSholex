from django.contrib import admin
from persianmeme import models
from django.http import HttpResponse, HttpRequest
from django.core.serializers import serialize
from .functions import fake_deny_vote
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


def current_meme(obj: models.User):
    return obj.current_meme.name if obj.current_meme else None


@admin.display(description='Deny Votes Count')
def count_deny_votes(obj: models.Meme):
    return obj.deny_vote.count()


@admin.display(description='Accept Votes Count')
def count_accept_votes(obj: models.Meme):
    return obj.accept_vote.count()


@admin.display(description='Tags Count')
def count_tags(obj: models.Meme):
    return obj.tags.count()


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
class User(admin.ModelAdmin):
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
    actions = (unban_user, full_ban, ban_user, export_json)
    raw_id_fields = (
        'last_broadcast',
        'playlists',
        'current_playlist',
        'current_meme',
        'current_ad',
        'temp_meme_tags',
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
            'current_ad',
            'last_broadcast',
            'use_recent_memes',
            'report_violation_count'
        )}),
        ('Memes', {'fields': ('playlists',)}),
        ('Temporary Values', {'fields': ('temp_meme_name', 'temp_user_id', 'temp_meme_tags')})
    )
    inlines = (UsernameInline, RecentMemeInline)


@admin.register(models.Meme)
class Meme(admin.ModelAdmin):
    @admin.display(description='Accept Votes')
    def accept_vote(self, request: HttpRequest, queryset):
        result = [(target_meme, target_meme.accept()) for target_meme in queryset if target_meme.status == 'p']
        result_len = len(result)
        if result_len == 0:
            self.message_user(request, 'There is no need to accept these memes !')
        elif result_len == 1:
            self.message_user(request, f'{result[0][0]} meme has been accepted !')
        else:
            self.message_user(request, f'{result_len} memes have been accepted !')

    @admin.display(description='Deny Vote')
    def deny_vote(self, request: HttpRequest, queryset):
        result = [
            (target_meme, target_meme.delete_vote(), target_meme.deny())
            for target_meme in queryset if target_meme.status == 'p'
        ]
        result_len = len(result)
        if result_len == 0:
            self.message_user(request, 'There is no need to deny these memes !')
        else:
            queryset.delete()
            if result_len == 1:
                self.message_user(request, f'{result[0][0]} has been denied !')
            else:
                self.message_user(request, f'{result_len} memes have been denied !')

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
    list_display = (
        'id', 'name', 'sender', 'type', 'status', 'usage_count', count_deny_votes, count_accept_votes, count_tags
    )
    list_filter = ('status', 'visibility', 'reviewed', 'type', 'previous_status')
    search_fields = ('name', 'sender__chat_id', 'file_id', 'file_unique_id', 'id', 'sender__user_id', 'description')
    actions = (export_json, accept_vote, deny_vote, add_fake_deny_votes, recover_memes, ban_senders)
    list_per_page = 15
    readonly_fields = ('id', 'date')
    raw_id_fields = ('sender', 'voters', 'accept_vote', 'deny_vote', 'tags', 'assigned_admin')
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
            'assigned_admin',
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


@admin.register(models.Ad)
class Ad(admin.ModelAdmin):
    list_display = ('ad_id', 'chat_id', 'message_id')
    readonly_fields = ('ad_id',)
    search_fields = ('chat_id', 'message_id', 'seen__chat_id')
    list_filter = ('chat_id',)
    fieldsets = (('Information', {'fields': ('ad_id', 'chat_id', 'message_id', 'seen')}),)
    raw_id_fields = ('seen',)


@admin.register(models.Delete)
class Delete(admin.ModelAdmin):
    list_display = ('id', 'meme', 'user')
    readonly_fields = ('id',)
    search_fields = (
        'id', 'user__user_id', 'user__chat_id', 'meme__id', 'meme__file_id', 'meme__file_unique_id'
    )
    raw_id_fields = ('meme', 'user')
    fieldsets = (('Information', {'fields': ('id', 'meme', 'user')}),)


@admin.register(models.Broadcast)
class Broadcast(admin.ModelAdmin):
    list_display = ('id', 'message_id', 'sender', 'sent')
    list_filter = ('sent',)
    search_fields = ('id', 'message_id', 'sender__chat_id', 'sender__user_id')
    list_per_page = 15
    readonly_fields = ('id',)
    raw_id_fields = ('sender',)
    fieldsets = (('Information', {'fields': ('id', 'message_id', 'sender')}), ('Status', {'fields': ('sent',)}))


@admin.register(models.Playlist)
class Playlist(admin.ModelAdmin):
    list_display = ('id', 'name', count_voices, 'creator', 'date')
    date_hierarchy = 'date'
    list_filter = ('creator__rank', 'creator__status')
    search_fields = ('name', 'id', 'creator__user_id', 'creator__chat_id')
    list_per_page = 15
    readonly_fields = ('id', 'date')
    raw_id_fields = ('voices', 'creator')
    fieldsets = (('Information', {'fields': ('id', 'name', 'date', 'voices', 'creator')}),)


@admin.register(models.Message)
class Message(admin.ModelAdmin):
    list_display = ('id', 'sender', 'status')
    list_filter = ('status',)
    raw_id_fields = ('sender',)
    search_fields = ('id', 'sender__user_id', 'sender__user_id', 'sender__chat_id')
    list_per_page = 15
    readonly_fields = ('id',)
    fieldsets = (('Information', {'fields': ('id', 'sender')}), ('Status', {'fields': ('status',)}))


@admin.register(models.MemeTag)
class MemeTag(admin.ModelAdmin):
    list_display = ('tag',)
    search_fields = ('tag',)
    list_per_page = 30
    fieldsets = (('Information', {'fields': ('tag',)}),)


@admin.register(models.RecentMeme)
class RecentMeme(admin.ModelAdmin):
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
class Report(admin.ModelAdmin):
    list_display = ('meme', count_reporters, 'status')
    list_filter = ('status',)
    list_per_page = 20
    search_fields = (
        'reporters__user_id',
        'reporters__chat_id',
        'reporters__user',
        'meme__id',
        'meme__name',
        'meme__file_id',
        'meme__file_unique_id'
    )
    raw_id_fields = ('meme', 'reporters')
    fieldsets = (('Information', {'fields': ('meme', 'reporters')}), ('Status', {'fields': ('status',)}))


@admin.register(models.Username)
class Username(admin.ModelAdmin):
    list_display = ('id', 'user', 'username', 'creation_date')
    date_hierarchy = 'creation_date'
    search_fields = ('user__chat_id', 'user__user_id', 'username')
    list_per_page = 30
    raw_id_fields = ('user',)
    readonly_fields = ('id', 'creation_date')
    fieldsets = (('Information', {'fields': ('id', 'user', 'username', 'creation_date')}),)
