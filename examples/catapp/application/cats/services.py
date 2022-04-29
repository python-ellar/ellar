from ellar.di import injectable


@injectable
class AnotherService:
    x = 15


@injectable
class CatService:
    def __init__(self, another_service: AnotherService) -> None:
        self.another_service = another_service

    def list_cat(self):
        cats = []
        for item in range(1, self.another_service.x):
            cats.append(dict(name=f'cat {item}'))
        return cats

    def update_cat(self, cat_id: int):
        return dict(updated='Okay', cat_id=cat_id, another_service=self.another_service.x)

    def deleted_cat(self, cat_id: int):
        return dict(deleted='Okay', cat_id=cat_id, another_service=self.another_service.x)

    def create_cat(self):
        return dict(created='Okay', another_service=self.another_service.x)
