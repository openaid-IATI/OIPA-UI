# local settings do NOT add this to version control!

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'openaid33',                      # Or path to database file if using sqlite3.
        'USER': 'aoi888',                      # Not used with sqlite3.
        'PASSWORD': 'zz558ad',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5433',
    },

    #'world': {
         #'ENGINE': 'django.contrib.gis.db.backends.mysql',
         #'NAME': 'geodjango',
         #'USER': 'geo',
    #}
}


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

GEOS_LIBRARY_PATH = '/usr/local/lib/libgeos_c.so.1'