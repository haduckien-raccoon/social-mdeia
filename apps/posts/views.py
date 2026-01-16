from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .services import *


def feed_view(request):
    """A simple view to demonstrate fetching and displaying posts."""
    posts = Post.objects.filter(is_deleted=False).order_by('-created_at')
    return render(request, 'posts/feed.html', {'posts': posts})

def create_post_view(request):
    """A view to handle post creation."""
    if request.method == 'POST':
        content = request.POST.get('content')
        privacy = request.POST.get('privacy', PostPrivacy.PUBLIC)
        images = request.FILES.getlist('images')
        files = request.FILES.getlist('files')
        tagged_user_ids = request.POST.getlist('tagged_users')
        hashtags = request.POST.getlist('hashtags')

        tagged_users = User.objects.filter(id__in=tagged_user_ids)

        PostService.create_post(
            user=request.user,
            content=content,
            privacy=privacy,
            images=images,
            files=files,
            tagged_users=tagged_users,
            hashtags=hashtags
        )
        return redirect('posts:feed')

    return render(request, 'posts/create_post.html')

def post_detail_view(request, post_id):
    """A view to display a single post's details."""
    post = get_object_or_404(Post, id=post_id, is_deleted=False)
    return render(request, 'posts/post_detail.html', {'post': post})

def delete_post_view(request, post_id):
    """A view to handle post deletion."""
    post = get_object_or_404(Post, id=post_id, author=request.user)
    post.soft_delete()
    return redirect('posts:feed')

def create_commanet_view(request, post_id):
    """A view to handle comment creation."""
    post = get_object_or_404(Post, id=post_id, is_deleted=False)

    if request.method == 'POST':
        content = request.POST.get('content')
        CommentService.create_comment(
            user=request.user,
            post=post,
            content=content
        )
        return redirect('posts:post_detail', post_id=post.id)

    return render(request, 'posts/create_comment.html', {'post': post})

def toggle_reaction_view(request, post_id, reaction_type):
    """A view to handle adding/removing reactions to a post."""
    post = get_object_or_404(Post, id=post_id, is_deleted=False)

    ReactionService.toggle_reaction(
        user=request.user,
        post=post,
        target_type='post',
        target_id=post.id,
        reaction_type=reaction_type
    )
    return redirect('posts:post_detail', post_id=post.id)

