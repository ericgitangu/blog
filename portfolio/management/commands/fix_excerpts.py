"""Regenerate excerpts from content for all posts."""
from django.core.management.base import BaseCommand
from portfolio.models import Post


class Command(BaseCommand):
    help = 'Regenerate excerpts from content for all posts'

    def handle(self, *args, **options):
        updated = 0
        for post in Post.objects.all():
            excerpt = post.content.replace('\n', ' ').replace('  ', ' ').strip()
            if len(excerpt) > 197:
                excerpt = excerpt[:197] + '...'

            if post.excerpt != excerpt:
                self.stdout.write(f'Fixing: {post.title}')
                self.stdout.write(f'  OLD: {post.excerpt[:80]}')
                self.stdout.write(f'  NEW: {excerpt[:80]}')
                post.excerpt = excerpt
                post.save(update_fields=['excerpt'])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Fixed {updated} posts'))
