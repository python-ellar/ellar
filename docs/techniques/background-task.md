# **Background Tasks**

Background tasks are tasks attached to a response and processed after a response has been sent to the client. An example of 
this kind of task could be email notifications sent after performing an action.

## **Adding BackgroundTask**
In Ellar, you can access the **response** object and set a `background` parameter.
```python
from starlette.background import BackgroundTask
from ellar.common import ModuleRouter, Response

router = ModuleRouter('/background-test')

async def send_welcome_email(email):
    print(f'Send Welcome Email Task Called with {email}')

@router.post('/signup')
def sign_up(username: str, password: str, email: str, res:Response):
    res.background = BackgroundTask(send_welcome_email, email=email)
    return {'status': 'Signup successful'}
```
In above construct, we created `BackgroundTask` around `send_welcome_email` function and passed to it some `*args/**kwargs `required to invoke the wrapped function.
After the response has been sent to the client, the background function[`send_welcome_email`] will be called and there will be a print on the server log.

## **Using BackgroundTasks**
`BackgroundTasks` is another class from Starlette useful for adding multiple background tasks to a response. 
Unlike the previous construct, `BackgroundTasks` can be injected into your route function by type annotation.

For example:
```python
from starlette.background import BackgroundTasks
from ellar.common import ModuleRouter

router = ModuleRouter('/background-test')

def another_background_task(parameter):
    print(f'Another Background task called with "{parameter}"')
    
async def send_welcome_email(email):
    print(f'Send Welcome Email Task Called with "{email}"')

@router.post('/signup')
def sign_up(username: str, password: str, email: str, tasks: BackgroundTasks):
    tasks.add_task(send_welcome_email, email=email)
    tasks.add_task(another_background_task, 'another_background_task parameter')
    return {'status': 'Signup successful'}
```

During request response cycle, `BackgroundTasks` will be resolved made available to the route handler function.

!!! hint
    The tasks are executed in order. In case one of the tasks raises an exception, the following tasks will not get the opportunity to be executed.
