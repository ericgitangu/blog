from django.shortcuts import render, get_object_or_404
from datetime import date
from .models import Post, Tag
from django.views.generic import ListView, View
from .forms import CommentForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q, Count

# all_posts = [
#     {
#         "slug": "follow-on-linkedin",
#         "image": "linkedin.png",
#         "author": "Eric Gitangu",
#         "date": date(2022, 12, 21),
#         "title": "Follow me on LinkedIn!",
#         "excerpt": "Follow me on LinkedIn where I share my latest posts and projects.",
#         "content": """
#           Follow me on <a href="https://linkedin.com/in/ericgitangu">LinkedIn!</a> where I talk about #blockchaindevelopment, #fullstackdevelopment, #jamstack, #cloudcomputing, and #mobileappdevelopment. Let me know if you have any suggestions on what to share! ✒️ #share #linkedin
#         """
#     },
#     {
#         "slug": "programming-is-fun",
#         "image": "coding.jpg",
#         "author": "Eric Gitangu",
#         "date": date(2023, 1, 10),
#         "title": "Programming Is Fun!",
#         "excerpt": "Learning new tech stacks is fun right? Yep - that's what I did one Friday night, exploring the exciting features introduced in NextJS13...",
#         "content": """
#           Thought I'd spend my Friday night coining my alias Deveric by christening it with my official portfolio Full Stack site, done with the frontend more stuff coming for the backend
#           <a href="https://lnkd.in/djTV-Art">NextJS13 porfolio</a>
#           #frontend #backend #nextjs #typescript #seo #vercel
#         """
#     },
#     {
#         "slug": "ethical-ai-concerns",
#         "image": "ai.jpg",
#         "author": "Eric Gitangu",
#         "date": date(2023, 1, 5),
#         "title": "Is the AI race ethical?",
#         "excerpt": "Technology is amazing! But is the ongoing AI race amongst the tech giants ethical?",
#         "content": """
#           With several tech giants embattled in an <a href="https://dpmd.ai/alphacode-science-li">#ai</a> should this be a concern?
#           coupled with the diversity impresentation shouldn't we be concerned about the potential pitfalls of this powerful technology?,
#            it could be the tipping point... my 2ç 🤔
#         """
#     }
# ]

# def home(request):
#     latest_posts = Post.objects.all().order_by('-date')[:3]
#     return render(request, 'portfolio/home.html', {
#         'posts': latest_posts
#     })
class home(ListView):
    template_name = 'portfolio/home.html'
    model = Post
    ordering = ['-date']
    context_object_name = 'posts'
    paginate_by = 3

    ''' You can use this method to override the default queryset or just paginate, performance gains?'''
    # def get_queryset(self):
    #     query_set = super().get_queryset()
    #     set = query_set[:3]
    #     return set

# def posts(request):
#     all_posts = Post.objects.all().order_by('-date')
#     return render(request, 'portfolio/posts.html', {
#         'posts': all_posts
#     })

class posts(ListView):
    template_name = 'portfolio/posts.html'
    model = Post
    ordering = ['-date']
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()

        # Search functionality
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query)
            )

        # Tag filtering
        tag_slug = self.request.GET.get('tag', '').strip()
        if tag_slug:
            queryset = queryset.filter(tags__caption__iexact=tag_slug)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all tags with post counts
        context['tags'] = Tag.objects.annotate(
            post_count=Count('posts')
        ).filter(post_count__gt=0).order_by('-post_count')

        # Total post count
        context['total_posts'] = Post.objects.count()

        # Current filters
        context['search_query'] = self.request.GET.get('q', '')
        context['active_tag'] = self.request.GET.get('tag', '')

        # Filtered count
        context['filtered_count'] = self.get_queryset().count()

        return context

# def post_detail(request, slug):
#     identified_post = get_object_or_404(Post, slug=slug)
#     return render(request, 'portfolio/post_details.html', {
#         'post': identified_post,
#         'post_tags': identified_post.tags.all()
#     })

class post_detail(View):
    template_name = 'portfolio/post_details.html'
    model = Post
    context_object_name = 'post'
    ordering = ['-date']

    def isSavedForLater(self, request, post_id):
        stored_posts = request.session.get('stored_posts', [])
        if stored_posts is not None:
            is_saved = post_id in stored_posts
        else:
            is_saved = False
        return is_saved

    def get(self, request, slug):
        post = get_object_or_404(Post, slug=slug)        
        context = { 'post': post, 'post_tags': post.tags.all(), 'comment_form': CommentForm(), 'comments': post.comments.all(), 'saved_for_later': self.isSavedForLater(request, post.id) }
        return render(request, 'portfolio/post_details.html', context)
    
    def post(self, request, slug):
        post = get_object_or_404(Post, slug=slug)
        context = { 'post': post, 'post_tags': post.tags.all(), 'comment_form': CommentForm(), 'comments': post.comments.all(), 'saved_for_later': self.isSavedForLater(request, post.id) }
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return HttpResponseRedirect(reverse("post_detail", args=[slug]))
        context = { 'post': post, 'post_tags': post.tags.all(), 'comment_form': form }
        return render(request, self.template_name, context)

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['post_tags'] = self.object.tags.all()
    #     context['comment_form'] = CommentForm()
    #     return context
class Saved(View):
    def get(self, request):
        context = {}
        stored_posts = request.session.get("stored_posts")
        if stored_posts is None:
            context["posts"] = []
            context["has_posts"] = False
        else:
            posts = Post.objects.filter(id__in=stored_posts)
            context["posts"] = posts
            context["has_posts"] = True
        return render(request, "portfolio/stored_post.html", context=context)

    def post(self, request):
        stored_posts = request.session.get("stored_posts")
        if stored_posts is None:
            stored_posts = []

        post_id = int(request.POST.get('post_id'))
        
        if post_id not in stored_posts:
            stored_posts.append(post_id)
        else:
            stored_posts.remove(post_id)

        request.session['stored_posts'] = stored_posts

        return HttpResponseRedirect('/')
