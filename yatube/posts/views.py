import shutil
import tempfile

from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group', 'author')
    page_obj = paginator(request, post_list)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = paginator(request, posts)
    template = 'posts/group_list.html'
    context = {'group': group, 'page_obj': page_obj}
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('author')
    posts_count = author.posts.select_related('author').count()
    page_obj = paginator(request, posts)
    template = 'posts/profile.html'
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(
                    user=request.user,
                    author=author).exists():
            following = True 
    context = {
        'author': author,
        'page_obj': page_obj,
        'posts_count': posts_count,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    form = CommentForm(request.POST or None)
    posts = get_object_or_404(Post, id=post_id)
    posts_count = posts.author.posts.select_related('author').count()
    template = 'posts/post_detail.html'
    comments = posts.comments.all()
    context = {
        'posts': posts,
        'posts_count': posts_count,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    template = 'posts/create_post.html'
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, template, {'form': form})


def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    user = request.user
    author = post.author
    template = 'posts/create_post.html'
    if author != user:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(
        request,
        template,
        {'form': form, 'post': post, 'is_edit': True})

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id) 

@login_required
def follow_index(request):
    username = request.user.username
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(request, post_list)
    context = {'page_obj': page_obj, 'username': username}
    return render(request, 'posts/follow.html', context)

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(
                    user=request.user,
                    author=author).exists()
    if author != request.user and not follow:
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username)

@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(
                user=request.user,
                author=author)
    follow.delete()
    return redirect('posts:profile', username)