try:
    import jinja2

    # @contextfunction renamed to @pass_context in Jinja 3.0, to be removed in 3.1
    if hasattr(jinja2, "pass_context"):
        pass_context = jinja2.pass_context
    else:  # pragma: nocover
        pass_context = jinja2.contextfunction  # type: ignore
except ImportError:  # pragma: nocover
    jinja2 = None  # type: ignore
