import os

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'ms-length',
    'ms-status',
    'ms-fake',
    'ms-attributes',
    'ms-errors',
)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'UNAUTHENTICATED_USER': None
}
INSTALLED_APPS = [
    'rest_framework',
    'corsheaders',
]
MIDDLEWARE_CLASSES = [
    'corsheaders.middleware.CorsMiddleware',
]
MS_DEFAULT_LIST_LENGTH = 10
