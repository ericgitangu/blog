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

    # Normalize whitespace: collapse multiple spaces/newlines into single space
    plain = re.sub(r'\s+', ' ', plain).strip()

    return plain
