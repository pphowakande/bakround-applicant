
from django import template

register = template.Library()


@register.filter()
def sort_by_key(a_list, key_name):
    return sorted(a_list, key = lambda elt: elt[key_name])
