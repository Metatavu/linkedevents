ALLOWED_HOSTS = ['*']
STATIC_ROOT = os.path.join(BASE_DIR, "static")
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ['DATABASE_NAME'],
        'USER': os.environ['DATABASE_USER'],
        'PASSWORD': os.environ['DATABASE_PASS'],
        'HOST': os.environ['DATABASE_HOST'],
        'PORT': os.environ['DATABASE_PORT'],
    }
}

REST_FRAMEWORK = {
    'PAGE_SIZE': 20,
    'ORDERING_PARAM': 'sort',
    'DEFAULT_RENDERER_CLASSES': (
        'events.renderers.JSONRenderer',
        'events.renderers.JSONLDRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'events.parsers.CamelCaseJSONParser',
        'events.parsers.JSONLDParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'events.api_pagination.CustomPagination',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'events.auth.ApiKeyAuthentication',
        'events.auth.OIDCAuthentication'
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'VIEW_NAME_FUNCTION': 'events.api.get_view_name',
    'OIDC_ENDPOINT': os.environ['OIDC_ENDPOINT'],
    'OIDC_AUDIENCES': os.environ['OIDC_AUDIENCES'].split(','),
}