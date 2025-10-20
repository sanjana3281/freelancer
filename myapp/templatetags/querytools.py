# myapp/templatetags/querytools.py
from django import template
from urllib.parse import urlencode

register = template.Library()

@register.filter
def get_item(d, key):
    try:
        return d.get(key, 0)
    except Exception:
        return 0

@register.simple_tag(takes_context=True)
def qs_without(context, key, value=None):
    """
    Build a querystring without a key or a specific key=value.
    """
    request = context["request"]
    params = request.GET.copy()
    if value is None:
        params.pop(key, None)
    else:
        vals = params.getlist(key)
        if value in vals:
            vals.remove(value)
            if vals:
                params.setlist(key, vals)
            else:
                params.pop(key, None)
    return urlencode(params, doseq=True)
