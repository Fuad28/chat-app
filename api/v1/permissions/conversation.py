from rest_framework import permissions

from api.models import Conversation, ConversationMembers, Message


class IsConversationMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: Conversation):
        return request.user in obj.members.all()
    

class IsConversationAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: Conversation):
        
        return ConversationMembers.objects.get(
            user= request.user, 
            conversation= obj).is_admin
    

class IsMessageOwnerorAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: Message):
        return (request.user == obj.sent_by) or ConversationMembers.objects.get(
            user= request.user, 
            conversation= obj.conversation
        ).is_admin