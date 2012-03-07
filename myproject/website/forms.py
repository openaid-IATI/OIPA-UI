# coding=utf-8
from decimal import Decimal
import itertools
import unicodedata
import re

from django.forms.widgets import RadioFieldRenderer
from django import forms
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

from website.templatetags.country import iso_to_country, country_to_iso
from website.templatetags.cur import currency
from world.models import WorldBorder
from website.iso_country_code import SUBREGIONS, COUNTRY
from website.widgets import FilterWidget
from website.fields import DynamicMultipleChoiceField, DynamicChoiceField


class SearchForm(forms.Form):
    query = forms.CharField(required=False,label='',widget=forms.TextInput(attrs={'class':'txt'}))
    
    def clean_query(self):
        data = strip_accents(self.cleaned_data['query'])
        
        for country in COUNTRY.keys():
            pattern = re.compile(re.escape(strip_accents(country)), re.IGNORECASE)
            if pattern.search(data):
                data = pattern.sub('', data, count=1)
        data = ' '.join(data.split())
        
        return data

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c))


class FilterRadioFieldRenderer(RadioFieldRenderer):
    def render(self):
        return mark_safe(u'<div class="filterblock">\n%s\n</div>' % u'\n'.join([u'<div class="row">%s</div>'
                % force_unicode(w) for w in self]))


class FilterForm(forms.Form):
    """
    This form shows choices based on the current query.
    
    The options shown are based on two things:
    1. Not providing options that will produce a query with no results
    2. Allowing users to change already selected filters 
    """
    query = forms.CharField(required=False, widget=forms.HiddenInput)
    countries = DynamicMultipleChoiceField(required=False, widget=FilterWidget)
    regions = DynamicMultipleChoiceField(required=False, widget=FilterWidget)
    budget = DynamicChoiceField(required=False, widget=forms.RadioSelect(renderer=FilterRadioFieldRenderer))
    sectors = DynamicMultipleChoiceField(required=False, widget=FilterWidget)

    def __init__(self, view=None, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        
        if view:
            activities = view.queryset or view.search(query=view.querydict['query'])
            
            def get_qs_for(filter_name):
                """
                Does a search without the current filter.
                This is to allow users to change already selected filters. 
                """
                if view.querydict.get(filter_name) and view.queryset:
                    querydict = view.querydict.copy()
                    del querydict[filter_name]
                    return view.search(**querydict)
                else:
                    return activities
        
            qs = get_qs_for('countries')
            countries = set(project['recipient_country_code'] for project in qs if project['recipient_country_code'])
            country_choices = sorted(zip(countries, [iso_to_country(iso) for iso in countries]), key=lambda country: country[1])
            country_choices = sorted(country_choices, key=lambda country: country[0] not in view.modified_request.getlist('countries'))
            
            qs = get_qs_for('budget')
            largest_budget = max(Decimal(project['total_budget']) for project in qs) if qs else 0
            budget_choices = list(itertools.takewhile(lambda x: x < largest_budget, [0, 10000, 50000, 100000, 500000, 1000000, 5000000, 10000000]))
            budget_choices = zip(budget_choices, ['> ' + currency(budget) for budget in budget_choices])
            
            qs = get_qs_for('sectors')
            sector_choices = set((project['sector_code'], project['sector']) for project in qs if project['sector'])
            sector_choices = sorted(sector_choices, key=lambda sector:sector[1])
            sector_choices = sorted(sector_choices, key=lambda sector:sector[0] not in view.request.GET.getlist('sectors'))
            
            region_choices = WorldBorder.objects.filter(iso2__in=countries).values_list('subregion', flat=True).distinct()
            region_choices = sorted(map(lambda x: (x, SUBREGIONS[x]), region_choices), key=lambda x: x[1])
            region_choices = sorted(region_choices, key=lambda region: unicode(region[0]) not in view.request.GET.getlist('regions'))
            
            self.fields['countries'].choices = country_choices
            self.fields['regions'].choices = region_choices
            self.fields['budget'].choices = budget_choices
            self.fields['sectors'].choices = sector_choices
    
    def clean(self):
        cleaned_data = self.cleaned_data
        query = cleaned_data.get('query')
        countries = cleaned_data.get('countries', [])
        regions = cleaned_data.get('regions')
        
        # adds query countries to country list
        countries_from_query= []
        if query:
            for country in COUNTRY.keys():
                pattern = re.compile(re.escape(strip_accents(country)), re.IGNORECASE)
                if pattern.search(query):
                    countries_from_query.append(country_to_iso(country.lower()))
        countries.extend(countries_from_query)
        
        # adds region countries to country list
        if regions:
            country_set = set(countries)
            subregion_set = set(WorldBorder.objects.filter(subregion__in=regions).values_list('iso2', flat=True))
            countries = list(country_set.union(subregion_set))
            
        cleaned_data['countries_from_query'] = countries_from_query
        cleaned_data['countries'] = countries
        
        return cleaned_data