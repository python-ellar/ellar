class ExceptionRunner:
    def __init__(self, exception, **init_kwargs):
        self.exception = exception
        self.option = init_kwargs

    def run(self):
        raise self.exception(**self.option)
