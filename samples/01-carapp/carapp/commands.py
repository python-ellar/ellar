from ellar_cli.click import Group, command

db = Group(name="db")


@db.command()
def create_migration():
    """Creates Database Migration"""


@command()
def whatever_you_want():
    """Whatever you want"""
