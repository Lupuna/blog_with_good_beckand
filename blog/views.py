from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
from . import models
from . import forms


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
            # форма успешно прошла валидацию
            cd = form.cleaned_data
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


def post_list(request):
    post_lists = models.Post.published.all()
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

    context = {'posts': posts}
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
    context = {
        'post': post,
        'comments': comments,
        'form': form
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
