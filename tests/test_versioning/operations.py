from ellar.common import Controller, ModuleRouter, get, version

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


mr_with_version = ModuleRouter("/with-version", version="1")


@mr_with_version.get("/version")
def default_version():
    return dict(version="v1 only")


@mr_with_version.get("/version")
@version("2", "3")
def default_version_1():
    return dict(version="v2 and v3 only")


mr_with_version_list = ModuleRouter("/with-version-list", version=["1", "2"])


@mr_with_version_list.get("/version")
def default_version():
    return dict(version="v1 and v2")


@Controller("/individual")
class ControllerIndividualVersioning:
    @get("/version")
    def default_version(self):
        return dict(version="default")

    @get("/version")
    @version("1", 1)
    def default_version_1(self):
        return dict(version="v1")

    @get("/version")
    @version("2", 2)
    def default_version_2(self):
        return dict(version="v2")

    @get("/version")
    @version("3", 3)
    def default_version_3(self):
        return dict(version="v3")


@Controller("/controller-versioning", version="1")
class ControllerVersioning:
    @get("/version")
    def default_version(self):
        return dict(version="default")

    @get("/version")
    @version("2")
    def default_version_2(self):
        return dict(version="v2")


@Controller("/controller-versioning-list", version=["1", "2"])
class ControllerListVersioning:
    @get("/version")
    def default_version(self):
        return dict(version="default")

    @get("/version")
    @version("3")
    def default_version_3(self):
        return dict(version="v3")
