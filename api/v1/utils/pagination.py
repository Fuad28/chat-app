from rest_framework.pagination import LimitOffsetPagination

class CustomLimitOffsetPagination(LimitOffsetPagination):
	"""
	There's a need for a custom pagination class due to our data storage logic. 
	We only need the paginator class to construct a response. The task of trimming
	data has been done in the CachedMessageQuerySet class.
	"""
	
	def paginate_queryset(self, queryset, request, view=None):
		self.request = request
		self.limit = self.get_limit(request)
		if self.limit is None:
			return None

		self.count = self.get_count(queryset)
		self.offset = self.get_offset(request)
		if self.count > self.limit and self.template is not None:
			self.display_page_controls = True

		if self.count == 0 or self.offset > self.count:
			return []
		
		return queryset

