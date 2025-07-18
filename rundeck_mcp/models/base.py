"""Base models for Rundeck MCP Server."""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel as PydanticBaseModel, Field, computed_field


T = TypeVar("T")


class BaseModel(PydanticBaseModel):
    """Base model with common configuration."""
    
    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }


class ListResponseModel(BaseModel, Generic[T]):
    """Generic response model for list operations."""
    
    response: List[T] = Field(description="List of items")
    total_count: Optional[int] = Field(None, description="Total number of items available")
    
    @computed_field
    @property
    def count(self) -> int:
        """Number of items in the current response."""
        return len(self.response)
    
    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable summary of the response."""
        if self.total_count is not None:
            return f"Retrieved {self.count} of {self.total_count} items"
        return f"Retrieved {self.count} items"


class PaginatedResponse(BaseModel, Generic[T]):
    """Response model for paginated operations."""
    
    items: List[T] = Field(description="List of items in current page")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_count: Optional[int] = Field(None, description="Total number of items available")
    has_next: bool = Field(description="Whether there are more pages")
    has_previous: bool = Field(description="Whether there are previous pages")
    
    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable summary of the pagination."""
        start = (self.page - 1) * self.page_size + 1
        end = min(self.page * self.page_size, self.total_count or len(self.items))
        
        if self.total_count is not None:
            return f"Page {self.page}: Items {start}-{end} of {self.total_count}"
        return f"Page {self.page}: {len(self.items)} items"


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    @computed_field
    @property
    def summary(self) -> str:
        """Human-readable error summary."""
        if self.error_code:
            return f"Error {self.error_code}: {self.error}"
        return f"Error: {self.error}"