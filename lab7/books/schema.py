from pydantic import BaseModel, Field

class Book(BaseModel):
    id: int
    title: str = Field(..., min_length=3, max_length=30)
    author: str = Field(..., min_length=3, max_length=30)
    year: int = Field(..., ge=1000, le=2025)
    genre: str = Field(..., min_length=2, max_length=10)
