from ellar.core import TestClientFactory
from ellar.samples.modules import HomeModule

tm = TestClientFactory.create_test_module_from_module(HomeModule)
client = tm.get_client()


def test_home_module_works():
    res = client.get("/")
    assert res.status_code == 200
    assert res.template.name == "home/index.html"
    assert res.context["docs_url"] == "https://eadwincode.github.io/ellar/"
    assert res.context["git_hub"] == "https://github.com/eadwincode/ellar"
