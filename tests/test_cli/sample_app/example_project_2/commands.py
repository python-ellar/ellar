from ellar.commands import EllarTyper
from ellar.common import command

db = EllarTyper(name="db")


@db.command()
def create_migration():
    """Creates Database Migration"""
    print("create migration command from example_project_2")


@command()
def whatever_you_want():
    """Whatever you want"""
    print("Whatever you want command from example_project_2")


@command()
def project_2_command():
    """Project 2 Custom Command"""
    print("Project 2 Custom Command from example_project_2")
