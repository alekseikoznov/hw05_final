from yatube.settings import NUMBER_OF_POSTS
from django.core.paginator import Paginator


def paginator(request, obj):
    paginator = Paginator(obj, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
