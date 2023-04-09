from ellar.core.conf import ConfigDefaultTypesMixin


class DevelopmentConfig(ConfigDefaultTypesMixin):
    DEBUG = True


class TestingConfig(ConfigDefaultTypesMixin):
    DEBUG = False
