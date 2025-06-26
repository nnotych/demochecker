from fastapi import FastAPI
from books.router import router as books_router
from auth.auth_router import router as auth_router

app = FastAPI(title="Books API")

app.include_router(books_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
