from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.response import Response
from math import ceil


class DynamicPagination(LimitOffsetPagination):
    """
    Enhanced limit-offset based pagination.
    Provides additional metadata about pagination state.
    
    Query parameters:
    - limit: Number of items to return per page
    - offset: Starting position
    """
    default_limit = 10
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100
    
    def get_paginated_response(self, data):
        total_count = self.count
        limit = self.limit
        
        return Response({
            'status': 'success',
            'count': total_count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'total_pages': ceil(total_count / limit) if limit else 1,
            'current_offset': self.offset,
            'limit': limit,
            'results': data
        })


class StaticPagination(PageNumberPagination):
    """
    Enhanced page number based pagination.
    Provides additional metadata about pagination state.
    
    Query parameters:
    - page: Page number
    - page_size: Number of items per page
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        return Response({
            'status': 'success',
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'page_size': self.get_page_size(self.request),
            'results': data
        })