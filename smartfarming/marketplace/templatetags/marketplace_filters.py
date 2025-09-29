from django import template
from marketplace.models import Tool, Pesticide  # adjust if models are in another app

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

# ✅ Get tool object if item_type is "tool"
@register.filter
def to_tool(item):
    try:
        if item.item_type == "tool":
            return Tool.objects.get(id=item.item_id)
    except Tool.DoesNotExist:
        return None
    return None

# ✅ Get pesticide object if item_type is "pesticide"
@register.filter
def to_pesticide(item):
    try:
        if item.item_type == "pesticide":
            return Pesticide.objects.get(id=item.item_id)
    except Pesticide.DoesNotExist:
        return None
    return None
