from django import template
from django.conf import settings
from decimal import Decimal
register = template.Library()

@register.filter
def currency(value):
    symbol = '$' 
    thousand_sep = ''
    decimal_sep = ''
    # try to use settings if set 
    try:
        symbol = settings.CURRENCY_SYMBOL
    except AttributeError:
        pass

    try:
        thousand_sep = settings.THOUSAND_SEPARATOR
        decimal_sep = settings.DECIMAL_SEPARATOR
    except AttributeError:
        thousand_sep = ',' 
        decimal_sep = '.' 

    intstr = str(int(Decimal(value)))
    f = lambda x, n, acc=[]: f(x[:-n], n, [(x[-n:])]+acc) if x else acc
    intpart = thousand_sep.join(f(intstr, 3))
    return "%s%s" % (symbol, intpart)
