from logging.config import fileConfig

from alembic import context
from ellar.app import current_injector
from ellar.threading import run_as_async
from ellar_sql.migrations import SingleDatabaseAlembicEnvMigration
from ellar_sql.services import EllarSQLService

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)  # type:ignore[arg-type]

# logger = logging.getLogger("alembic.env")
# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


@run_as_async
async def main() -> None:
    db_service: EllarSQLService = current_injector.get(EllarSQLService)

    # initialize migration class
    alembic_env_migration = SingleDatabaseAlembicEnvMigration(db_service)

    if context.is_offline_mode():
        alembic_env_migration.run_migrations_offline(context)  # type:ignore[arg-type]
    else:
        await alembic_env_migration.run_migrations_online(context)  # type:ignore[arg-type]


main()
