# backend/app/core/exceptions.py

class NotFoundException(Exception):
    """Custom exception for when a resource is not found."""
    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)

class BadRequestException(Exception):
    """Custom exception for bad client requests."""
    def __init__(self, message: str = "Bad request"):
        self.message = message
        super().__init__(self.message)

class ForbiddenException(Exception):
    """Custom exception for when an action is forbidden."""
    def __init__(self, message: str = "Forbidden"):
        self.message = message
        super().__init__(self.message)

class UnprocessableEntityException(Exception):
    """Custom exception for when an entity cannot be processed."""
    def __init__(self, message: str = "Unprocessable entity"):
        self.message = message
        super().__init__(self.message)
