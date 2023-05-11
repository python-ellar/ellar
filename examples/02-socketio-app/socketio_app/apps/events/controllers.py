"""
Define endpoints routes in python class-based fashion
example:

@Controller("/dogs", tag="Dogs", description="Dogs Resources")
class MyController(ControllerBase):
    @get('/')
    def index(self):
        return {'detail': "Welcome Dog's Resources"}
"""
from ellar.common import ControllerBase, Controller, render, get

@Controller('/events')
class EventsController(ControllerBase):
    @get('/')
    @render()
    def index(self):
        return {}
