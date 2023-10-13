from ellar.common import IHostContext, Inject, Module, ModuleRouter, middleware
from ellar.core import ModuleBase
from ellar.testing import Test
from starlette.background import BackgroundTask, BackgroundTasks

router = ModuleRouter()
background_task_results = {}


async def background_task_1():
    background_task_results["background_task_1"] = "Called"


def background_task_2():
    background_task_results["background_task_2"] = "Called"


@Module(routers=[router])
class ModuleSample(ModuleBase):
    @classmethod
    def background_task_3(cls):
        background_task_results["background_task_3"] = "Called"

    @middleware()
    async def some_middleware(cls, context: IHostContext, call_next):
        res = context.switch_to_http_connection().get_response()
        res.background = BackgroundTask(cls.background_task_3)
        await call_next()


@router.get("/background-task")
def check_background_task_working(tasks: Inject[BackgroundTasks]):
    tasks.add_task(background_task_2)
    tasks.add_task(background_task_1)

    return "testing background tasks"


@router.get("/background-task-with-string-annotation")
def check_background_task_working_with_string_annotation(
    tasks_string_annotation: Inject["BackgroundTasks"],
):
    tasks_string_annotation.add_task(background_task_2)
    tasks_string_annotation.add_task(background_task_1)

    return "testing background tasks"


def test_background_tasks_works():
    global background_task_results
    background_task_results = {}

    client = Test.create_test_module(routers=[router]).get_test_client()
    res = client.get("/background-task")
    assert res.status_code == 200
    assert res.text == '"testing background tasks"'
    assert background_task_results == {
        "background_task_1": "Called",
        "background_task_2": "Called",
    }


def test_any_existing_background_task():
    global background_task_results
    background_task_results = {}

    client = Test.create_test_module(modules=[ModuleSample]).get_test_client()
    res = client.get("/background-task")
    assert res.status_code == 200
    assert res.text == '"testing background tasks"'

    assert background_task_results == {
        "background_task_1": "Called",
        "background_task_2": "Called",
        "background_task_3": "Called",
    }


def test_any_existing_background_task_with_string_annotation():
    global background_task_results
    background_task_results = {}

    client = Test.create_test_module(modules=[ModuleSample]).get_test_client()
    res = client.get("/background-task-with-string-annotation")
    assert res.status_code == 200
    assert res.text == '"testing background tasks"'

    assert background_task_results == {
        "background_task_1": "Called",
        "background_task_2": "Called",
        "background_task_3": "Called",
    }
