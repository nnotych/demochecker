from fastapi import APIRouter, HTTPException
from .schema import Book
from typing import List

router = APIRouter(prefix="/books", tags=["books"])

books_db = []

@router.get("/", response_model=List[Book])
def get_books():
    return books_db

@router.post("/", response_model=Book, status_code=201)
def add_book(book: Book):
    books_db.append(book)
    return book

@router.get("/{book_id}", response_model=Book)
def get_book(book_id: int):
    for book in books_db:
        if book.id == book_id:
            return book
    raise HTTPException(status_code=404, detail="Book not found")

@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: int):
    global books_db
    books_db = [b for b in books_db if b.id != book_id]
