# FastAPI Library Management System

##  Project Overview
This project is a backend application built using FastAPI to manage a library system. It supports book management, borrowing, returning, and queue handling with advanced features like search, sorting, and pagination.

---

##  Features Implemented

###  Book Management
- View all books
- Add new books
- Update book details
- Delete books

###  Borrow & Return System
- Borrow books with validation
- Return books
- Auto reassign book from queue

### Queue System
- Add users to waiting list if book unavailable
- Automatically assign book when returned

###  Advanced Features
- Search books (title & author)
- Filter books
- Sort books
- Pagination
- Combined browsing (filter + sort + pagination)

---

##  Technologies Used
- FastAPI
- Python
- Pydantic
- Uvicorn

---

##API Endpoints

### Books
- GET /books
- POST /books
- PUT /books/{book_id}
- DELETE /books/{book_id}
- GET /books/filter
- GET /books/search
- GET /books/sort
- GET /books/page
- GET /books/browse

###  Borrowing
- POST /borrow
- POST /return/{book_id}
- GET /borrow-records
- GET /borrow-records/search
- GET /borrow-records/page

### ⏳ Queue
- POST /queue/add
- GET /queue

---

## 📸 Screenshots
Screenshots of API testing are available in the `screenshots/` folder.

---

## How to Run the Project

1. Install dependencies:
```bash
pip install -r requirements.txt