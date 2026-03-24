from pathlib import Path
import os
import json
import random
import hexoweb.exceptions as exceptions
import logging
import urllib3

urllib3.disable_warnings()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

LOGIN_REDIRECT_URL = "home"  # Route defined in home/urls.py
LOGOUT_REDIRECT_URL = "home"  # Route defined in home/urls.py

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-mrf1flh+i8*!ao73h6)ne#%gowhtype!ld#+(j^r*!^11al2vz'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

LOCAL_CONFIG = False

# Application definition
# NOTE:
# INSTALLED_APPS depends on the final DATABASES backend, so it is assigned
# after DATABASES and USE_MONGODB are fully resolved.
INSTALLED_APPS = []

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

visitor_cors_origins = os.environ.get('VISITOR_CORS_ALLOWED_ORIGINS')
if visitor_cors_origins:
    try:
        parsed_visitor_origins = json.loads(visitor_cors_origins)
        if isinstance(parsed_visitor_origins, list) and parsed_visitor_origins:
            CORS_ALLOWED_ORIGINS = parsed_visitor_origins
            CORS_ORIGIN_ALLOW_ALL = False
    except json.JSONDecodeError:
        logging.warning('VISITOR_CORS_ALLOWED_ORIGINS is not valid JSON, keeping default CORS settings')

# WebAuthn / Passkeys Configuration
AUTHENTICATION_BACKENDS = [
    'passkeys.backend.PasskeyModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

errors = ""

if os.environ.get("MONGODB_HOST"):  # 浣跨敤MONGODB
    logging.info("浣跨敤鐜鍙橀噺涓殑MongoDB鏁版嵁搴?)
    for env in ["MONGODB_HOST", "MONGODB_PORT", "MONGODB_PASS"]:
        if env not in os.environ:
            if env == "MONGODB_USER" and "MONGODB_USERNAME" in os.environ:
                continue
            if env == "MONGODB_PASS" and "MONGODB_PASSWORD" in os.environ:
                continue
            errors += f"\"{env}\" "
    DATABASES = {
        'default': {
            'ENGINE': 'django_mongodb_backend',
            'NAME': os.environ.get("MONGODB_DB") or os.environ.get("MONGODB_NAME") or 'django',
            'HOST': os.environ.get("MONGODB_HOST"),
            'PORT': int(os.environ.get("MONGODB_PORT", "27017")),
            'USER': os.environ.get("MONGODB_USER") or os.environ.get("MONGODB_USERNAME") or "root",
            'PASSWORD': os.environ.get("MONGODB_PASS") or os.environ.get("MONGODB_PASSWORD"),
            'OPTIONS': {
                'authSource': os.environ.get("MONGODB_AUTH_DB") or os.environ.get("MONGODB_AUTHDB") or "admin",
                'authMechanism': os.environ.get("MONGODB_AUTH_MECHANISM") or 'SCRAM-SHA-1',
            }
        }
    }
elif os.environ.get("PG_HOST") or os.environ.get("POSTGRES_HOST"):  # 浣跨敤 PostgreSQL
    logging.info("浣跨敤鐜鍙橀噺涓殑PostgreSQL鏁版嵁搴?)
    for env in ["PG_HOST", "PG_PASS"]:
        if (env not in os.environ) and (env.replace("PG_", "POSTGRES_") not in os.environ):  # 璇嗗埆涓嶅悓鐨勬牸寮?
            if env == "PG_USER" and "POSTGRES_USERNAME" in os.environ:
                continue
            if env == "PG_PASS" and "POSTGRES_PASSWORD" in os.environ:
                continue
            errors += f"\"{env}\" "
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get("PG_DB") or os.environ.get("POSTGRES_DB") or os.environ.get(
                "POSTGRES_DATABASE") or "root",
            'USER': os.environ.get("PG_USER") or os.environ.get("POSTGRES_USERNAME") or os.environ.get(
                "POSTGRES_USER") or "root",
            'PASSWORD': os.environ.get("PG_PASS") or os.environ.get("POSTGRES_PASSWORD"),
            'HOST': os.environ.get("PG_HOST") or os.environ.get("POSTGRES_HOST"),
            'PORT': os.environ.get("PG_PORT") or os.environ.get("POSTGRES_PORT") or 5432,
        }
    }
elif os.environ.get("MYSQL_HOST"):  # 浣跨敤MYSQL
    logging.info("浣跨敤鐜鍙橀噺涓殑MySQL鏁版嵁搴?)
    for env in ["MYSQL_HOST", "MYSQL_PORT", "MYSQL_PASSWORD"]:
        if env not in os.environ:
            if env == "MYSQL_PASSWORD" and "MYSQL_PASS" in os.environ:
                continue
            errors += f"\"{env}\" "
    import pymysql

    pymysql.install_as_MySQLdb()
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('MYSQL_NAME') or os.environ.get('MYSQL_DB') or 'root',
            'HOST': os.environ.get('MYSQL_HOST'),
            'PORT': os.environ.get('MYSQL_PORT'),
            'USER': os.environ.get('MYSQL_USER') or os.environ.get('MYSQL_USERNAME') or 'root',
            'PASSWORD': os.environ.get('MYSQL_PASSWORD') or os.environ.get('MYSQL_PASS'),
            'OPTIONS': {
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"
            }
        }
    }
    if os.environ.get("MYSQL_SSL"):
        DATABASES["default"]["OPTIONS"]["ssl"] = {
            "ssl_verify_cert": True,
            "ssl_verify_identity": False,
        }
    if os.environ.get("PLANETSCALE"):
        DATABASES["default"]["ENGINE"] = "hexoweb.libs.django_psdb_engine"
elif os.path.exists(BASE_DIR / "configs.py"):
    import configs

    DATABASES = configs.DATABASES
    LOCAL_CONFIG = True
else:
    errors = "鏁版嵁搴?

# Vercel 鏃犳硶浣跨敤 Sqlite
# else:  # sqlite
#     print("浣跨敤sqlite鏁版嵁搴?)
#     import sqlite3
#
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': 'qexo_data.db',
#         }
#     }

if errors:
    logging.error(f"{errors}鏈缃? 璇锋煡鐪? https://www.oplog.cn/qexo/start/build.html")
    raise exceptions.InitError(f"{errors}鏈缃? 璇锋煡鐪? https://www.oplog.cn/qexo/start/build.html")

# Update USE_MONGODB based on actual database backend ENGINE
# This ensures compatibility with both environment variable and local config.py deployments
USE_MONGODB = 'mongodb' in DATABASES.get('default', {}).get('ENGINE', '').lower()


def _build_installed_apps(use_mongodb):
    if use_mongodb:
        return [
            # 'django.contrib.admin',
            'core.mongodb_apps.MongoAuthConfig',  # Custom config for MongoDB
            'core.mongodb_apps.MongoContentTypesConfig',  # Custom config for MongoDB
            'django.contrib.sessions',
            'django.contrib.messages',
            # 'django.contrib.staticfiles',
            'hexoweb.apps.ConsoleConfig',
            'corsheaders',
            'passkeys',
        ]

    return [
        # 'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        # 'django.contrib.staticfiles',
        'hexoweb.apps.ConsoleConfig',
        'corsheaders',
        'passkeys',
    ]


INSTALLED_APPS = _build_installed_apps(USE_MONGODB)

def _load_allowed_hosts(local_config):
    if local_config:
        # 鏈湴閰嶇疆妯″紡锛氬繀椤昏缃?DOMAINS
        try:
            hosts = configs.DOMAINS
        except AttributeError:
            raise exceptions.InitError('鏈湴 configs.py 缂哄皯 DOMAINS, 璇疯缃负 ["example.com"]')
        
        if not isinstance(hosts, (list, tuple)):
            raise exceptions.InitError('鏈湴閰嶇疆 DOMAINS 蹇呴』涓哄垪琛? 渚嬪 ["example.com"]')
        
        if (not hosts) or hosts == ["*"]:
            raise exceptions.InitError('鏈湴閰嶇疆 DOMAINS 鏈厤缃湁鏁堝煙鍚? 璇峰～鍐欏疄闄呭煙鍚? 渚嬪 ["example.com"]')
        
        logging.info(f"浠庢湰鍦伴厤缃幏鍙栧煙鍚? {list(hosts)}")
        return list(hosts)
    
    else:
        # 鐜鍙橀噺妯″紡锛氭敹闆?DOMAINS 鍜?Vercel 鐜鍙橀噺
        domains_hosts = []
        vercel_hosts = []
        
        # 瑙ｆ瀽 DOMAINS 鐜鍙橀噺
        domains_raw = os.environ.get("DOMAINS")
        if domains_raw:
            try:
                parsed = json.loads(domains_raw)
                if not isinstance(parsed, (list, tuple)):
                    raise exceptions.InitError('鐜鍙橀噺 DOMAINS 蹇呴』涓哄垪琛? 渚嬪 ["example.com"]')
                domains_hosts = [h for h in parsed if h and h != "*"]
            except json.JSONDecodeError as exc:
                raise exceptions.InitError(f"DOMAINS 鐜鍙橀噺瑙ｆ瀽澶辫触: {exc}")
        
        # 鏀堕泦 Vercel 鐜鍙橀噺
        for env_var in ["VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL"]:
            url = os.environ.get(env_var)
            if url and url not in vercel_hosts:
                vercel_hosts.append(url)
        
        # 纭畾鏈€缁?hosts
        if domains_hosts and vercel_hosts:
            # 涓よ€呴兘鏈夛細鍙栦氦闆嗭紝浜ら泦涓虹┖鍒欑敤骞堕泦
            hosts = [h for h in domains_hosts if h in vercel_hosts] or list(set(domains_hosts + vercel_hosts))
            logging.info(f"浠?DOMAINS 鍜?Vercel 鐜鍙橀噺鑾峰彇鍩熷悕: {hosts}")
        else:
            hosts = domains_hosts or vercel_hosts
            if not hosts:
                raise exceptions.InitError('DOMAINS 鏈缃笖鏈娴嬪埌 Vercel 鐜鍙橀噺, 璇蜂负 DOMAINS 鐜鍙橀噺濉啓瀹為檯鍩熷悕, 渚嬪 ["example.com"]')
            logging.info(f"浠巤'鐜鍙橀噺 DOMAINS' if domains_hosts else 'Vercel 鐜鍙橀噺'}鑾峰彇鍩熷悕: {hosts}")
        
        return hosts


def _build_csrf_trusted_origins(hosts):
    origins = []
    for host in hosts:
        if (not host) or host == "*":
            continue
        host = host.rstrip("/")
        if "://" in host:
            origins.append(host)
        else:
            origins.append(f"https://{host}")
            origins.append(f"http://{host}")
    return origins


ALLOWED_HOSTS = _load_allowed_hosts(LOCAL_CONFIG)
CSRF_TRUSTED_ORIGINS = _build_csrf_trusted_origins(ALLOWED_HOSTS)

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'zh-Hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True


USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# STATIC_URL = 'static/'
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "static"),
# ]
# STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

# Use ObjectIdAutoField for MongoDB, BigAutoField for other databases
if USE_MONGODB:
    DEFAULT_AUTO_FIELD = 'django_mongodb_backend.fields.ObjectIdAutoField'
else:
    DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 86400

# Passkeys / WebAuthn Configuration
def get_fido_server_id(request=None):
    """鍔ㄦ€佽幏鍙朏IDO Server ID锛圧P ID锛夛紝涓庡綋鍓嶈闂煙鍚嶄繚鎸佷竴鑷淬€?""
    host = None

    # 浼樺厛浣跨敤瀹為檯璇锋眰鍩熷悕锛堝寘鍚鍙ｆ椂鍘绘帀绔彛锛?
    if request:
        try:
            host = request.get_host()
        except Exception:
            host = None

    # 鍥為€€鍒癆LLOWED_HOSTS閰嶇疆
    if not host:
        host = (ALLOWED_HOSTS[0] if ALLOWED_HOSTS else "localhost")

    # 娓呯悊鍗忚鍜岀鍙?
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split(":", 1)[0].strip()

    # FIDO瑕佹眰RP ID鏄湁鏁堢殑娉ㄥ唽鍩熸垨localhost
    if not host:
        return "localhost"

    return host

FIDO_SERVER_ID = get_fido_server_id
FIDO_SERVER_NAME = "Qexo"
KEY_ATTACHMENT = None  # 鍏佽浠讳綍绫诲瀷鐨勮璇佸櫒锛堝钩鍙版垨璺ㄥ钩鍙帮級

