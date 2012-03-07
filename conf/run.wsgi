import os, sys

apache_configuration= os.path.dirname(__file__)
project = os.path.dirname(apache_configuration)
workspace = os.path.dirname(project)
sys.path.append(workspace) 

sys.path.append('/var/lib/python-support/python2.5/django/')
sys.path.append('/home/openaid/public_html/openaid.com/openaid/')
sys.path.append('/home/openaid/public_html/openaid.com/openaid/myproject/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()