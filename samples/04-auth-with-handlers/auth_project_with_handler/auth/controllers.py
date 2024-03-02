"""
Define endpoints routes in python class-based fashion
example:

@Controller("/dogs", tag="Dogs", description="Dogs Resources")
class MyController(ControllerBase):
    @get('/')
    def index(self):
        return {'detail': "Welcome Dog's Resources"}
"""
from ellar.auth import AuthenticationRequired, SkipAuth
from ellar.common import Body, Controller, ControllerBase, get, post
from ellar.openapi import ApiTags

from .services import AuthService


@AuthenticationRequired("JWTAuthentication")
@Controller
@ApiTags(name="Authentication", description="User Authentication Endpoints")
class AuthController(ControllerBase):
    def __init__(self, auth_service: AuthService) -> None:
        self.auth_service = auth_service

    @post("/login")
    @SkipAuth()
    async def sign_in(self, username: Body[str], password: Body[str]):
        return await self.auth_service.sign_in(username=username, password=password)

    @get("/profile")
    async def get_profile(self):
        return self.context.user

    @SkipAuth()
    @post("/refresh")
    async def refresh_token(self, payload: str = Body(embed=True)):
        return await self.auth_service.refresh_token(payload)
