from ellar.common import ModuleRouter, version

mr = ModuleRouter("")


@mr.Get("/version")
def default_version():
    return dict(version="default")


@mr.Get("/version")
@version("1", 1)
def default_version():
    return dict(version="v1")


@version("2", 2)
@mr.Get("/version")
def default_version():
    return dict(version="v2")


@mr.Get("/version")
@version("3", 3)
def default_version():
    return dict(version="v3")
