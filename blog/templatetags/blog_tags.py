from django import template
from .. import models

register = template.Library()


@register.simple_tag
def total_posts():
    return models.Post.published.count()


@register.inclusion_tag('blog/post/includes/latests_posts.html')
def show_latest_post(count=5):
    latest_posts = models.Post.order_by('-publish')[:count]
    return {'latest_posts': latest_posts}

# В этом файле хранятся кастомные фильтры и теги для django template language
