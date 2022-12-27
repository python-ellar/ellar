# from ellar.core.exceptions.base import ErrorDetail
#
#
# class TestErrorDetail:
#     def test_eq(self):
#         assert ErrorDetail("msg") == ErrorDetail("msg")
#         assert ErrorDetail("msg", "code") == ErrorDetail("msg", code="code")
#
#         assert ErrorDetail("msg") == "msg"
#         assert ErrorDetail("msg", "code") == "msg"
#
#     def test_ne(self):
#         assert ErrorDetail("msg1") != ErrorDetail("msg2")
#         assert ErrorDetail("msg") != ErrorDetail("msg", code="invalid")
#
#         assert ErrorDetail("msg1") != "msg2"
#         assert ErrorDetail("msg1", "code") != "msg2"
#
#     def test_repr(self):
#         assert repr(
#             ErrorDetail("msg1")
#         ) == "ErrorDetail(string={!r}, code=None)".format("msg1")
#         assert repr(
#             ErrorDetail("msg1", "code")
#         ) == "ErrorDetail(string={!r}, code={!r})".format("msg1", "code")
#
#     def test_str(self):
#         assert str(ErrorDetail("msg1")) == "msg1"
#         assert str(ErrorDetail("msg1", "code")) == "msg1"
#
#     def test_hash(self):
#         assert hash(ErrorDetail("msg")) == hash("msg")
#         assert hash(ErrorDetail("msg", "code")) == hash("msg")
