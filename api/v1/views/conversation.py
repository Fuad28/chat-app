from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action 
from rest_framework.response import Response

from api.models import Conversation, Message, ConversationMembers
from api.v1.permissions import IsConversationMember, IsConversationAdmin
from api.v1.serializers.conversation import (
	CreateConversationSerializer, ConversationSerializer, SimpleConversationSerializer,
	AddORemoveMemberConversationSerializer)


class ConversationViewSet(ModelViewSet):
	http_method_names= ["get", "post", "patch"]
	
	def get_serializer_class(self):
		if self.action == "create":
			return CreateConversationSerializer
		
		elif self.action == "retrieve":
			return ConversationSerializer
		
		elif self.action in ["add_member", "remove_member"]:
			return AddORemoveMemberConversationSerializer

		return SimpleConversationSerializer
	
	def get_permissions(self):
		if self.action in ["add_member", "remove_member"]:
			return [IsAuthenticated(), IsConversationMember(), IsConversationAdmin()]

		elif self.action == "list":
			return SimpleConversationSerializer

		return [IsAuthenticated()]
		

	def get_queryset(self):
		return Conversation.objects.filter(members= self.request.user)
	
	def get_object(self) -> Conversation:
		return super().get_object()
	

	@action(detail=True, methods=["post"])
	def join(self, request):
		conversation = self.get_object()
		
		if not conversation.is_private:
			conversation.members.add(self.request.user)
			return Response(status= status.HTTP_204_NO_CONTENT)
		
		return Response({
			"detail": "You can't join a private conversation."
			},
			status= status.HTTP_403_FORBIDDEN)
	

	@action(detail=True, methods=["post"])
	def add_member(self, request):
		conversation = self.get_object()
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception= True)
		user= serializer.data.get("user")

		if not conversation.is_private:
			conversation.members.add(user)
			return Response(status= status.HTTP_204_NO_CONTENT)
		
		return Response({
				"detail": "You can't join a provate conversation."},
				status= status.HTTP_403_FORBIDDEN)
	

	@action(detail=True, methods=["post"])
	def remove_member(self, request):
		conversation = self.get_object()
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception= True)
		user= serializer.data.get("user")

		if request.user != conversation.created_by:
			return Response({
				"detail": "You can't remove group creator."
				},
			status= status.HTTP_403_FORBIDDEN)

		
		conversation.members.remove(user)
		return Response(status= status.HTTP_204_NO_CONTENT)
	

	@action(detail=True, methods=["post"])
	def make_admin(self, request):
		conversation = self.get_object()
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception= True)
		user= serializer.data.get("user")

		if request.user not in conversation.members:
			return Response({
				"detail": "User is not in conversation."
				},
			status= status.HTTP_400_BAD_REQUEST)

		
		member= ConversationMembers.objects.get(user= user, conversation= conversation)
		member.is_admin= True
		member.save() #TODO: should broadcast this, should broadcaset add and remove also

		return Response(status= status.HTTP_204_NO_CONTENT)
	
