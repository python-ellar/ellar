# **HTML Templating with [Jinja](https://jinja.palletsprojects.com/en/3.0.x/){target='_blank'}**
Jinja2 is a powerful template engine for Python. It can be used in web applications to separate static and dynamic content, 
making it easier to maintain and update the dynamic content. 

In Ellar, a Model-View-Controller (MVC) framework, Jinja2 templates are typically used in the View layer to render dynamic content, 
while the Model and Controller layers handle the data and logic of the application.


## **Installation**
[`Jinja2`](https://jinja.palletsprojects.com/en/3.0.x/){target='_blank'} package is installed alongside with Ellar.


## **Quick overview on jinja2 Usage**
A Jinja2 template is a plain text file that contains dynamic content, represented using Jinja2 syntax. 
Here's an example template that displays a list of items:

```html
<html>
  <body>
    <ul>
      {% for item in items %}
      <li>{{ item }}</li>
      {% endfor %}
    </ul>
  </body>
</html>
```
The `{% for item in items %}` and `{% endfor %`} tags define a loop that iterates over the items list and displays each item as a list item. 
The `{{ item }}` tag inserts the value of the `item` variable into the template.

To render the template, you'll need to use the Jinja2 API in your view function. Here's an example of how you might do this:

```python
# main.py

import uvicorn
from jinja2 import Environment, FileSystemLoader
from ellar.core import Request, AppFactory
from ellar.common import ModuleRouter, HTMLResponse
from pathlib import Path

BASE_DIR = Path(__file__).parent
router = ModuleRouter('/template-testing')

# Also create a templates folder at the main.py root dir. And add template.html into it

@router.get()
def view_function(request: Request):
    # Load the template file
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('template.html')

    # Render the template with some dynamic data
    items = ['apple', 'banana', 'cherry']
    rendered_template = template.render(items=items)

    # Return the rendered template as the response
    return HTMLResponse(rendered_template)

app = AppFactory.create_app(routers=[router], template_folder='templates', base_directory=BASE_DIR)

if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="info")

# visit: http://127.0.0.1:5000/template-testing/
```

This example loads the `template.html` file from the `templates` directory, renders it with the items list, 
and returns the rendered template as the `HTTP` response to the request.

This example also shows manual setup of using `jinja2` in Ellar.


## **Jinja2 usage in Ellar**

In Ellar, the `@render` decorator transforms the route handler response into a Templated Response via an `HTMLResponseModel` with a status code of 200. 
And the route handler is required to return a `dictionary` object which serves as the template's context.

Additionally, each registered `Module` functions as a jinja2 `TemplateLoader` for loading templates, but only when a templates_folder is provided and exists.

### In Controller

In Controllers, the `@render` decorator uses the decorated function name + controller name to generate a path to the template when creating `HTMLResponseModel` to handle the response

For example:
```python
# main.py
import uvicorn
from ellar.common import render, Controller, get
from ellar.core import AppFactory
from pathlib import Path

BASE_DIR = Path(__file__).parent


@Controller()
class TemplateExampleController:
    @get('/')
    @render()
    def index(self):
        return {'name': 'Ellar Template'}

app = AppFactory.create_app(controllers=[TemplateExampleController], template_folder='templates', base_directory=BASE_DIR)

if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="info")

# visit: http://127.0.0.1:5000/templateexample/
```

In this example, the `@render` decorator will create an `HTMLResponseModel` with a template path = `templateexample/index.html`. When the `@render` decorator is
applied to a `Controller` class, it assumes this pattern of resolving the template part. This behavior can be overridden by providing the `template_name` parameter on the `@render` decorator.

For example:
```python
# main.py
import uvicorn
from ellar.common import render, Controller, get
from ellar.core import AppFactory
from pathlib import Path

BASE_DIR = Path(__file__).parent


@Controller()
class TemplateExampleController:
    @get('/')
    @render(template_name='templateexample/list.html')
    async def index(self):
        return {'name': 'Ellar Template'}

app = AppFactory.create_app(
    controllers=[TemplateExampleController], 
    template_folder='templates', 
    base_directory=BASE_DIR
)

if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="info")

# visit: http://127.0.0.1:5000/templateexample
```

### In ModuleRouter
In `ModuleRouter`, `@render` decorators will enforce the `template_name` provision when creating `HTMLResponseModel`.
Ellar does not assume the function name to be equivalent to the template name because it's a wide scope of guess.

A quick example:
```python
# main.py

import uvicorn
from ellar.core import Request, AppFactory
from ellar.common import ModuleRouter, render
from pathlib import Path

BASE_DIR = Path(__file__).parent
router = ModuleRouter('/template-testing')

@router.get()
@render('some-path/template-name.html')
async def index(request: Request):
    return {'name': 'Ellar Template'}
    

app = AppFactory.create_app(routers=[router], template_folder='templates', base_directory=BASE_DIR)

if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="info")
```

!!! info
    `Jinja2` supports async template rendering, however as a general rule we'd recommend that you keep your templates free from logic that invokes database lookups, or other I/O operations.
    Instead, we'd recommend that you ensure that your endpoints perform all I/O, for example, strictly evaluate any database queries within the view and include the final results in the context.'
    - [`Starlette Recommendation`](https://www.starlette.io/templates/#asynchronous-template-rendering){target="_blank"}


## **Jinja2 Configurations**
If there are specific configurations you want to apply to your Jinja2 Environment, you can look at [JINJA_TEMPLATE_OPTIONS](configurations.md#jinja_templates_options){target="_blank"} configuration.

## **Default Jinja Template Context**

Every jinja template in ellar receives two context, `url_for`, `config`, `request` object and other specific context defined to render a template.

- `url_for` is a utility function that helps to resolve path to files and url(reversing url)
- `config` is current application configuration object.
- `request` is current request object.


## **Static Files In Template**

As stated above, you can resolve file paths to static files using `url_for`.

For example:
```html
<head>
    <meta charset="UTF-8">
    <title>Welcome - Ellar ASGI Python Framework</title>
    <link rel="shortcut icon" type="image/x-icon" href="{{ url_for('static', path='img/Icon.svg') }}"/>
    <link rel="stylesheet" href="{{ url_for('static', path='css/bootstrap.min.css') }}">
</head>
```

The `url_for` takes `path` parameter, in the case of `static` files, to match the **directory** and **filename** to be resolved.
This `url_for('static', path='img/Icon.svg')` will search for `img/Icon.svg` in all registered static folders.


### **Reversing Controllers URLs**
It is common to need to generate URLs for specific routes, particularly when returning a redirect response. 
This can be achieved by using the `request.url_for` method in the request object, or in the case of templating, by using the `url_for()` function.

The `request.url_for` method generates a URL based on the current request context, while in template `{{url_for()}}` function generates a URL based on the current routing configuration.
Both of them will generate a URL for a specific route, allowing the server to redirect the client to the correct location.

In controllers, urls are reversed by joining the **controller_name** and **route handler** name like so `controller_name:function_name`.

For example:

```python
# main.py
import uvicorn
from ellar.common import render, Controller, get
from ellar.core import AppFactory, Request
from pathlib import Path

BASE_DIR = Path(__file__).parent


@Controller()
class TemplateExampleController:
    @get('/')
    @render()
    async def index(self, request:Request):
        assert request.url_for('templateexample:index') == 'http://127.0.0.1:5000/templateexample/'
        return {'name': 'Ellar Template'}


app = AppFactory.create_app(
    controllers=[TemplateExampleController],
    template_folder='templates', base_directory=BASE_DIR
)

if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="info")

```

Then in `templates/templateexample/index.html` add the follow:

```html
<html>
  <body>
    <a href="{{url_for('templateexample:index')}}">Index</a>
  </body>
</html>
```

In the example mentioned, `controller_name` is combined with `function_name` to generate the url for the 'index' route.

In the same example, URL parameters can also be passed as keyword arguments to the `url_for` function. For example:

```
url_for('templateexample:index', parameter_a='value1', parameter_b='value2')
```
This would generate a URL that includes the values of `parameter_a` and `parameter_b` as URL parameters, like this :

```
example.com/index/value1/value2
```

For instance:

```python
@get('/{parameter_a}/{parameter_b}')
@render()
async def index(self, parameter_a:str, request:Request):
    assert request.url_for('templateexample:index', parameter_a='ellar') == 'http://127.0.0.1:5000/templateexample/ellar'
    return {'name': 'Ellar Template'}
```

In the example `request.url_for('templateexample:index', parameter_a='ellar')`, 
we can see that the `parameter_a` is used as a keyword argument to satisfy the dependency on the `parameter_a` parameter in the URL being generated.

!!! info
    If the `url_for` function is called with a path that does not exist or with insufficient parameters to resolve an existing URL, 
    it will raise a `starlette.routing.NoMatchFound` exception.

### **Reversing Module Router URLs**

Just like in controller, we can also reverse URLs that belongs to `ModuleRouter`. 

```python
# main.py
import uvicorn
from ellar.common import ModuleRouter
from ellar.core import AppFactory, Request
from pathlib import Path

BASE_DIR = Path(__file__).parent

router = ModuleRouter('/template-reversing', name='users')

@router.get('/{user_id}')
def profile(user_id: str, request:Request):
    profile_url = request.url_for('users:profile', user_id=user_id)
    return profile_url


app = AppFactory.create_app(
    routers=[router],
    template_folder='templates', base_directory=BASE_DIR
)

if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, log_level="info")
```

In the example you mentioned, by adding `name='users'` to the router, it provides a unique way to reverse the routing pattern for the router. 
We can now use the **name** along with the route **function name** in the form of `{name}:{function_name}` to resolve the URL. 
As you can see in `request.url_for('users:profile', user_id=user_id)` the 'users:profile' is the string passed to the `url_for` method. 
This is using the **name** as "users" and the **function name** as "profile" to generate the url based on the routing configuration.
The **user_id** parameter is passed as keyword argument which will be used to construct the URL based on the routing configuration, which should include a parameter for **user_id**

However, If you don't provide a name on the router, you'll have to use only the function name to resolve the URL.
For example, `request.url_for('profile', user_id=user_id)`. In this case, the routing configuration should have a route that match the function name 'profile' and have a parameter for `user_id` in the routing path.

For example:

```python
router = ModuleRouter('/template-reversing')

@router.get('/{user_id}')
def profile(user_id: str, request:Request):
    profile_url = request.url_for('profile', user_id=user_id)
    return profile_url
```

It's worth noting that providing a unique name to a router is useful if you have multiple routes with the same function name, or to make the URL reversing more readable or meaningful.


### **Overriding Reversing URL Function Name**
You can override the `function_name` part of reversing the URL by providing a `name` on the **route method** decorator.
Each route method has an optional name parameter, which, when set, is used in place of the function name when reversing the URL.
For example, you could have the following code:

```python
router = ModuleRouter('/template-reversing', name='users')

@router.get("/profile/{user_id}", name="user_profile")
async def profile(user_id: str, request:Request):
    profile_url = request.url_for('users:user_profile', user_id=user_id)
    return profile_url
```

In this case, when reversing the URL, you would use `request.url_for('users:user_profile', user_id=user_id)`
which will generate `http://127.0.0.1:5000/template-reversing/profile/value_of_user_id` based on routing configuration.

This allows for greater control and readability when reversing URLs, and makes it less prone to error if the function name of the route were to change in the future.


### **Adding template filters and template globals.**
Jinja template filter and global functions can be defined at module level as shown here: [Module Templating Filters](../overview/modules.md#module-templating-filters){target="_blank"}
