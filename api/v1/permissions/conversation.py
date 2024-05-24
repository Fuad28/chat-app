from rest_framework import permissions

from api.models import Conversation, ConversationMembers


class IsConversationMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: Conversation):
        return request.user in obj.members.all()
    

class IsConversationAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: Conversation):
        return ConversationMembers.objects.get(
            user= request.user, 
            conversation= obj).is_admin