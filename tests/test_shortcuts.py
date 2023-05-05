from ellar.common.shortcuts import fail_silently, normalize_path


def test_fail_silently():
    def call_with_args_kwargs(*args, **kwargs):
        return args, kwargs

    def raise_exception():
        raise Exception()

    assert fail_silently(
        call_with_args_kwargs, "someArg1", "someArg2", start=True, end=True
    ) == (("someArg1", "someArg2"), {"end": True, "start": True})
    assert fail_silently(raise_exception) is None


def test_normalize_path():
    path1 = "////somepath//somevalue///somevalue///somevalue"
    path2 = "///somepath//somevalue///somevalue///somevalue"
    path3 = "/somepath/somevalue/somevalue/somevalue"

    assert normalize_path(path1) == path3
    assert normalize_path(path2) == path3
    assert normalize_path(path3) == path3
