from ellar.common import ModuleRouter, version

mr = ModuleRouter("")


@mr.get("/version")
def default_version():
    return dict(version="default")


@mr.get("/version")
@version("1", 1)
def default_version_1():
    return dict(version="v1")


@mr.get("/version")
@version("2", 2)
def default_version_2():
    return dict(version="v2")


@mr.get("/version")
@version("3", 3)
def default_version_3():
    return dict(version="v3")
