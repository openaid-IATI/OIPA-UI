from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list import ListView
from django.template.context import Context
from django.utils import simplejson
from django.views.generic.base import View, TemplateResponseMixin
from django.utils.http import urlencode
from django.http import Http404, HttpResponse
from django.core.cache import cache
from settings import API_URL

from world.models import WorldBorder
from website.forms import FilterForm, SearchForm
from website.templatetags.country import iso_to_country
from website.templatetags.cur import currency
from website.utils import UnicodeWriter
from website.templatetags.significance import code_to_significance

from urllib2 import urlopen, URLError
from urlparse import urljoin
from datetime import datetime
from decimal import Decimal

class ApiMixin(object):
    def connect(self, handler, **query):
        url = urljoin(API_URL, handler) + '/'
        
        # removes queries with empty values
        query = self.filter_querydict(query)
        is_empty_query = not bool(query) #save for later reference
        
        if query:
            url += '?'
            for k, v in query.copy().items():
                # handle OR-ing of search parameters
                if '|' in k:
                    del query[k]
                    url += '|'.join(urlencode({i : v}) for i in k.split('|'))
        if query:
            url += '&' + urlencode(query).replace('%7C', '|')
        
        if handler == 'activity' and is_empty_query:
            # Handles caching for the main search page
            cached_data = cache.get('all-activities')
            remote_last_updated = unicode(self.html_or_404(urljoin(API_URL, 'last_updated/')))
            cache_invalid = cache.get('last_updated') != remote_last_updated
            
            if cached_data and not cache_invalid:
                # Cache hit!
                json = cached_data
            else:
                # No cache! Get data and fill cache
                json = self.json_or_404(url)
                cache.set('all-activities', json, 60*60*24)
                cache.set('last_updated', remote_last_updated)
        else:
            json = self.json_or_404(url)
        return json
    
    def filter_querydict(self, querydict):
        return dict([(k, v) for k, v in querydict.items() if v not in['', None, []]])
    
    def html_or_404(self, url):
        try:
            return urlopen(url).read()
        except URLError:
            raise Http404
        
    def json_or_404(self, url):
        try:
            response = urlopen(url)
            return simplejson.load(response)
        except URLError:
            raise Http404
        

class WhereaidApi(ApiMixin, ListView):
    template_name = 'website/whereaid_api.html'
    searchform_class = SearchForm
    filterform_class = FilterForm
    context_object_name = 'activity_list'
    paginate_by = 15
    
    def get(self, request, *args, **kwargs):
        searchform = self.searchform_class(data=request.GET)
        filterform = self.filterform_class(data=request.GET)
        self.order_by = self.request.GET.get('order_by')
        
        # holds extra filters based on cleaned data
        self.modified_request = self.request.GET.copy()
        
        if searchform.is_valid() and filterform.is_valid():
            query = searchform.cleaned_data['query']
            countries = filterform.cleaned_data['countries']
            regions = filterform.cleaned_data['regions']
            budget = filterform.cleaned_data['budget']
            sectors = filterform.cleaned_data['sectors']
            self.querydict = dict(
                query=query,
                countries=countries,
                regions=regions,
                budget=budget,
                sectors=sectors,
            )
            
            # adds countries to selected checkboxes
            countries_from_query = filterform.cleaned_data['countries_from_query']
            for country in countries_from_query:
                self.modified_request.update(dict(countries=country))

            self.queryset = self.search(**self.querydict)
           
        return super(WhereaidApi, self).get(self, request, *args, **kwargs)
    
    def search(self, query='', countries=[], regions=[], budget=[], sectors=[]):
        """
        Does a search on the backend.
        
        All the filters are rewritten to a format used by the backend.
        """
        qs = self.connect(
            'activity',
            **{
               'description__icontains|title__icontains' : query,
               'recipient_country_code' : '|'.join(countries),
               'total_budget__gt': budget,
               'sector_code' : '|'.join(sectors),
               '_order_by' : self.order_by if not self.order_by in ['recipient_country', '-recipient_country'] else None
            }
        )
        
        # Only country codes are stored in the DB, so we need to sort manually
        # if we want to sort by full country name
        if self.order_by == 'recipient_country':
            return self._sort_countries(qs, reverse=False)
        elif self.order_by == '-recipient_country':
            return self._sort_countries(qs, reverse=True)
        else:
            return qs
        
    def get_context_data(self, **kwargs):
        """
        Note: Forms are bound with the modified request to include extra filters
        """
        context = super(WhereaidApi, self).get_context_data(**kwargs)
        context['search_form'] = self.searchform_class(data=self.modified_request)
        context['filter_form'] = self.filterform_class(data=self.modified_request, view=self)
        context['countries'] = self._get_map_country_information()
        context['url'] = '?%s' % urlencode(self.request.GET, doseq=True)
        context['sorting_links'] = self._get_sorting_links()

        return context

    def render_to_response(self, context):
        if self.request.GET.get('format','html') == 'csv':
            return self.render_to_csv_response(context)
        else:
            return ListView.render_to_response(self, context)
    
    def render_to_csv_response(self, context):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=search_results.csv'
        
        writer = UnicodeWriter(response)
        
        writer.writerow(['title', 'description', 'country', 'start date', 'budget', 'principal sector'])
        for activity in context['paginator'].object_list:
            title = activity['title']
            description = activity['description']
            country = iso_to_country(activity['recipient_country_code']) or "Unspecified"
            start_date = activity['start_actual']
            budget = currency(activity['total_budget'])
            sector = activity['sector']
            writer.writerow([title, description, country, start_date, budget, sector])
        return response
    
    def _sort_countries(self, qs, reverse=False):
        return sorted(qs, key=lambda activity: iso_to_country(activity['recipient_country_code']), reverse=reverse)
        
    def _get_sorting_links(self):
        return [
            SortingLink('total_budget', 'Budget', self.order_by, self.request.GET),
            SortingLink('start_actual', 'Start date', self.order_by, self.request.GET),
            SortingLink('recipient_country', 'Country', self.order_by, self.request.GET),
        ]
    
    def _get_map_country_information(self):
        countries = set(project['recipient_country_code'] for project in self.queryset if project['recipient_country_code'])
        countries = list(WorldBorder.objects.filter(iso2__in=countries))
        for country in countries:
            projects = [project for project in self.queryset if project['recipient_country_code'] == country.iso2]
            country.total_budget = sum(Decimal(project['total_budget']) for project in projects)
            country.total_activities = len(projects)
            country_parameters = self.request.GET.copy()
            country_parameters['countries'] = country.iso2
            country.total_activities_url = '?%s' % urlencode(country_parameters, doseq=True)  
        return countries


class BaseProjectDetailApi(ApiMixin, View):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        project_id = self.kwargs.get('id')
        
        project = self.connect('activity/%s/' % project_id)
        project.update(organisation=self.connect('organisation/%s/' % project['organisation_id']))
        transactions = self.connect('transaction', activity_id=project_id)
        policy_markers = self.connect('policymarker', activity_id=project_id, significance__gt=0, _order_by='code')
        
        commitment_list = []
        disbursement_list = []
        for t in transactions:
            if t['transaction_type'] == 'Commitments':
                commitment_list.append(t)
            else:
                disbursement_list.append(t)
        
        context = kwargs
        context['project'] = project
        context['commitment_list'] = commitment_list
        context['disbursement_list'] = disbursement_list
        
        context['table'] = [
            ['Country Information'],
            ['Country', iso_to_country(project['recipient_country_code'])],
            [],
            ['Activity Information'],
            ['IATI Identifier', project['identifier']],
            ['Reporting Organisation', project['organisation']['name']], 
            ['Sector', project['sector']],
            ['Sector code', project['sector_code']],
            ['Last updated', project['last_updated']],
            ['Start date planned', format_date(project['start_planned'])],
            ['Start date actual', format_date(project['start_actual'])],
            ['End date planned', format_date(project['end_planned'])],
            ['End date actual', format_date(project['end_actual'])],
            ['Collaboration type', project['collaboration_type']],
            ['Flow type', project['default_flow_type']],
            ['Aid type', project['default_aid_type']],
            ['Finance type', project['default_finance_type']],
            ['Tying status', project['default_tied_status']],
            ['Activity status', project['activity_status']],
            [],
            ['Participating Organisations'],
            ['Name', project['organisation']['name']],
            ['Type', project['organisation']['type']],
            ['Organisation reference code', project['organisation']['ref']],
            [],
        ]
        
        if commitment_list:
            context['table'] += [
                ['Commitments']
            ]
            for commitment in commitment_list:
                context['table'] += [
                    ['Activity', project['title']],
                    ['Provider org', commitment['provider_org']],
                    ['Receiver org', commitment['receiver_org']],
                    ['Value', currency(Decimal(commitment['value']))],
                    ['Transaction date', format_date(commitment['transaction_date'])],
                    [],
                ]
        # TODO: DNRY
        if disbursement_list:
            context['table'] += [
                ['Disbursements']
            ]
            for disbursement in disbursement_list:
                context['table'] += [
                    ['Activity', project['title']],
                    ['Provider org', disbursement['provider_org']],
                    ['Receiver org', disbursement['receiver_org']],
                    ['Value', currency(Decimal(disbursement['value']))],
                    ['Transaction date', format_date(disbursement['transaction_date'])],
                    [],
                ]
        
        if policy_markers:
            context['table'] += [
                ['Policy markers']
            ]
            for policy_marker in policy_markers:
                context['table'] += [
                    ['Description', policy_marker['description']],
                    ['Significance', code_to_significance(policy_marker['significance'])],
                    [],
                ]
        
        context['table'] = [[cell or 'Unknown' for cell in row] for row in context['table']]
        
        return context


class ProjectDetailApi(TemplateResponseMixin, BaseProjectDetailApi):
    template_name = 'website/projectdetail_api.html'


class ProjectDetailApiCsv(BaseProjectDetailApi):
    def render_to_response(self, context):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % context['project']['title']
        
        writer = UnicodeWriter(response)
        writer.writerow([context['project']['title']])
        writer.writerow([context['project']['description']])
        writer.writerow([])
        writer.writerows(context['table'])
        return response


class SortingLink(object):
    """
    Calculates the various attributes for a sorting link on the whereaid_api page
    """
    def __init__(self, field, text, order_by, get_parameters):
        self.text = text
        get_parameters = get_parameters.copy()
        
        if order_by == field:
            get_parameters['order_by'] = '-%s' % field
            self.cls = 'ascending'
        elif order_by == '-%s' % field:
            get_parameters['order_by'] = field
            self.cls = 'descending'
        else:
            get_parameters['order_by'] = field
            self.cls = 'unsorted'
        self.url = '?%s' % urlencode(get_parameters, doseq=True)


def format_date(string):
    return datetime.strptime(string, '%Y-%m-%d').strftime('%d-%m-%Y') if string else None
