from ellar_sql import model


class User(model.Model):
    id: model.Mapped[int] = model.mapped_column(model.Integer, primary_key=True)
    username: model.Mapped[str] = model.mapped_column(
        model.String, unique=True, nullable=False
    )
    email: model.Mapped[str] = model.mapped_column(model.String)
