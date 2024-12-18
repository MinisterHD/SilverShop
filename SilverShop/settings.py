"""
Django settings for SilverShop project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
from decouple import config

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!


# SECURITY WARNING: don't run with debug turned on in production!


SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'zarrin_pal',
    'user_app',
    'django_celery_beat',
    'product_app.apps.ProductAppConfig',
    'order_app',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    
    
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    
]

ROOT_URLCONF = 'SilverShop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'SilverShop.wsgi.application'
ASGI_APPLICATION = 'SilverShop.asgi.application'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='3306'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
        'DEFAULT_FILTER_BACKENDS': [
      'rest_framework.filters.SearchFilter'],   
        'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication'
        ,
    ], 'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',

]
AUTH_USER_MODEL = 'user_app.User'

import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

from datetime import timedelta

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  
SESSION_COOKIE_SAMESITE = 'None' 
SESSION_COOKIE_AGE = 30 * 24 * 60 * 60 
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
# CSRF settings
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'None'  

SESSION_COOKIE_DOMAIN = "127.0.0.1"  
CSRF_COOKIE_DOMAIN = "127.0.0.1"  

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,  
    'AUTH_COOKIE': 'access_token',  
    'AUTH_COOKIE_SECURE': False,
    'AUTH_COOKIE_HTTP_ONLY': False,  
    'AUTH_COOKIE_PATH': '/',  
    'AUTH_COOKIE_SAMESITE': 'Lax',
}



ALLOWED_HOSTS = ['*']
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [config('REDIS_URL', default='redis://redis:6379')],
        },
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'SilverShop API',
    'DESCRIPTION': 'API documentation for SilverShop project',
    'VERSION': '1.0.0',
    
}
'''
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': config('LOGGING_LEVEL', default='DEBUG'),  # Default to DEBUG
            'class': 'logging.FileHandler',
            'filename': config('LOGGING_FILE_PATH', default=os.path.join(BASE_DIR, 'logfile.log')),  # Default to BASE_DIR/logfile.log
        },
        'console': {
            'level': config('LOGGING_LEVEL', default='DEBUG'),  # Default to DEBUG
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': config('LOGGING_LEVEL', default='DEBUG'),  # Default to DEBUG
            'propagate': True,
        },
        'chat_app': {
            'handlers': ['file', 'console'],
            'level': config('LOGGING_LEVEL', default='DEBUG'),  # Default to DEBUG
            'propagate': True,
        },
    },
}
'''

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


CELERY_BROKER_URL = config('REDIS_URL', default='redis://redis:6379')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://redis:6379')
CELERY_BEAT_SCHEDULE = {
    'update_delivery_status': {
        'task': 'order_app.tasks.update_delivery_status',
        'schedule': 86400,
    },
}

CORS_ALLOW_ALL_ORIGINS = True

# OR specify allowed origins (recommended for production)
#CORS_ALLOWED_ORIGINS = [
  #  "http://localhost:3000",  # Add your frontend URL here
   # "https://your-frontend-domain.com",
#]
# settings.py


CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Adjust this to match your frontend origin
]
KAVENEGAR_API_KEY = config('KAVENEGAR_API_KEY')
OWNER_PHONE_NUMBER = '1234567890'

# Add this to your settings.py file

# Sandbox mode for Zarinpal
SANDBOX = config('SANDBOX', cast=bool)  # Set to False in production

# Merchant ID for Zarinpal
MERCHANT = config('MERCHANT')
TIME_ZONE = 'Asia/Tehran'
USE_TZ = True