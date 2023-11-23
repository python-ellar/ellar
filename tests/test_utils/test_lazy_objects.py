import copy
import pickle
import sys

import pytest
from ellar.common.utils.functional import (
    LazyObject,
    LazyStrImport,
    SimpleLazyObject,
    empty,
)
from ellar.common.utils.importer import ImportFromStringError


class Foo:
    """
    A simple class with just one attribute.
    """

    foo = "bar"

    def __eq__(self, other):
        return self.foo == other.foo


class TestLazyObject:
    def lazy_wrap(self, wrapped_object):
        """
        Wrap the given object into a LazyObject
        """

        class AdHocLazyObject(LazyObject):
            def _setup(self):
                self._wrapped = wrapped_object

        return AdHocLazyObject()

    @pytest.mark.parametrize(
        "attr",
        [
            "__getitem__",
            "__setitem__",
            "__delitem__",
            "__iter__",
            "__len__",
            "__contains__",
        ],
    )
    def test_getattribute(self, attr):
        """
        Proxy methods don't exist on wrapped objects unless they're set.
        """
        foo = Foo()
        obj = self.lazy_wrap(foo)

        assert not hasattr(obj, attr)
        setattr(foo, attr, attr)
        obj_with_attr = self.lazy_wrap(foo)
        assert hasattr(obj, attr)
        assert getattr(obj_with_attr, attr) == attr

    def test_getattr(self):
        obj = self.lazy_wrap(Foo())
        assert obj.foo == "bar"

    def test_delattr_fails(self):
        obj = self.lazy_wrap(Foo())
        with pytest.raises(TypeError):
            del obj._wrapped

    def test_getattr_falsey(self):
        class Thing:
            def __getattr__(self, key):
                return []

        obj = self.lazy_wrap(Thing())
        assert obj.main == []

    def test_setattr(self):
        obj = self.lazy_wrap(Foo())
        obj.foo = "BAR"
        obj.bar = "baz"
        assert obj.foo == "BAR"
        assert obj.bar == "baz"

    def test_setattr2(self):
        # Same as test_setattr but in reversed order
        obj = self.lazy_wrap(Foo())
        obj.bar = "baz"
        obj.foo = "BAR"
        assert obj.foo == "BAR"
        assert obj.bar == "baz"

    def test_delattr(self):
        class A:
            def __init__(self):
                self.foo = "bar"

        obj = self.lazy_wrap(A())
        del obj.foo

        with pytest.raises(AttributeError):
            assert obj.foo

        obj.bar = "baz"
        assert obj.bar == "baz"
        del obj.bar

        with pytest.raises(AttributeError):
            assert obj.bar

    def test_cmp(self):
        obj1 = self.lazy_wrap("foo")
        obj2 = self.lazy_wrap("bar")
        obj3 = self.lazy_wrap("foo")
        assert obj1 == "foo"
        assert obj1 == obj3
        assert obj1 != obj2
        assert obj1 != "bar"

    def test_lt(self):
        obj1 = self.lazy_wrap(1)
        obj2 = self.lazy_wrap(2)
        assert obj1 < obj2

    def test_gt(self):
        obj1 = self.lazy_wrap(1)
        obj2 = self.lazy_wrap(2)
        assert obj2 > obj1

    def test_bytes(self):
        obj = self.lazy_wrap(b"foo")
        assert bytes(obj) == b"foo"

    def test_text(self):
        obj = self.lazy_wrap("foo")
        assert str(obj) == "foo"

    def test_bool(self):
        # Refs #21840
        for f in [False, 0, (), {}, [], None, set()]:
            assert not self.lazy_wrap(f)
        for t in [True, 1, (1,), {1: 2}, [1], object(), {1}]:
            assert t

    def test_dir(self):
        obj = self.lazy_wrap("foo")
        assert dir(obj) == dir("foo")

    def test_len(self):
        for seq in ["asd", [1, 2, 3], {"a": 1, "b": 2, "c": 3}]:
            obj = self.lazy_wrap(seq)
            assert len(obj) == 3

    def test_class(self):
        assert isinstance(self.lazy_wrap(42), int)

        class Bar(Foo):
            pass

        assert isinstance(self.lazy_wrap(Bar()), Foo)

    def test_hash(self):
        obj = self.lazy_wrap("foo")
        d = {obj: "bar"}
        assert "foo" in d
        assert d["foo"] == "bar"

    def test_contains(self):
        test_data = [
            ("c", "abcde"),
            (2, [1, 2, 3]),
            ("a", {"a": 1, "b": 2, "c": 3}),
            (2, {1, 2, 3}),
        ]
        for needle, haystack in test_data:
            assert needle in self.lazy_wrap(haystack)

        # __contains__ doesn't work when the haystack is a string and the
        # needle a LazyObject.
        for _ in test_data[1:]:
            assert self.lazy_wrap(needle) in haystack
            assert self.lazy_wrap(needle) in self.lazy_wrap(haystack)

    def test_getitem(self):
        obj_list = self.lazy_wrap([1, 2, 3])
        obj_dict = self.lazy_wrap({"a": 1, "b": 2, "c": 3})

        assert obj_list[0] == 1
        assert obj_list[-1] == 3
        assert obj_list[1:2] == [2]

        assert obj_dict["b"] == 2

        with pytest.raises(IndexError):
            obj_list[3]

        with pytest.raises(KeyError):
            obj_dict["f"]

    def test_setitem(self):
        obj_list = self.lazy_wrap([1, 2, 3])
        obj_dict = self.lazy_wrap({"a": 1, "b": 2, "c": 3})

        obj_list[0] = 100
        assert obj_list == [100, 2, 3]
        obj_list[1:2] = [200, 300, 400]
        assert obj_list == [100, 200, 300, 400, 3]

        obj_dict["a"] = 100
        obj_dict["d"] = 400
        assert obj_dict == {"a": 100, "b": 2, "c": 3, "d": 400}

    def test_delitem(self):
        obj_list = self.lazy_wrap([1, 2, 3])
        obj_dict = self.lazy_wrap({"a": 1, "b": 2, "c": 3})

        del obj_list[-1]
        del obj_dict["c"]
        assert obj_list == [1, 2]
        assert obj_dict == {"a": 1, "b": 2}

        with pytest.raises(IndexError):
            del obj_list[3]

        with pytest.raises(KeyError):
            del obj_dict["f"]

    def test_iter(self):
        # Tests whether an object's custom `__iter__` method is being
        # used when iterating over it.

        class IterObject:
            def __init__(self, values):
                self.values = values

            def __iter__(self):
                return iter(self.values)

        original_list = ["test", "123"]
        assert list(self.lazy_wrap(IterObject(original_list))) == original_list

    def test_pickle(self):
        # See ticket #16563
        obj = self.lazy_wrap(Foo())
        obj.bar = "baz"
        pickled = pickle.dumps(obj)
        unpickled = pickle.loads(pickled)
        assert isinstance(unpickled, Foo)
        assert unpickled == obj
        assert unpickled.foo == obj.foo
        assert unpickled.bar == obj.bar

    # Test copying lazy objects wrapping both builtin types and user-defined
    # classes since a lot of the relevant code does __dict__ manipulation and
    # builtin types don't have __dict__.

    def test_copy_list(self):
        # Copying a list works and returns the correct objects.
        lst = [1, 2, 3]

        obj = self.lazy_wrap(lst)
        len(lst)  # forces evaluation
        obj2 = copy.copy(obj)

        assert obj is not obj2
        assert isinstance(obj2, list)
        assert obj2 == [1, 2, 3]

    def test_copy_list_no_evaluation(self):
        # Copying a list doesn't force evaluation.
        lst = [1, 2, 3]

        obj = self.lazy_wrap(lst)
        obj2 = copy.copy(obj)

        assert obj is not obj2
        assert obj._wrapped is empty
        assert obj2._wrapped is empty

    def test_copy_class(self):
        # Copying a class works and returns the correct objects.
        foo = Foo()

        obj = self.lazy_wrap(foo)
        str(foo)  # forces evaluation
        obj2 = copy.copy(obj)

        assert obj is not obj2
        assert isinstance(obj2, Foo)
        assert obj2 == Foo()

    def test_copy_class_no_evaluation(self):
        # Copying a class doesn't force evaluation.
        foo = Foo()

        obj = self.lazy_wrap(foo)
        obj2 = copy.copy(obj)

        assert obj is not obj2
        assert obj._wrapped is empty
        assert obj2._wrapped is empty

    def test_deepcopy_list(self):
        # Deep copying a list works and returns the correct objects.
        lst = [1, 2, 3]

        obj = self.lazy_wrap(lst)
        len(lst)  # forces evaluation
        obj2 = copy.deepcopy(obj)

        assert obj is not obj2
        assert isinstance(obj2, list)
        assert obj2 == [1, 2, 3]

    def test_deepcopy_list_no_evaluation(self):
        # Deep copying doesn't force evaluation.
        lst = [1, 2, 3]

        obj = self.lazy_wrap(lst)
        obj2 = copy.deepcopy(obj)

        assert obj is not obj2
        assert obj._wrapped is empty
        assert obj2._wrapped is empty

    def test_deepcopy_class(self):
        # Deep copying a class works and returns the correct objects.
        foo = Foo()

        obj = self.lazy_wrap(foo)
        str(foo)  # forces evaluation
        obj2 = copy.deepcopy(obj)

        assert obj is not obj2
        assert isinstance(obj2, Foo)
        assert obj2 == Foo()

    def test_deepcopy_class_no_evaluation(self):
        # Deep copying doesn't force evaluation.
        foo = Foo()

        obj = self.lazy_wrap(foo)
        obj2 = copy.deepcopy(obj)

        assert obj is not obj2
        assert obj._wrapped is empty
        assert obj2._wrapped is empty


class TestSimpleLazyObject:
    # By inheriting from LazyObjectTestCase and redefining the lazy_wrap()
    # method which all testcases use, we get to make sure all behaviors
    # tested in the parent testcase also apply to SimpleLazyObject.
    def lazy_wrap(self, wrapped_object):
        return SimpleLazyObject(lambda: wrapped_object)

    def test_repr(self):
        # First, for an unevaluated SimpleLazyObject
        obj = self.lazy_wrap(42)
        # __repr__ contains __repr__ of setup function and does not evaluate
        # the SimpleLazyObject
        assert "<SimpleLazyObject:" in repr(obj)
        assert obj._wrapped is empty  # make sure evaluation hasn't been triggered

        assert obj == 42  # evaluate the lazy object
        assert isinstance(obj._wrapped, int)
        assert repr(obj) == "<SimpleLazyObject: 42>"

    def test_add(self):
        obj1 = self.lazy_wrap(1)
        assert obj1 + 1 == 2
        obj2 = self.lazy_wrap(2)
        assert obj2 + obj1 == 3
        assert obj1 + obj2 == 3

    def test_radd(self):
        obj1 = self.lazy_wrap(1)
        assert 1 + obj1 == 2

    def test_trace(self):
        old_trace_func = sys.gettrace()
        try:

            def trace_func(frame, event, arg):
                assert frame.f_locals["self"].__class__
                if old_trace_func is not None:
                    old_trace_func(frame, event, arg)

            sys.settrace(trace_func)
            self.lazy_wrap(None)
        finally:
            sys.settrace(old_trace_func)

    def test_none(self):
        i = [0]

        def f():
            i[0] += 1
            return None

        x = SimpleLazyObject(f)
        assert str(x) == "None"
        assert i == [1]
        assert str(x) == "None"
        assert i == [1]

    def test_dict(self):
        lazydict = SimpleLazyObject(lambda: {"one": 1})
        assert lazydict["one"] == 1
        lazydict["one"] = -1
        assert lazydict["one"] == -1
        assert "one" in lazydict
        assert "two" != lazydict
        assert len(lazydict) == 1
        del lazydict["one"]
        with pytest.raises(KeyError):
            lazydict["one"]

    def test_list_set(self):
        lazy_list = SimpleLazyObject(lambda: [1, 2, 3, 4, 5])
        lazy_set = SimpleLazyObject(lambda: {1, 2, 3, 4})
        assert 1 in lazy_list
        assert 1 in lazy_set
        assert 6 not in lazy_list
        assert 6 not in lazy_set
        assert len(lazy_list) == 5
        assert len(lazy_set) == 4


class BaseBaz:
    """
    A base class with a funky __reduce__ method, meant to simulate the
    __reduce__ method of Model, which sets self._django_version.
    """

    def __init__(self):
        self.baz = "wrong"

    def __reduce__(self):
        self.baz = "right"
        return super().__reduce__()

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        for attr in ["bar", "baz", "quux"]:
            if hasattr(self, attr) != hasattr(other, attr):
                return False
            elif getattr(self, attr, None) != getattr(other, attr, None):
                return False
        return True


class Baz(BaseBaz):
    """
    A class that inherits from BaseBaz and has its own __reduce_ex__ method.
    """

    def __init__(self, bar):
        self.bar = bar
        super().__init__()

    def __reduce_ex__(self, proto):
        self.quux = "quux"
        return super().__reduce_ex__(proto)


class BazProxy(Baz):
    """
    A class that acts as a proxy for Baz. It does some scary mucking about with
    dicts, which simulates some crazy things that people might do with
    e.g. proxy models.
    """

    def __init__(self, baz):
        self.__dict__ = baz.__dict__
        self._baz = baz
        # Grandparent super
        super(BaseBaz, self).__init__()


class TestSimpleLazyObjectPickle:
    """
    Regression test for pickling a SimpleLazyObject wrapping a model (#25389).
    Also covers other classes with a custom __reduce__ method.
    """

    def test_pickle_with_reduce(self):
        """
        Test in a fairly synthetic setting.
        """
        # Test every pickle protocol available
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            lazy_objs = [
                SimpleLazyObject(lambda: BaseBaz()),
                SimpleLazyObject(lambda: Baz(1)),
                SimpleLazyObject(lambda: BazProxy(Baz(2))),
            ]
            for obj in lazy_objs:
                pickled = pickle.dumps(obj, protocol)
                unpickled = pickle.loads(pickled)
                assert unpickled == obj
                assert unpickled.baz == "right"


class TestLazyClassImport:
    """Test lazy import"""


def test_lazy_str_import_works():
    lazy_import = LazyStrImport(
        "tests.test_utils.test_lazy_objects:TestLazyClassImport"
    )
    instance = lazy_import()
    assert isinstance(instance, TestLazyClassImport)

    with pytest.raises(ImportFromStringError):
        lazy_import = LazyStrImport("tests.test_lazy_import:InvalidLazyClassImport")
        lazy_import()
