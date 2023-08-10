"""
Define endpoints routes in python class-based fashion
example:

@Controller("/dogs", tag="Dogs", description="Dogs Resources")
class MyController(ControllerBase):
    @get('/')
    def index(self):
        return {'detail': "Welcome Dog's Resources"}
"""
from ellar.common import Body, Controller, ControllerBase, UseGuards, get, post

from .guards import AllowAnyGuard
from .schemas import UserCredentials
from .services import AuthService


@Controller("/auth")
class AuthController(ControllerBase):
    def __init__(self, auth_service: AuthService) -> None:
        self.auth_service = auth_service

    @post("/sign-in")
    @UseGuards(AllowAnyGuard)
    async def sign_in(self, payload: UserCredentials = Body()):
        return await self.auth_service.sign_in(payload)

    @get("/profile")
    def get_profile(self):
        return self.context.user
