from rest_framework.pagination import PageNumberPagination


class PaginacionEstandar(PageNumberPagination):
    page_size = 50
    page_size_query_param = "tamano"
    max_page_size = 200
