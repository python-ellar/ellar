import os

from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar_cli.main import create_ellar_cli

if __name__ == "__main__":
    os.environ.setdefault(
        ELLAR_CONFIG_MODULE, "ellar_and_django_orm.config:DevelopmentConfig"
    )

    # initialize Commandline program
    cli = create_ellar_cli("ellar_and_django_orm.server:bootstrapper")
    # start commandline execution
    ss = cli(prog_name="Ellar Web Framework CLI")
