# **Application Context**

In Ellar, reaching the application instance without have circular import error is nearly impossible, 
hence application context exist to solve this problem.
Application context makes the application object available through a context during request, 
some CLI commands and other activities that invoked the context manually. 

There are three proxies variables exposed by application context:

- **current_app**: references current running application instance
- **current_injector**: refer to current running application DI container
- **current_config**: refer to current running application configuration

One of the three or all would be needed for reference when designing your application.

For example:
```python
import ellar_cli.click as click
from ellar.app import current_injector, config
from ellar.core import Config


@click.command()
@click.argument('name')
def my_command(name: str):
    my_service = current_injector.get
```
