import base64
import pickle

import pytest

from ellar.testing import Test

from .app import AppModule


class TestMovieController:
    client = Test.create_test_module(modules=[AppModule]).get_test_client()

    def test_get_fast_x_fails_for_anonymous_users(self):
        with self.client as client:
            res = client.get("/movies/")
            assert res.status_code == 401

    @pytest.mark.parametrize(
        "age, status",
        [
            (19, 403),
            (20, 403),
            (21, 200),
            (22, 200),
        ],
    )
    def test_get_fast_x_works(self, age, status):
        with self.client as client:
            auth = base64.b64encode(pickle.dumps(dict(age=age, id=23)))
            res = client.get("/movies/", headers=dict(key=auth))
            assert res.status_code == status

    @pytest.mark.parametrize(
        "roles, path, status",
        [
            (["admin", "staff"], "staff-only", 200),
            (
                [
                    "admin",
                ],
                "staff-only",
                403,
            ),
            (
                [
                    "staff",
                ],
                "staff-only",
                200,
            ),
            (["admin", "staff"], "admin-only", 200),
            (
                [
                    "admin",
                ],
                "admin-only",
                200,
            ),
            (
                [
                    "staff",
                ],
                "admin-only",
                403,
            ),
        ],
    )
    def test_admin_only_works(self, roles, path, status):
        with self.client as client:
            auth = base64.b64encode(pickle.dumps(dict(roles=roles, id=23)))
            res = client.get(f"/article/{path}", headers=dict(key=auth))
            assert res.status_code == status
