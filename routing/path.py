from starlette.routing import compile_path, Route, Mount


class PathModifier:
    def __init__(self, operation: Route):
        self.operation = operation
        self.mount_suffix = "/{path:path}" if isinstance(operation, Mount) else ""

    def prefix(self, prefix: str):
        assert prefix.startswith("/")
        path = f"{prefix.rstrip('/')}/{self.operation.path.lstrip('/')}"
        if self.mount_suffix:
            path += self.mount_suffix
        self.operation.path_regex, self.operation.path_format, self.operation.param_convertors = compile_path(path)
        self.operation.path = path

    def suffix(self, suffix: str):
        assert suffix.startswith("/")
        path = f"{self.operation.path.lstrip('/')}/{suffix.rstrip('/')}"
        if self.mount_suffix:
            path += self.mount_suffix
        self.operation.path_regex, self.operation.path_format, self.operation.param_convertors = compile_path(path)
        self.operation.path = path
