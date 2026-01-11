"""
Seed blog posts from LinkedIn data export.

LinkedIn export contains a CSV file with your posts.
Export from: LinkedIn Settings > Data Privacy > Get a copy of your data > Posts

Usage:
    python manage.py seed_linkedin --file /path/to/Shares.csv
"""
import csv
import re
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from portfolio.models import Post, Author, Tag


class Command(BaseCommand):
    help = 'Seed blog posts from LinkedIn data export (Shares.csv)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to LinkedIn Shares.csv export file'
        )
        parser.add_argument(
            '--author-first',
            type=str,
            default='Eric',
            help='Author first name'
        )
        parser.add_argument(
            '--author-last',
            type=str,
            default='Gitangu',
            help='Author last name'
        )
        parser.add_argument(
            '--author-email',
            type=str,
            default='developer.ericgitangu@gmail.com',
            help='Author email'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of posts to import'
        )

    def extract_hashtags(self, text):
        """Extract hashtags from post content."""
        hashtags = re.findall(r'#(\w+)', text)
        return list(set(hashtags))[:5]  # Limit to 5 tags per post

    def generate_title(self, content, max_length=100):
        """Generate a title from the first line or sentence of content."""
        # Remove URLs
        content = re.sub(r'http\S+', '', content)
        # Get first line or first sentence
        first_line = content.split('\n')[0].strip()
        if len(first_line) > max_length:
            first_line = first_line[:max_length-3] + '...'
        return first_line or 'LinkedIn Post'

    def generate_excerpt(self, content, max_length=200):
        """Generate an excerpt from content."""
        # Remove URLs and hashtags for cleaner excerpt
        clean = re.sub(r'http\S+', '', content)
        clean = re.sub(r'#\w+', '', clean)
        clean = ' '.join(clean.split())  # Normalize whitespace
        if len(clean) > max_length:
            clean = clean[:max_length-3] + '...'
        return clean or 'Read more...'

    def parse_linkedin_date(self, date_str):
        """Parse LinkedIn date format."""
        try:
            # LinkedIn export format: "2024-07-15 10:30:00 UTC"
            dt = datetime.strptime(date_str.replace(' UTC', ''), '%Y-%m-%d %H:%M:%S')
            return timezone.make_aware(dt, timezone.utc)
        except ValueError:
            try:
                # Try alternative format
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return timezone.make_aware(dt, timezone.utc)
            except ValueError:
                return timezone.now()

    def handle(self, *args, **options):
        file_path = options['file']
        limit = options['limit']

        # Get or create author
        author, created = Author.objects.get_or_create(
            email=options['author_email'],
            defaults={
                'first_name': options['author_first'],
                'last_name': options['author_last'],
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created author: {author}'))
        else:
            self.stdout.write(f'Using existing author: {author}')

        # Read LinkedIn export CSV
        posts_created = 0
        posts_skipped = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # LinkedIn export has different CSV structures, try to detect
                reader = csv.DictReader(f)

                for row in reader:
                    if posts_created >= limit:
                        break

                    # LinkedIn Shares.csv typically has: Date, ShareCommentary, SharedUrl, MediaUrl
                    content = row.get('ShareCommentary', row.get('Content', row.get('Text', '')))
                    date_str = row.get('Date', row.get('Created', ''))
                    shared_url = row.get('SharedUrl', row.get('URL', ''))

                    if not content or len(content.strip()) < 50:
                        posts_skipped += 1
                        continue

                    # Generate post data
                    title = self.generate_title(content)
                    slug_base = slugify(title)[:80]

                    # Ensure unique slug
                    slug = slug_base
                    counter = 1
                    while Post.objects.filter(slug=slug).exists():
                        slug = f'{slug_base}-{counter}'
                        counter += 1

                    # Add shared URL to content if present
                    if shared_url:
                        content = f'{content}\n\nOriginally shared: {shared_url}'

                    # Create post
                    post = Post.objects.create(
                        title=title,
                        slug=slug,
                        content=content,
                        date=self.parse_linkedin_date(date_str),
                        excerpt=self.generate_excerpt(content),
                        author=author,
                    )

                    # Extract and add tags
                    hashtags = self.extract_hashtags(content)
                    for tag_name in hashtags:
                        tag, _ = Tag.objects.get_or_create(
                            caption=tag_name.lower()[:20]
                        )
                        post.tags.add(tag)

                    posts_created += 1
                    self.stdout.write(f'Created post: {title[:50]}...')

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading file: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created {posts_created} posts, skipped {posts_skipped} (too short or empty)'
        ))
        self.stdout.write(f'Total posts in database: {Post.objects.count()}')
