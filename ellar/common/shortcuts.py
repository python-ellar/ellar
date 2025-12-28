def normalize_path(path: str) -> str:
    """
    Normalizes a path by removing duplicate slashes.
    """
    while "//" in path:
        path = path.replace("//", "/")
    return path
