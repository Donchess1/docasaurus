from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from utils.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "size"
    max_page_size = 25

    def get_paginated_response(self, data):
        return Response(
            success=True,
            message=self.message if self.message else "Results retrieved successfully",
            status_code=status.HTTP_200_OK,
            data=data,
            meta={
                "current_page": self.page.number,
                "total_pages": self.page.paginator.num_pages,
                "page_size": self.page.paginator.per_page,
                "total_results": self.page.paginator.count,
            },
        )
