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
        url = urljoin(API_URL, handler)
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
        transactions = self.connect('transaction', activity__id=project_id)
        policy_markers = self.connect('policymarker', activity__id=project_id, significance__gt=0, _order_by='code')
        
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

#List of RSR feed relations, added on the 13th of februari
list_rsr_references = { "NL-1-PPR-23872": ["http://www.akvo.org/rsr/organisation/734", "http://www.akvo.org/rsr/project/574","http://search-api.openaid.nl/projectdetail_api/660/"], "NL-1-PPR-23872": ["http://www.akvo.org/rsr/organisation/734", "http://www.akvo.org/rsr/project/575","http://search-api.openaid.nl/projectdetail_api/660/"], "NL-1-PPR-23872": ["http://www.akvo.org/rsr/organisation/735", "http://www.akvo.org/rsr/project/773","http://search-api.openaid.nl/projectdetail_api/660/"], "NL-1-PPR-23872": ["http://www.akvo.org/rsr/organisation/734", "http://www.akvo.org/rsr/project/773","http://search-api.openaid.nl/projectdetail_api/660/"], "NL-1-PPR-23872": ["http://www.akvo.org/rsr/organisation/736", "http://www.akvo.org/rsr/project/773","http://search-api.openaid.nl/projectdetail_api/660/"], "NL-1-PPR-23872": ["http://www.akvo.org/rsr/organisation/734", "http://www.akvo.org/rsr/project/796","http://search-api.openaid.nl/projectdetail_api/660/"], "NL-1-PPR-23872": ["http://www.akvo.org/rsr/organisation/734", "http://www.akvo.org/rsr/project/797","http://search-api.openaid.nl/projectdetail_api/660/"], "NL-1-PPR-23872": ["http://www.akvo.org/rsr/organisation/734", "http://www.akvo.org/rsr/project/798","http://search-api.openaid.nl/projectdetail_api/660/"], "NL-1-PPR-23872": ["http://www.akvo.org/rsr/organisation/734", "http://www.akvo.org/rsr/project/799","http://search-api.openaid.nl/projectdetail_api/660/"], "NL-1-PPR-23872": ["http://www.akvo.org/rsr/organisation/734", "http://www.akvo.org/rsr/project/800","http://search-api.openaid.nl/projectdetail_api/660/"], "NL-1-PPR-23872": ["http://www.akvo.org/rsr/organisation/734", "http://www.akvo.org/rsr/project/801","http://search-api.openaid.nl/projectdetail_api/660/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/13", "http://www.akvo.org/rsr/project/464","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/13", "http://www.akvo.org/rsr/project/350","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/351","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/413","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/360","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/361","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/364","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/13", "http://www.akvo.org/rsr/project/366","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/13", "http://www.akvo.org/rsr/project/367","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/387","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/389","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/392","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/398","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/393","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/397","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/394","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/403","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/404","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/401","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/439","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/440","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/441","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/442","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/443","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/444","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/445","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/446","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/447","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/456","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/456","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/459","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/459","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/462","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/462","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/464","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/469","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/474","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/475","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/476","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/477","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/487","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/488","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/468","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/490","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/13", "http://www.akvo.org/rsr/project/490","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/13", "http://www.akvo.org/rsr/project/494","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/494","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/13", "http://www.akvo.org/rsr/project/495","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/497","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/529","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/544","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/545","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/534","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/555","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/558","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/559","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/559","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/572","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/494", "http://www.akvo.org/rsr/project/529","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/35", "http://www.akvo.org/rsr/project/533","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/533","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/8", "http://www.akvo.org/rsr/project/662","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/662","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/681","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-22168": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/682","http://search-api.openaid.nl/projectdetail_api/278/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/26","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/41","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/38","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/39","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/40","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/27","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/30","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/16","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/17","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/60","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/54","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/56","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/69","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/78","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/66", "http://www.akvo.org/rsr/project/50","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/43","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/49","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/75","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/101","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/164","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/129","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/175","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/94","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/152","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/141","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/145","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/153","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/180","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/179","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/155","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/157","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/154","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/138","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/171","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/147","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/148","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/182","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/150","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/151","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/143","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/183","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/161","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/178","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/142","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/187","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/188","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/210","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/235","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/268","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/209","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/347","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/421","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/457","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/326","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/560","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/571","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/576","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/330","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/332","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/595","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/590","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/614","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/603","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/656","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/640","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/727","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/134","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-19884": ["http://www.akvo.org/rsr/organisation/43", "http://www.akvo.org/rsr/project/315","http://search-api.openaid.nl/projectdetail_api/2669/"], "NL-1-PPR-23718": ["http://www.akvo.org/rsr/organisation/464", "http://www.akvo.org/rsr/project/706","http://search-api.openaid.nl/projectdetail_api/2284/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/385","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/212","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/34", "http://www.akvo.org/rsr/project/213","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/216","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/34", "http://www.akvo.org/rsr/project/216","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/34", "http://www.akvo.org/rsr/project/277","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/294","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/296","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/312","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/314","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/317","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/320","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/321","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/313","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/316","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/322","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/323","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/327","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/328","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/318","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/331","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/336","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/337","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/343","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/348","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/349","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/339","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/34", "http://www.akvo.org/rsr/project/339","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/352","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/353","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/354","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/355","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/356","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/357","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/363","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/365","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/406","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/390","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/399","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/396","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/400","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/402","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/405","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/408","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/409","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/410","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/341","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/411","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/412","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/414","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/416","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/418","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/419","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/422","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/423","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/34", "http://www.akvo.org/rsr/project/420","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/432","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/34", "http://www.akvo.org/rsr/project/433","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/434","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/34", "http://www.akvo.org/rsr/project/435","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/436","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/405", "http://www.akvo.org/rsr/project/438","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/448","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/34", "http://www.akvo.org/rsr/project/448","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/449","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/34", "http://www.akvo.org/rsr/project/449","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/485","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/273", "http://www.akvo.org/rsr/project/486","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/483","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/34", "http://www.akvo.org/rsr/project/483","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/526","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/472","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/546","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/450","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/417","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/585","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/586","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-22163": ["http://www.akvo.org/rsr/organisation/319", "http://www.akvo.org/rsr/project/587","http://search-api.openaid.nl/projectdetail_api/1272/"], "NL-1-PPR-19499": ["http://www.akvo.org/rsr/organisation/464", "http://www.akvo.org/rsr/project/711","http://search-api.openaid.nl/projectdetail_api/1059/"] }

class ProjectDetailApi(TemplateResponseMixin, BaseProjectDetailApi):
    template_name = 'website/projectdetail_api.html'

    def get_context_data(self, **kwargs):
        data = super(ProjectDetailApi, self).get_context_data(**kwargs)
        data['list_rsr'] = list_rsr_references
        return data


class ProjectDetailApiCsv(BaseProjectDetailApi):
    def render_to_response(self, context):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % str(unicode(context['project']['title']).encode('utf-8'))
        
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

