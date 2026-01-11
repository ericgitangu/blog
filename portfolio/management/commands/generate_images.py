"""
Generate AI images for posts using DALL-E 3.

Creates unique, high-quality images based on post titles and tags.
Images are saved to MEDIA_ROOT/posts/

Usage:
    python manage.py generate_images
    python manage.py generate_images --overwrite  # Regenerate all

Requires OPENAI_API_KEY environment variable.
"""
import os
import requests
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from portfolio.models import Post

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


class Command(BaseCommand):
    help = 'Generate AI images for posts using DALL-E 3'

    # Style keywords based on tags
    STYLE_HINTS = {
        'rust': 'rust-colored, industrial, metallic gears',
        'python': 'blue and yellow, snake motif, clean code',
        'java': 'coffee themed, orange and brown, enterprise',
        'javascript': 'yellow and black, dynamic, web nodes',
        'react': 'blue atoms, component blocks, modern UI',
        'blockchain': 'golden chains, distributed nodes, crypto',
        'kubernetes': 'blue containers, orchestration, cloud pods',
        'aws': 'orange cloud, infrastructure, scalable',
        'django': 'green, web framework, python elegant',
        'go': 'cyan gopher, concurrent, fast',
        'android': 'green robot, mobile, apps',
        'ai': 'neural networks, purple gradients, futuristic',
        'security': 'red shields, locks, cyber protection',
        'career': 'professional, blue suit, growth chart',
        'education': 'books, graduation, academic green',
        'project': 'blueprints, building blocks, orange',
        'certifications': 'badges, certificates, achievements',
        'skills': 'toolbox, expertise icons, teal',
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Regenerate images even for posts that have one'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show prompts without generating images'
        )

    def get_style_hint(self, post):
        """Get style hints based on post tags."""
        tags = [t.caption.lower() for t in post.tags.all()]
        hints = []

        for tag in tags:
            for key, hint in self.STYLE_HINTS.items():
                if key in tag:
                    hints.append(hint)
                    break

        return ', '.join(hints[:2]) if hints else 'modern tech, professional'

    def create_prompt(self, post):
        """Create a DALL-E prompt for the post."""
        title = post.title[:100]
        style_hint = self.get_style_hint(post)

        prompt = f"""Create a modern, professional blog header image for an article titled "{title}".

Style: Abstract, minimalist tech illustration with {style_hint}.
Requirements:
- Clean, modern design suitable for a tech blog
- No text or letters in the image
- Soft gradients and geometric shapes
- Professional color palette
- 16:9 aspect ratio composition
- Suitable as a blog post thumbnail"""

        return prompt

    def generate_with_dalle(self, client, prompt):
        """Generate image using DALL-E 3."""
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",  # Closest to 16:9
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url

        # Download the image
        img_response = requests.get(image_url)
        img_response.raise_for_status()

        return img_response.content

    def resize_image(self, image_data, target_size=(800, 400)):
        """Resize image to target dimensions."""
        if not HAS_PILLOW:
            return image_data

        img = Image.open(BytesIO(image_data))
        img = img.resize(target_size, Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        return buffer.read()

    def handle(self, *args, **options):
        api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key:
            self.stdout.write(self.style.ERROR(
                'OPENAI_API_KEY environment variable is required.\n'
                'Set it with: fly secrets set OPENAI_API_KEY="sk-..." --app deveric-blog'
            ))
            return

        if not HAS_OPENAI:
            self.stdout.write(self.style.ERROR('OpenAI package required. Run: pip install openai'))
            return

        client = OpenAI(api_key=api_key)

        overwrite = options['overwrite']
        dry_run = options['dry_run']

        if overwrite:
            posts = Post.objects.all()
        else:
            posts = Post.objects.filter(image='')

        if not posts.exists():
            self.stdout.write('No posts need images.')
            return

        # Ensure media directory exists
        posts_media = os.path.join(settings.MEDIA_ROOT, 'posts')
        os.makedirs(posts_media, exist_ok=True)

        total = posts.count()
        self.stdout.write(f'Generating images for {total} posts...\n')
        self.stdout.write(f'Estimated cost: ${total * 0.04:.2f} - ${total * 0.08:.2f}\n')

        if dry_run:
            self.stdout.write('\n--- DRY RUN (no images generated) ---\n')
            for post in posts[:5]:
                prompt = self.create_prompt(post)
                self.stdout.write(f'\n{post.title[:50]}...')
                self.stdout.write(f'Prompt: {prompt[:200]}...\n')
            return

        generated = 0
        failed = 0

        for i, post in enumerate(posts, 1):
            try:
                self.stdout.write(f'[{i}/{total}] {post.title[:40]}... ', ending='')

                prompt = self.create_prompt(post)
                image_data = self.generate_with_dalle(client, prompt)

                # Resize to blog dimensions
                image_data = self.resize_image(image_data)

                # Generate filename from slug
                filename = f"{post.slug[:50]}.png"

                # Save to post
                post.image.save(filename, ContentFile(image_data), save=True)

                generated += 1
                self.stdout.write(self.style.SUCCESS('Done'))

            except Exception as e:
                failed += 1
                self.stdout.write(self.style.WARNING(f'Failed: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nComplete! Generated: {generated}, Failed: {failed}'))
        self.stdout.write(f'Estimated cost: ~${generated * 0.04:.2f}')
