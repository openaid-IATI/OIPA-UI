import string

from django import template

from website.iso_country_code import COUNTRY_REVERSED, COUNTRY

register = template.Library()

@register.filter
def country_to_iso(value):
    countries = dict(zip(map(string.lower,COUNTRY.keys()),COUNTRY.values()))
    return countries.get(value.lower(), "Unknown")

@register.filter
def iso_to_country(value):
    return COUNTRY_REVERSED.get(value, "")
