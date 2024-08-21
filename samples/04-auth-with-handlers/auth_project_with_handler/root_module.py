from ellar.common import Module
from ellar.core import LazyModuleImport as lazyLoad
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule


@Module(
    modules=[HomeModule, lazyLoad("auth_project_with_handler.auth.module:AuthModule")]
)
class ApplicationModule(ModuleBase):
    pass
