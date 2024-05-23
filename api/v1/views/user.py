from rest_framework.response import Response
from rest_framework import status

from djoser.views import UserViewSet as DjoserUserViewset

class UserViewSet(DjoserUserViewset):

	def perform_update(self, serializer):
		"""Djoser sends notifications to users upon every profile update. We want to avoid that"""
		
		super().perform_update(serializer)

	
	def create(self, request, *args, **kwargs):
		""" Cast emails into all lower case. """
		
		if "email" in request.data:
			request.data["email"]= request.data["email"].lower()
		return super().create(request, *args, **kwargs)

	
	def destroy(self, request, *args, **kwargs):
		"""Djoser tries to log user out upon account deletion. This throws an error when using JWTs"""
		
		instance = self.get_object()
		serializer = self.get_serializer(instance, data=request.data)
		serializer.is_valid(raise_exception=True)
		
		self.perform_destroy(instance)
		return Response(status=status.HTTP_204_NO_CONTENT)
