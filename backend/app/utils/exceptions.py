# backend/app/utils/exceptions.py

class NotFoundError(Exception):
    """Custom exception for when a resource is not found."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class BadRequestError(Exception):
    """Custom exception for bad client requests (e.g., invalid parameters)."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class ConflictException(Exception):
    """Custom exception for when a resource conflict occurs (e.g., duplicate)."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class DatabaseException(Exception):
    """Custom exception for database-related errors."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class UnprocessableEntityException(Exception):
    """Custom exception for when an entity cannot be processed due to validation errors."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class ForbiddenException(Exception):
    """Custom exception for when an action is forbidden for the current user."""
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(message)
        self.message = message

class InternalServerError(Exception):
    """Custom exception for unexpected server-side errors."""
    def __init__(self, message: str = "An internal server error occurred."):
        super().__init__(message)
        self.message = message
