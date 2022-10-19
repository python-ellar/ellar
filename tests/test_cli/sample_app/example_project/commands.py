from ellar.commands import EllarTyper
from ellar.common import command

db = EllarTyper(name="db")


@db.command()
def create_migration():
    """Creates Database Migration"""
    print("create migration command")


@command()
def whatever_you_want():
    """Whatever you want"""
    print("Whatever you want command")
