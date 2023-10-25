from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe
import markdown
from .. import models

register = template.Library()


@register.simple_tag
def total_posts():
    return models.Post.published.count()


@register.inclusion_tag('blog/post/includes/show_latest_post.html')
def show_latest_post(count=5):
    latest_posts = models.Post.published.order_by('-publish')[:count]
    return {'latest_posts': latest_posts}


@register.simple_tag
def get_most_commented_posts(count=5):
    max_comment = models.Post.published.annotate(total_comments=Count('comments')).order_by('-total_comments')[:count]
    return max_comment


@register.filter(name='markdown')
def markdown_format(text):
    # mark_safe помечает информацию как безопасная (т.е. переданный HTML код не будет экранироваться)
    return mark_safe(markdown.markdown(text))

# В этом файле хранятся кастомные фильтры и теги для django template language
