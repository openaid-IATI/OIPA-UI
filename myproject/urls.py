from django.conf.urls.defaults import *

from django.contrib import admin
from settings import rel
admin.autodiscover()

urlpatterns = patterns('',
    (r'^', include('myproject.website.urls')),

    (r'^admin/', include(admin.site.urls)),
    
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rel('media')}),
)
