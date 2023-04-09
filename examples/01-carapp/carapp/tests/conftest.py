import os
from ellar.constants import ELLAR_CONFIG_MODULE

os.environ.setdefault(ELLAR_CONFIG_MODULE,  'carapp.config:TestingConfig')
