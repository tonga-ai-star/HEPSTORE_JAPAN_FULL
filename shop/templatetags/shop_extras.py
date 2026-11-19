from django import template
register=template.Library()
@register.filter
def money(value):
    try:return f'{int(value):,}'.replace(',','.')+' ₫'
    except (TypeError,ValueError):return '0 ₫'
@register.filter
def mul(value, arg):
    try:return int(value)*int(arg)
    except (TypeError,ValueError):return 0
