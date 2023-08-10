from ellar.common import Controller, ModuleRouter, Version, get

mr = ModuleRouter("")


@mr.get("/version")
def default_version():
    return {"version": "default"}


@mr.get("/version")
@Version("1", 1)
def default_version_1():
    return {"version": "v1"}


@mr.get("/version")
@Version("2", 2)
def default_version_2():
    return {"version": "v2"}


@mr.get("/version")
@Version("3", 3)
def default_version_3():
    return {"version": "v3"}


mr_with_version = ModuleRouter("/with-version", version="1")


@mr_with_version.get("/version")
def default_version_case2():
    return {"version": "v1 only"}


@mr_with_version.get("/version")
@Version("2", "3")
def default_version_1_case2():
    return {"version": "v2 and v3 only"}


mr_with_version_list = ModuleRouter("/with-version-list", version=["1", "2"])


@mr_with_version_list.get("/version")
def default_version_case3():
    return {"version": "v1 and v2"}


@Controller("/individual")
class ControllerIndividualVersioning:
    @get("/version")
    def default_version(self):
        return {"version": "default"}

    @get("/version")
    @Version("1", 1)
    def default_version_1(self):
        return {"version": "v1"}

    @get("/version")
    @Version("2", 2)
    def default_version_2(self):
        return {"version": "v2"}

    @get("/version")
    @Version("3", 3)
    def default_version_3(self):
        return {"version": "v3"}


@Controller("/controller-versioning")
@Version("1")
class ControllerVersioning:
    @get("/version")
    def default_version(self):
        return {"version": "default"}

    @get("/version")
    @Version("2")
    def default_version_2(self):
        return {"version": "v2"}


@Version("1", "2")
@Controller("/controller-versioning-list")
class ControllerListVersioning:
    @get("/version")
    def default_version(self):
        return {"version": "default"}

    @get("/version")
    @Version("3")
    def default_version_3(self):
        return {"version": "v3"}
