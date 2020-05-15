from django import template
register = template.Library()


@register.filter(is_safe=True)
def add_class(field, name):
    if 'vCheckboxLabel' in name:
        field = field.replace(':', '')
    return field.replace('>', f' class="{name}">')
