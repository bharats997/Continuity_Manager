# backend/app/utils/common_schemas.py
from typing import List, TypeVar, Generic
from pydantic import BaseModel, Field, ConfigDict

DataType = TypeVar('DataType')

class PaginationResponse(BaseModel, Generic[DataType]):
    items: List[DataType] = Field(..., description="List of items for the current page")
    total_items: int = Field(..., description="Total number of items available")
    total_pages: int = Field(..., description="Total number of pages")
    current_page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")

    model_config = ConfigDict(arbitrary_types_allowed=True)

class MessageResponse(BaseModel):
    message: str = Field(..., description="A message describing the result of an operation")
