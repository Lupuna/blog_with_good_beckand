from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from . import models, forms


class PostListView(ListView):
    """
    Альтернативное представление списка постов
    """
    queryset = models.Post.published.all()
    context_object_name = 'posts'
    paginate_by = 2
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    post = get_object_or_404(models.Post, id=post_id, status=models.Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        # Форма была передана на обработку
        form = forms.EmailPostForm(request.POST)
        if form.is_valid():
            # форма успешно прошла валидацию, поэтому мы извлекаем полученные данные
            cd = form.cleaned_data()
            # отправить электронное письмо
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f'{cd["name"]} recommends you read {post.title}'
            message = f'Read {post.title} at {post_url}\n\n {cd["name"]}\'s comments: {cd["comments"]}'
            send_mail(subject, message, 'terragod427@gmil.com', [cd['to']])
            sent = True
    else:
        form = forms.EmailPostForm()
    context = {
        'post': post,
        'form': form,
        'sent': sent
    }
    return render(request, 'blog/post/share.html', context)


def post_list(request, tag_slug=None):
    post_lists = models.Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_lists = post_lists.filter(tags__in=[tag])
    # Постраничная разбивка с 2-мя постами на страницу
    paginator = Paginator(post_lists, 2)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        # если page_number находиться вне диапазона, то выдать последнюю страницу
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        # если page_number не целое число, то выдать первую страницу
        posts = paginator.page(1)

    context = {
        'posts': posts,
        'tag': tag,
    }
    return render(request, 'blog/post/list.html', context)


def post_ditail(request, year, month, day, post):
    # try:
    #     post = models.Post.published.get(id=id)
    # except models.Post.DoesNotExist:
    #     raise Http404('No Post found')
    post = get_object_or_404(models.Post, status=models.Post.Status.PUBLISHED, slug=post, publish__year=year,
                             publish__month=month, publish__day=day)
    comments = post.comments.filter(active=True)
    form = forms.CommentForm()
    post_list_ids = post.tags.values_list('id', flat=True)
    similar_post = models.Post.published.filter(tags__in=post_list_ids).exclude(id=post.id)
    similar_post = similar_post.annotate(same_tags=Count('tags')).order_by('-same_tags', 'publish')[:4]
    context = {
        'post': post,
        'comments': comments,
        'form': form,
        'similar_posts': similar_post,
    }
    return render(request, 'blog/post/detail.html', context)


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(models.Post, id=post_id, status=models.Post.Status.PUBLISHED)
    comment = None
    # создается экземпляр формы
    form = forms.CommentForm(data=request.POST)
    if form.is_valid():
        # Создать объект класса Comment, не сохраняя его в базе данных
        comment = form.save(commit=False)
        # Назначить пост комментарию
        comment.post = post
        # Сохранить комментарий в базе данных
        comment.save()
    context = {
        'post': post,
        'form': form,
        'comment': comment
    }
    return render(request, 'blog/post/comment.html', context)


def post_search(request):
    form = forms.SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = forms.SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A')+SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            # ranck__gte=0.3 фильтрует только те записи, у которых процент совпадения 0.3 и выше
            # подробнее в практике на основе тестирования 4.0 186 стр.
            results = models.Post.published.annotate(search=search_vector, ranck=SearchRank(search_vector, search_query))\
                .filter(ranck__gte=0.3).order_by('-rank')
    context = {
        'form': form,
        'query': query,
        'results': results
    }
    return render(request, 'blog/post/search.html', context)
