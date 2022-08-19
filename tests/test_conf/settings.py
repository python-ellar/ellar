from ellar.core.versioning import UrlPathAPIVersioning

DEBUG: bool = True

SECRET_KEY: str = "your-secret-key-changed"

INJECTOR_AUTO_BIND = True

JINJA_TEMPLATES_OPTIONS = {"auto_reload": DEBUG}

VERSIONING_SCHEME = UrlPathAPIVersioning()
REDIRECT_SLASHES: bool = True
STATIC_MOUNT_PATH: str = "/static-changed"
