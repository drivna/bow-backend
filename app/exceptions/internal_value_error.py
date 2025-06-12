class InternalValueError(Exception):
    # known invalid input error but meant to be consumed internally
    def __init__(self, message: str) -> None:
        self.message = message
