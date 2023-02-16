import time
from unittest import mock

from pylibmc import Client


class MockClient(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs
        self._cache = {}

    def set(self, *args, **kwargs):
        key, value, _time = args
        with mock.patch.object(Client, "set") as set_mock:
            set_mock.return_value = True
            res = super().set(*args, **kwargs)
        assert set_mock.call_args.args == args
        self._cache[key] = (value, _time)
        return res

    def get(self, *args, **kwargs):
        (key,) = args
        _res = self._cache.get(key)

        if _res and time.time() >= _res[1]:
            del self._cache[key]
            _res = None

        with mock.patch.object(Client, "get") as get_mock:
            get_mock.return_value = _res[0] if _res else None
            res = super().get(*args, **kwargs)
        assert get_mock.call_args.args == args
        return res

    def touch(self, *args, **kwargs):
        key, _time = args
        _res = self._cache.get(key)
        value = False
        if _res:
            self._cache.update({key: (_res[0], _time)})
            value = True

        with mock.patch.object(Client, "touch") as touch_mock:
            touch_mock.return_value = value
            res = super().touch(*args, **kwargs)
        assert touch_mock.call_args.args == args
        return res

    def delete(self, *args, **kwargs):
        (key,) = args
        value = True
        if self._cache.get(key):
            del self._cache[key]
        else:
            value = False
        with mock.patch.object(Client, "delete") as delete_mock:
            delete_mock.return_value = value
            res = super().delete(*args, **kwargs)
        assert delete_mock.call_args.args == args
        return res

    def disconnect_all(self, *args, **kwargs):
        with mock.patch.object(Client, "disconnect_all") as disconnect_all_mock:
            disconnect_all_mock.return_value = None
            res = super().disconnect_all(*args, **kwargs)
        assert disconnect_all_mock.call_args.args == args
        return res
