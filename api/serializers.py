from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Group, Event, UserProfile, Members, Comments, Prediction
from rest_framework.authtoken.models import Token
from django.db.models import Sum
from django.utils import timezone
class changePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id','image','is_premium', 'bio')
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    class Meta:
        model = User
        fields = ('id', 'username','email', 'password','profile')
        extra_kwargs = {'password':{'write_only': True,'required': False}}

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, **profile_data)
        Token.objects.create(user=user)
        return user

class PredictionSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)
    class Meta:
        model = Prediction
        fields = ('id', 'user', 'event', 'score1', 'score2', 'points')
class EventSerializer(serializers.ModelSerializer):

    class Meta:
        model = Event
        fields = ('id', 'team1', 'team2', 'time', 'group')

class EventFullSerializer(serializers.ModelSerializer):


    predictions = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    class Meta:
        model = Event
        fields = ('id', 'team1', 'team2', 'time', 'score1', 'score2', 'group', 'predictions', 'is_admin')

    def get_predictions(self, obj):
        if obj.time < timezone.now():
            predictions = Prediction.objects.filter(event=obj)
        else:
            user = self.context['request'].user
            predictions = Prediction.objects.filter(event=obj, user=user)

        serializer = PredictionSerializer(predictions, many=True)
        return serializer.data

    def get_is_admin(self, obj):
        try:
            user = self.context['request'].user
            print(user)
            member = Members.objects.get(group=obj.group, user=user)
            return member.admin
        except:
            return None



class MembersSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)

    class Meta:
        model = Members
        fields = ('user', 'group', 'admin')
class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('id', 'name', 'location', 'desc', 'num_members')

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = ('user', 'group', 'description', 'time')

class GroupFullSerializer(serializers.ModelSerializer):
    events = EventSerializer(many=True)
    members = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    class Meta:
        model = Group
        fields = ('id', 'name', 'location', 'desc', 'events', 'members', 'comments')


    def get_comments(self, obj):
        comments = Comments.objects.filter(group=obj).order_by('-time')
        serializer = CommentSerializer(comments, many=True)
        return serializer.data

    def get_members(self, obj):
        people_points = []

        members = obj.members.all()

        for member in members:
            points = Prediction.objects.filter(event__group=obj, user=member.user.id).aggregate(pts=Sum('points'))
            member_serialized = MembersSerializer(member, many=False)
            member_data = member_serialized.data
            member_data['points'] = points['pts'] or 0
            people_points.append(member_data)

        return people_points

