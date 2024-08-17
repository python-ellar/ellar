import time

from pylibmc import Client


class MockClient(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs
        self._cache = {}

    def set(self, *args, **kwargs):
        key, value, _time = args
        self._cache[key] = (value, _time)
        return True

    def get(self, *args, **kwargs):
        (key,) = args
        _res = self._cache.get(key)

        if _res and time.time() >= _res[1]:
            del self._cache[key]
            _res = None

        return _res[0] if _res else None

    def touch(self, *args, **kwargs):
        key, _time = args
        _res = self._cache.get(key)
        value = False
        if _res:
            self._cache.update({key: (_res[0], _time)})
            value = True
        return value

    def delete(self, *args, **kwargs):
        (key,) = args
        value = True
        if self._cache.get(key):
            del self._cache[key]
        else:
            value = False
        return value

    def disconnect_all(self, *args, **kwargs):
        return None

    def flush_all(self):
        self._cache.clear()

    def _incr_decr_action(self, key: str, delta: int) -> int:
        value, _time = self._cache[key]
        new_value = value + delta
        self._cache.update({key: (new_value, _time)})
        return new_value

    def incr(self, key: str, delta: int = 1, **kwargs) -> int:
        return self._incr_decr_action(key, delta)

    def decr(self, key: str, delta: int = 1, **kwargs) -> int:
        res = self._incr_decr_action(key, delta * -1)
        if res < 0:
            return self._incr_decr_action(key, res * -1)
        return res


class MockSetFailureClient(MockClient):
    def set(self, *args, **kwargs):
        key, value, _time = args
        self._cache[key] = (value, _time)
        return False
