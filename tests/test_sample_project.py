from ellar.samples.modules import HomeModule
from ellar.testing import Test

tm = Test.create_test_module(modules=[HomeModule])
client = tm.get_test_client()


def test_home_module_works():
    res = client.get("/")
    assert res.status_code == 200
    assert res.template.name == "home/index.html"
    assert res.context["docs_url"] == "https://python-ellar.github.io/ellar/"
    assert res.context["git_hub"] == "https://github.com/python-ellar/ellar"
