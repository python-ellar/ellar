# **Versioning**
Versioning allows for the existence of multiple versions of controllers or individual routes within the same application, 
which can be useful when making changes that may break previous versions. 
This allows developers to support older versions of the application while still making necessary updates.

There are 4 types of versioning that are supported:

- [`URL Versioning`](#url-versioning): The version will be passed within the **URL** of the request 
- [`Header Versioning`](#header-versioning): A custom request **header** will specify the version
- [`Query Versioning`](#query-versioning): A custom request **query** will specify the version
- [`Host Versioning`](#host-versioning): The version will be part of the request **client host**

## **URL Versioning**
This scheme requires the client to specify the version as part of the URL path.
```
GET /v1/receipes/ HTTP/1.1
Host: example.com
Accept: application/json
```

To enable **URL Versioning** for your application, do the following:
```python
# project_name/server.py
import os
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.core.factory import AppFactory
from ellar.core.versioning import VersioningSchemes
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "dialerai.config:DevelopmentConfig"
    ),
    global_guards=[]
)
application.enable_versioning(VersioningSchemes.URL, version_parameter='v', default_version=None)
```
The URL path will be parsed with the provided `version_parameter`, `v`, to determine specified version. 
For example, `https://example.com/v1/route`, will resolve to `version='1'` and `https://example.com/v3/route`, will resolve to `version='3'`.

If version is not specified in the URL, the `default_version` will be used. Which in this case is `None`. 

## **Header Versioning**
This scheme requires the client to specify the version as part of the media type in the `Accept` header. 
The version is included as a media type parameter, that supplements the main media type.

Here's an example HTTP request using accept header versioning style.
```
GET /receipes/ HTTP/1.1
Host: example.com
Accept: application/json; version=1
```

To enable **Header Versioning** for your application, do the following:
```python
# project_name/server.py
import os
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.core.factory import AppFactory
from ellar.core.versioning import VersioningSchemes
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "dialerai.config:DevelopmentConfig"
    ),
    global_guards=[]
)
application.enable_versioning(
    VersioningSchemes.HEADER, 
    header_parameter='accept', 
    version_parameter='version', 
    default_version=None
)
```
During request handling, request header `accept` value will be parsed to read the version value. A header `accept: application/json; version=2` will resolve to `version='2'`

#### **Using Custom Header**
We can also use a custom header asides `accept`. for example:
```
GET /receipes/ HTTP/1.1
Host: example.com
X-Custom-Header: version=2
```

And then we enable it with the code below:
```python
# project_name/server.py
...
application.enable_versioning(
    VersioningSchemes.HEADER, 
    header_parameter='x-custom-header', 
    version_parameter='version_header', 
    default_version=None
)
```
The header property, `x-custom-header`, will be the name of the header that will contain the version of the request. 
And the value follow the format `[version_parameter]=version-number;`, for example: `headers={'x-custom-header': 'version_header=3'}` will resolve to `version='3'`.

## **Query Versioning**
This scheme is a simple style that includes the version as a query parameter in the URL. For example:
```
GET /receipes?version=2 HTTP/1.1
Host: example.com
Accept: application/json
```

To enable **Query Versioning** for your application, do the following:
```python
# project_name/server.py
import os
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.core.factory import AppFactory
from ellar.core.versioning import VersioningSchemes
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "dialerai.config:DevelopmentConfig"
    ),
    global_guards=[]
)
application.enable_versioning(
    VersioningSchemes.QUERY, 
    version_parameter='version', 
    default_version=None
)
```

## **Host Versioning**
The hostname versioning scheme requires the client to specify the requested version as part of the hostname in the URL.

For example the following is an HTTP request to the `http://v1.example.com/receipes/` URL:
```
GET /receipes/ HTTP/1.1
Host: v1.example.com
Accept: application/json
```

To enable **Host Versioning** for your application, do the following:
```python
# project_name/server.py
import os
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.core.factory import AppFactory
from ellar.core.versioning import VersioningSchemes
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "dialerai.config:DevelopmentConfig"
    ),
    global_guards=[]
)
application.enable_versioning(
    VersioningSchemes.HOST, 
    version_parameter='v', 
    default_version=None
)
```
By default, this implementation expects the hostname to match this simple regular expression:
```regexp
^([a-zA-Z0-9]+)\.[a-zA-Z0-9]+\.[a-zA-Z0-9]+$
```

Note that the first group is enclosed in brackets, indicating that this is the matched portion of the hostname.

The `HostNameVersioning` scheme can be awkward to use in debug mode as you will typically be accessing a raw IP address such as 127.0.0.1. 
There are various online tutorials on how to [access localhost with a custom subdomain](https://reinteractive.net/posts/199-developing-and-testing-rails-applications-with-subdomains){target="_blank"} which you may find helpful in this case.

Hostname based versioning can be particularly useful if you have requirements to route incoming requests to different servers based on the version, as you can configure different DNS records for different API versions.

## **Controller Versions**
A version can be applied to a controller by using `Version` decorator from `ellar.common` package.

To add a version to a controller do the following:
```python
from ellar.common import Controller, Version

@Controller('/example')
@Version('1')
class ExampleControllerV1:
    pass

```
## **Route Versions**
A version can be applied to an individual route. This version will override any other version that would effect the route, such as the Controller Version.

To add a version to an individual route do the following:

```python
from ellar.common import Controller, Version, get

@Controller('/example')
class ExampleController:
    @Version('1')
    @get('/items')
    async def get_items_v1(self):
        return 'This action returns all items for version 1'
    
    @get('/items')
    @Version('2')
    async def get_items_v2(self):
        return 'This action returns all items for version 2'

```
## **Multiple Versions**
Multiple versions can be applied to a controller or route. To use multiple versions, you would set the version to be an Array.

To add multiple versions do the following:
```python
from ellar.common import Controller, Version, get

@Controller('/example')
@Version('1', '2')
class ExampleControllerV1AndV2:
    @get('/items')
    async def get_items(self):
        return 'This action returns all items for version 1 & 2'

```
