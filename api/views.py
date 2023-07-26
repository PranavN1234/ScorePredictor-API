import pytz
from django.shortcuts import render
from rest_framework import viewsets, status
from .models import Group, Event, UserProfile, Members, Comments, Prediction
from django.contrib.auth.models import User
from .serializers import GroupSerializer, EventSerializer, GroupFullSerializer, UserSerializer, UserProfileSerializer, changePasswordSerializer, MembersSerializer, CommentSerializer, EventFullSerializer, PredictionSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from datetime import datetime
# Create your views here.


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (AllowAny,)


    @action(methods=['PUT'], detail=True, serializer_class=changePasswordSerializer, permission_classes=[IsAuthenticated])
    def changePassword(self, request, pk):
        user = User.objects.get(pk=pk)
        serializer = changePasswordSerializer(data=request.data)

        if serializer.is_valid():
            if not user.check_password(serializer.data.get('old_password')):
                return Response({'message': 'Wrong old Password', 'error': 'wrong'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.data.get('new_password'))
            user.save()

            return Response({'message':'Password Successfully updated','error': 'right'}, status=status.HTTP_200_OK)





class ProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    authentication_classes = (TokenAuthentication,)

class GroupViewset(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = GroupFullSerializer(instance, many=False, context={'request': request})
        return Response(serializer.data)

class EventViewset(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = EventFullSerializer(instance, many=False, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['PUT'])
    def post_result(self, request, pk):
        event = self.get_object()
        if 'score1' in request.data and 'score2' in request.data and event.time < datetime.now(pytz.UTC):

            event.score1 = request.data['score1']
            event.score2 = request.data['score2']
            event.save()
            self.calculate_score()
            serializer = EventFullSerializer(event, context={'request':request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            response = {"message":"Wrong Params"}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def calculate_score(self):
        event = self.get_object()
        predictions = event.predictions.all()
        for prediction in predictions:
            points = 0

            if prediction.score1 == event.score1 and prediction.score2 == event.score2:
                points = 5

            else:
                prediction_score = prediction.score1 - prediction.score2
                event_score = event.score1 - event.score2

                if (prediction_score> 0 and event_score > 0) or (prediction_score<0 and event_score<0) or (prediction_score==0 and event_score==0) :
                    points = 2


            prediction.points = points
            prediction.save()


class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super(CustomObtainAuthToken, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        user = User.objects.get(id=token.user_id)
        userSerializer = UserSerializer(user, many=False)
        return Response({'token':token.key, 'user': userSerializer.data})

class CommentViewset(viewsets.ModelViewSet):
    queryset = Comments.objects.all()
    serializer_class = CommentSerializer


class MemberViewset(viewsets.ModelViewSet):
    queryset = Members.objects.all()
    serializer_class = MembersSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @action(methods=['POST'], detail=False)
    def join(self, request):
        if 'group' in request.data and 'user' in request.data:

            try:
                group = Group.objects.get(id=request.data['group'])
                user = User.objects.get(id=request.data['user'])
                member = Members.objects.create(group=group, user=user, admin=False)
                serializer = MembersSerializer(member, many=False)

                response = {'message': 'Joined Group', 'results': serializer.data}
                return Response(response, status=status.HTTP_200_OK)
            except:
                response = {'message': 'Unable to join'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)




        else:
            response = {'message': 'Wrong params'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=False)
    def leave(self, request):
        if 'group' in request.data and 'user' in request.data:

            try:
                group = Group.objects.get(id=request.data['group'])
                user = User.objects.get(id=request.data['user'])
                member = Members.objects.get(group=group, user=user)
                member.delete()

                response = {'message': 'Left Group'}
                return Response(response, status=status.HTTP_200_OK)

            except:
                response = {'message': 'Unable to Leave'}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)




        else:
            response = {'message': 'Wrong params'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PredictionViewset(viewsets.ModelViewSet):
    queryset = Prediction.objects.all()
    serializer_class = PredictionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        response = {'message': 'Method Not Allowed'}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        response = {'message': 'Method Not Allowed'}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)



    @action(detail=False, methods=['POST'], url_path='do_prediction')
    def do_prediction(self, request):
        if 'event' in request.data and 'score1' in request.data and 'score2' in request.data:
            event_id = request.data['event']
            event = Event.objects.get(id=event_id)

        #     check if user in group
            in_group = self.CheckIfuser(event, request.user)



            if event.time > datetime.now(pytz.UTC) and in_group:
                score1 = request.data['score1']
                score2 = request.data['score2']

                try:
                    prediction = Prediction.objects.get(event=event_id, user=request.user.id)
                    prediction.score1 = score1
                    prediction.score2 = score2
                    prediction.save()
                    serializer = PredictionSerializer(prediction, many=False)
                    response = {'message': 'PREDICTION UPDATED!!', 'new': False, 'result': serializer.data}
                    return Response(response, status=status.HTTP_200_OK)

                except:
                    prediction = Prediction.objects.create(event=event, user=request.user, score1=score1, score2=score2)
                    serializer = PredictionSerializer(prediction, many=False)
                    response = {'message': 'PREDICTION ADDED!!', 'new': True, 'result': serializer.data}
                    return Response(response, status=status.HTTP_200_OK)




            else:
                response = {'message': "You can't place bet"}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        else:
            response = {'message': 'Wrong params'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


    def CheckIfuser(self, event, user):

        try:
            return Members.objects.get(user=user, group=event.group)
        except:
            return False