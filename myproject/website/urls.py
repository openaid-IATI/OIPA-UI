from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from website.views import WhereaidApi, ProjectDetailApi, ProjectDetailApiCsv


urlpatterns = patterns('website.views',
    (r'^whereaid_api/$', WhereaidApi.as_view()),
    (r'^projectdetail_api/(?P<id>[0-9]+)/$', ProjectDetailApi.as_view()),
    (r'^projectdetail_api_csv/(?P<id>[0-9]+)/$', ProjectDetailApiCsv.as_view()),
    (r'^map/$', direct_to_template, {'template': 'website/includes/map.html'}),
)