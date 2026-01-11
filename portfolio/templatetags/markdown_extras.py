import markdown
from django import template
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
