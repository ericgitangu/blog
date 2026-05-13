import re
import markdown
from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='markdown')
def markdown_format(text):
    """Convert markdown text to HTML."""
    if not text:
        return ''

    # Configure markdown with useful extensions
    md = markdown.Markdown(extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.tables',
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists',
    ])

    return mark_safe(md.convert(text))


@register.filter(name='plaintext')
def plaintext(text):
    """Convert markdown to plain text with normalized whitespace."""
    if not text:
        return ''

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.tables',
    ])
    html = md.convert(text)

    # Strip HTML tags
    plain = strip_tags(html)

    # Decode common HTML entities
    import html as html_module
    plain = html_module.unescape(plain)

    # Strip markdown syntax that survived (e.g. inline headers, bold, links)
    plain = re.sub(r'#{1,6}\s*', '', plain)          # headers
    plain = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', plain)  # bold/italic
    plain = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', plain)   # links
    plain = re.sub(r'`([^`]+)`', r'\1', plain)       # inline code

    # Normalize whitespace
    plain = re.sub(r'\s+', ' ', plain).strip()

    return plain
