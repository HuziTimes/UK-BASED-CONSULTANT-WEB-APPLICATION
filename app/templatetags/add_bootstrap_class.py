# custom_filters.py
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='add_class')
def add_class(value, css_class):
    if hasattr(value, 'as_widget'):
        return value.as_widget(attrs={"class": css_class})
    else:
        return mark_safe(f'<span class="{css_class}">{value}</span>')

@register.filter
def get_item(dictionary, key):
    """Custom filter to get an item from a dictionary by key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
