class ContextPackerError(Exception):
    pass


class InvalidProjectRoot(ContextPackerError):
    pass


class ReadError(ContextPackerError):
    pass


class WriteError(ContextPackerError):
    pass
