## CATAPP Application

This is just a quick demonstration of ellar web framework. Modifications will be made on this project as the Ellar project 
evolves to become better.

### Start Development Server
Currently, to start development server, you need to tell uvicorn where the app
instance is.
So, run the command below:

```bash
uvicorn catapp.server.app --reload
```

Once the server is up, you can visit [SwaggerDoc](http://localhost:8000/docs#) or [ReDocs](http://localhost:8000/redoc#)
