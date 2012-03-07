from django import template
register = template.Library()

@register.filter
def code_to_significance(code):
    activity = {
        '1' : 'Significant',
        '2' : 'Principal',
    }
    return activity[code]