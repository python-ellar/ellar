import ellar_cli.click as click
from ellar.app import current_injector
from ellar_sql import EllarSQLService

from db_learning.models import User


@click.command("seed")
@click.with_app_context
def seed_user():
    db_service = current_injector.get(EllarSQLService)
    session = db_service.session_factory()

    for i in range(300):
        session.add(
            User(username=f"username-{i + 1}", email=f"user{i + 1}doe@example.com")
        )

    session.commit()
    db_service.session_factory.remove()
