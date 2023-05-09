from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator
from datetime import date
# Create your models here#.

class Author(models.Model):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField()
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'
class Post(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    content = models.TextField()
    date = models.DateTimeField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True)
    excerpt = models.CharField(max_length=200)
    tags = models.ManyToManyField('Tag', related_name='posts')

    def __str__(self):
        return self.title

class Tag(models.Model):
    caption = models.CharField(max_length=20)
    
    def __str__(self):
        return self.caption
    
class Comments(models.Model):
    name = models.CharField(max_length=100, validators=[MinLengthValidator(6)])
    email = models.EmailField()
    comment = models.TextField(validators=[MinLengthValidator(10)])
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    date = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f'{self.name} commented on "{self.post.title}", submitted {self.date.strftime("%c")}'

    class Meta:
        ordering = ('-date',)
