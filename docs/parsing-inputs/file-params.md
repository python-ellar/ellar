# File uploads

Handling files are no different from other parameters.
You can define files to be uploaded by using `File`.

!!! info
    To receive uploaded files, first install <a href="https://andrew-d.github.io/python-multipart/" class="external-link" target="_blank">`python-multipart`</a>.

    E.g. `pip install python-multipart`.

    This is because uploaded files are sent as "form data".

## Import `File`

First import `File` from `ellar.common` module

## Define `File` parameters

Create file parameters the same way you would for `Body` or `Form`:

```python
# project_name/apps/items/controllers.py
from ellar.common import File
from ellar.common import Controller, post
from ellar.core import ControllerBase


@Controller
class ItemsController(ControllerBase):
    @post("/files/")
    async def create_file(self, file: bytes = File()):
        return {"file_size": len(file)}
```

The files will be uploaded as "form data".

If you declare the type of your *path operation function* parameter as `bytes`, **Ellar** will read the file for you and you will receive the contents as `bytes`.

Have in mind that this means that the whole contents will be stored in memory. This will work well for small files.

But there are several cases in which you might benefit from using `UploadFile`.

## `File` parameters with `UploadFile`

Define a `File` parameter with a type of `UploadFile`:

```python
# project_name/apps/items/controllers.py
from ellar.common import File, UploadFile
from ellar.common import Controller, post
from ellar.core import ControllerBase


@Controller
class ItemsController(ControllerBase):
    @post("/files/")
    async def create_file(self, file: bytes = File()):
        return {"file_size": len(file)}
    
    
    @post("/uploadfile/")
    async def create_upload_file(self, file: UploadFile = File()):
        return {"filename": file.filename}
```

Using `UploadFile` has several advantages over `bytes`:

* It uses a "spooled" file:
    * A file stored in memory up to a maximum size limit, and after passing this limit it will be stored in disk.
* This means that it will work well for large files like images, videos, large binaries, etc. without consuming all the memory.
* You can get metadata from the uploaded file.
* It has a <a href="https://docs.python.org/3/glossary.html#term-file-like-object" class="external-link" target="_blank">file-like</a> `async` interface.
* It exposes an actual Python <a href="https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile" class="external-link" target="_blank">`SpooledTemporaryFile`</a> object that you can pass directly to other libraries that expect a file-like object.

### `UploadFile`

`UploadFile` has the following attributes:

* `filename`: A `str` with the original file name that was uploaded (e.g. `myimage.jpg`).
* `content_type`: A `str` with the content type (MIME type / media type) (e.g. `image/jpeg`).
* `file`: A <a href="https://docs.python.org/3/library/tempfile.html#tempfile.SpooledTemporaryFile" class="external-link" target="_blank">`SpooledTemporaryFile`</a> (a <a href="https://docs.python.org/3/glossary.html#term-file-like-object" class="external-link" target="_blank">file-like</a> object). This is the actual Python file that you can pass directly to other functions or libraries that expect a "file-like" object.

`UploadFile` has the following `async` methods. They all call the corresponding file methods underneath (using the internal `SpooledTemporaryFile`).

* `write(data)`: Writes `data` (`str` or `bytes`) to the file.
* `read(size)`: Reads `size` (`int`) bytes/characters of the file.
* `seek(offset)`: Goes to the byte position `offset` (`int`) in the file.
    * E.g., `await myfile.seek(0)` would go to the start of the file.
    * This is especially useful if you run `await myfile.read()` once and then need to read the contents again.
* `close()`: Closes the file.

As all these methods are `async` methods, you need to "await" them.

For example, inside an `async` *path operation function* you can get the contents with:

```python
contents = await myfile.read()
```

If you are inside of a normal `def` *path operation function*, you can access the `UploadFile.file` directly, for example:

```python
contents = myfile.file.read()
```

!!! note "`async` Technical Details"
    When you use the `async` methods, **Ellar** runs the file methods in a threadpool and awaits for them.

!!! note "Starlette Technical Details"
    **Ellar**'s `UploadFile` inherits directly from **Starlette**'s `UploadFile`, but adds some necessary parts to make it compatible with **Pydantic** and the other parts of Ellar.


## Uploading array of files

To **upload several files** at the same time, just declare a `List` of `UploadFile`:


```python
# project_name/apps/items/controllers.py
from typing import List
from ellar.common import File, UploadFile
from ellar.common import Controller, post
from ellar.core import ControllerBase


@Controller
class ItemsController(ControllerBase):
    @post("/upload-many")
    def upload_many(self, files: List[UploadFile] = File()):
        return [f.filename for f in files]
```

## Uploading files with extra fields

Note: HTTP protocol does not allow you to send files in application/json format by default (unless you encode it somehow to JSON on client side)

To send files along with some extra attributes you need to send bodies in multipart/form-data encoding. You can do it by simply marking fields with `Form`:

```python
# project_name/apps/items/controllers.py

from ellar.serializer import Serializer
from ellar.common import Controller, Form, File, UploadFile, post
from ellar.core import ControllerBase
from datetime import date


class UserDetails(Serializer):
    first_name: str
    last_name: str
    birthdate: date


@Controller
class ItemsController(ControllerBase):
    @post('/user')
    def create_user(self, details: UserDetails = Form(), file: UploadFile = File()):
        return [details.dict(), file.filename]

```

Note: in this case all fields should be sent as form fields

You can as well send payload in single field as JSON - just remove the Form mark from:

```python
# project_name/apps/items/controllers.py

from ellar.serializer import Serializer
from ellar.common import Controller, File, UploadFile, post
from ellar.core import ControllerBase
from datetime import date


class UserDetails(Serializer):
    first_name: str
    last_name: str
    birthdate: date


@Controller
class ItemsController(ControllerBase):
    @post('/user')
    def create_user(self, details: UserDetails, file: UploadFile = File()):
        return [details.dict(), file.filename]

```

this will expect from client side to send data as multipart/form-data with 2 fields:
  
  - details: Json as string
  - file: file
