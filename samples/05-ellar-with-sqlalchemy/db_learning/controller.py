import ellar.common as ecm
from ellar.pydantic import EmailStr
from ellar_sql import get_or_404, model

from .models import User


@ecm.Controller
class UsersController(ecm.ControllerBase):
    @ecm.post("/")
    def create_user(
        self,
        username: ecm.Body[str],
        email: ecm.Body[EmailStr],
        session: ecm.Inject[model.Session],
    ):
        user = User(username=username, email=email)

        session.add(user)
        session.commit()
        session.refresh(user)

        return user.dict()

    @ecm.get("/{user_id:int}")
    async def user_by_id(self, user_id: int):
        user: User = await get_or_404(User, user_id)
        return user.dict()

    @ecm.get("/")
    async def user_list(self, session: ecm.Inject[model.Session]):
        stmt = model.select(User)
        rows = session.execute(stmt.offset(0).limit(100)).scalars()
        return [row.dict() for row in rows]

    @ecm.get("/{user_id:int}")
    async def user_delete(self, user_id: int, session: ecm.Inject[model.Session]):
        user = get_or_404(User, user_id)
        session.delete(user)
        return {"detail": f"User id={user_id} Deleted successfully"}
