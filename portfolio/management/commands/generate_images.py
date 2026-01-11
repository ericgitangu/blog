"""
Generate images for posts that don't have one.

Creates gradient backgrounds with title text overlay.
Images are saved to MEDIA_ROOT/posts/

Usage:
    python manage.py generate_images
    python manage.py generate_images --overwrite  # Regenerate all
"""
import hashlib
import os
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from portfolio.models import Post

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


class Command(BaseCommand):
    help = 'Generate images for posts without images'

    # Color schemes based on tags
    COLOR_SCHEMES = {
        'rust': [(183, 65, 14), (255, 107, 53)],
        'python': [(55, 118, 171), (255, 212, 59)],
        'java': [(176, 114, 25), (237, 139, 0)],
        'javascript': [(247, 223, 30), (50, 51, 48)],
        'react': [(97, 218, 251), (32, 35, 42)],
        'blockchain': [(247, 147, 26), (20, 21, 26)],
        'kubernetes': [(50, 108, 229), (255, 255, 255)],
        'aws': [(255, 153, 0), (35, 47, 62)],
        'django': [(12, 75, 51), (44, 160, 101)],
        'go': [(0, 173, 216), (255, 255, 255)],
        'android': [(61, 220, 132), (255, 255, 255)],
        'ai': [(138, 43, 226), (255, 105, 180)],
        'security': [(220, 20, 60), (25, 25, 25)],
        'career': [(70, 130, 180), (255, 255, 255)],
        'education': [(34, 139, 34), (255, 255, 255)],
        'project': [(255, 69, 0), (255, 215, 0)],
        'certifications': [(75, 0, 130), (238, 130, 238)],
        'skills': [(0, 128, 128), (255, 255, 255)],
        'default': [(99, 102, 241), (168, 85, 247)],
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Regenerate images even for posts that have one'
        )

    def get_color_scheme(self, post):
        """Get color scheme based on post tags."""
        tags = [t.caption.lower() for t in post.tags.all()]

        for tag in tags:
            for key in self.COLOR_SCHEMES:
                if key in tag:
                    return self.COLOR_SCHEMES[key]

        return self.COLOR_SCHEMES['default']

    def wrap_text(self, text, font, max_width, draw):
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width > max_width:
                if len(current_line) == 1:
                    lines.append(current_line[0])
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines[:3]  # Max 3 lines

    def create_gradient(self, width, height, color1, color2):
        """Create a diagonal gradient image."""
        image = Image.new('RGB', (width, height))

        for y in range(height):
            for x in range(width):
                # Diagonal gradient
                ratio = (x + y) / (width + height)
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                image.putpixel((x, y), (r, g, b))

        return image

    def generate_image(self, post):
        """Generate an image for a post."""
        width, height = 800, 400
        color1, color2 = self.get_color_scheme(post)

        # Create gradient background
        image = self.create_gradient(width, height, color1, color2)
        draw = ImageDraw.Draw(image)

        # Try to load a font, fall back to default
        font_size = 56
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except (IOError, OSError):
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except (IOError, OSError):
                font = ImageFont.load_default()

        # Wrap and draw title
        title = post.title[:80]  # Limit title length
        lines = self.wrap_text(title, font, width - 80, draw)

        # Calculate vertical position to center text
        line_height = font_size + 14
        total_height = len(lines) * line_height
        y_start = (height - total_height) // 2

        # Draw text with strong outline for better readability
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y_start + i * line_height

            # Draw black outline (multiple passes for thickness)
            outline_color = (0, 0, 0)
            for offset_x in range(-3, 4):
                for offset_y in range(-3, 4):
                    if offset_x != 0 or offset_y != 0:
                        draw.text((x + offset_x, y + offset_y), line, font=font, fill=outline_color)

            # Main white text
            draw.text((x, y), line, font=font, fill=(255, 255, 255))

        # Add tag indicator at bottom with outline
        tags = [t.caption for t in post.tags.all()[:3]]
        if tags:
            tag_text = ' | '.join(tags)
            try:
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            except (IOError, OSError):
                small_font = font
            tag_x, tag_y = 20, height - 40
            # Outline for tags
            for ox in range(-2, 3):
                for oy in range(-2, 3):
                    if ox != 0 or oy != 0:
                        draw.text((tag_x + ox, tag_y + oy), tag_text.upper(), font=small_font, fill=(0, 0, 0))
            draw.text((tag_x, tag_y), tag_text.upper(), font=small_font, fill=(255, 255, 255))

        return image

    def handle(self, *args, **options):
        if not HAS_PILLOW:
            self.stdout.write(self.style.ERROR('Pillow is required. Run: pip install Pillow'))
            return

        overwrite = options['overwrite']

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

        generated = 0
        for post in posts:
            try:
                image = self.generate_image(post)

                # Save to BytesIO
                buffer = BytesIO()
                image.save(buffer, format='PNG', optimize=True)
                buffer.seek(0)

                # Generate filename from slug
                filename = f"{post.slug[:50]}.png"

                # Save to post
                post.image.save(filename, ContentFile(buffer.read()), save=True)

                generated += 1
                self.stdout.write(f'  Generated: {post.title[:50]}...')

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Failed for {post.title[:30]}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nDone! Generated {generated} images.'))
