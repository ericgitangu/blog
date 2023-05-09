from django.contrib import admin
from .models import Author, Post, Tag, Comments
# Register your models here.

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'author')
    list_filter = ('date', 'author', 'tags')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    date_hierarchy = 'date'
    ordering = ('date',)

class CommentsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'post', 'date')
    list_filter = ('name', 'date', 'post')
    search_fields = ('name', 'email', 'comment', 'date')
    date_hierarchy = 'date'
    ordering = ('date',)

admin.site.register(Author)
admin.site.register(Post, PostAdmin)
admin.site.register(Tag)
admin.site.register(Comments, CommentsAdmin)
