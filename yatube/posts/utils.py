from django.core.paginator import Paginator

from .constants import NUMBER_OF_POSTS_PER_PAGE


def paginator(request, obj_list):
    paginator = Paginator(obj_list, NUMBER_OF_POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
