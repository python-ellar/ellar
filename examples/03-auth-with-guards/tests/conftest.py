import subprocess

import pytest


@pytest.fixture(scope="session")
def install_ellar_jwt():
    try:
        import ellar_jwt  # noqa
    except ImportError:
        subprocess.Popen(["pip", "install", "ellar_jwt"])
    yield
