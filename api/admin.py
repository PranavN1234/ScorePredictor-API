from django.contrib import admin
from .models import Group, Event, UserProfile, Members, Comments, Prediction
# Register your models here.

@admin.register(UserProfile)
class UserprofileAdmin(admin.ModelAdmin):
    fields = ('user', 'image','is_premium', 'bio')
    list_display = ('id','user', 'image', 'is_premium', 'bio')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    fields = ('name', 'location', 'desc')
    list_display = ('id', 'name', 'location', 'desc')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    fields = ('team1', 'team2', 'time', 'score1', 'score2', 'group')
    list_display = ('team1', 'team2', 'time', 'score1', 'score2', 'group')

@admin.register(Members)
class MemberAdmin(admin.ModelAdmin):
    fields = ('user', 'group', 'admin')
    list_display = ('user', 'group', 'admin')

@admin.register(Comments)
class CommentAdmin(admin.ModelAdmin):
    fields = ('user', 'group', 'description')
    list_display = ('id','user', 'group', 'description', 'time')

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    fields = ('user', 'event', 'score1', 'score2')
    list_display = ('id', 'user', 'event', 'score1', 'score2')
