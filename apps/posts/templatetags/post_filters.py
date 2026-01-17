from django import template

register = template.Library()

@register.filter
def qmzp(value):
    return value
