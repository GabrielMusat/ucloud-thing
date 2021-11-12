class HttpException(Exception):
    def __init__(self, code, *args):
        super().__init__(*args)
        self.code = code

