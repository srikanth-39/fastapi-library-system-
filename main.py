from fastapi import FastAPI
from pydantic import BaseModel,Field
from fastapi import HTTPException,Query
from typing import Optional
from fastapi import status
from math import ceil
app=FastAPI()

#-------------Helper functions---------
# Helper function to find a book
def find_book(book_id):
    for b in books:
        if b["id"] == book_id:
            return b
    return None


# Helper function to calculate due date
def calculate_due_date(borrow_days,member_type):

    if member_type == "premium":
        max_days = 60
    else:
        max_days = 30

    if borrow_days > max_days:
        return f"Error: {member_type} members can borrow only up to {max_days} days"

    return f"Return by: Day {15 + borrow_days}"

def filter_books_logic(genre=None, author=None, is_available=None):
    result = books

    if genre is not None:
        result = [b for b in result if b["genre"].lower() == genre.lower()]

    if author is not None:
        result = [b for b in result if b["author"].lower() == author.lower()]

    if is_available is not None:
        result = [b for b in result if b["is_available"] == is_available]

    return result


#---------keyword search---------------------------------
@app.get("/books/search")
def search_books(keyword: str):
    keyword = keyword.lower()

    result = [
        b for b in books
        if keyword in b["title"].lower() or keyword in b["author"].lower()
    ]

    return {
        "total_found": len(result),
        "books": result
    }

#-----------paging-----------------------------------------


@app.get("/books/page")
def get_books_page(
    page: int = Query(1, gt=0),
    limit: int = Query(3, gt=0)
):
    total = len(books)

    
    total_pages = ceil(total / limit)

   
    if page > total_pages:
        raise HTTPException(status_code=400, detail="Page number out of range")

   
    start = (page - 1) * limit
    end = start + limit

    paginated_books = books[start:end]

    return {
        "total": total,
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit,
        "books": paginated_books
    }

#--------BORROWER SEARCH-------------------
@app.get("/borrow-records/search")
def search_borrow_records(member_name: str):
    keyword = member_name.lower()

    result = [
        r for r in borrow_records
        if keyword in r["member_name"].lower()
    ]

    return {
        "total_found": len(result),
        "records": result
    }

#------------BORROWER PAGE-----------------------


@app.get("/borrow-records/page")
def paginate_borrow_records(
    page: int = Query(1, gt=0),
    limit: int = Query(3, gt=0)
):
    total = len(borrow_records)

    total_pages = ceil(total / limit) if total > 0 else 1

    if page > total_pages:
        raise HTTPException(status_code=400, detail="Page out of range")

    start = (page - 1) * limit
    end = start + limit

    paginated = borrow_records[start:end]

    return {
        "total": total,
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit,
        "records": paginated
    }

#--------Combing all the filters-----------------


@app.get("/books/browse")
def browse_books(
    keyword: Optional[str] = None,
    sort_by: str = Query("title"),
    order: str = Query("asc"),
    page: int = Query(1, gt=0),
    limit: int = Query(3, gt=0)
):
    result = books

    if keyword is not None:
        keyword = keyword.lower()
        result = [
            b for b in result
            if keyword in b["title"].lower() or keyword in b["author"].lower()
        ]

    valid_sort_fields = ["title", "author", "genre"]
    valid_order = ["asc", "desc"]

    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid sort_by")

    if order not in valid_order:
        raise HTTPException(status_code=400, detail="Invalid order")

   
    reverse = True if order == "desc" else False

    result = sorted(
        result,
        key=lambda b: b[sort_by].lower(),
        reverse=reverse
    )

 
    total = len(result)
    total_pages = ceil(total / limit) if total > 0 else 1

    if page > total_pages:
        raise HTTPException(status_code=400, detail="Page out of range")

    start = (page - 1) * limit
    end = start + limit

    paginated = result[start:end]

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "books": paginated
    }

#---------------SORTING--------------------------------
@app.get("/books/sort")
def sort_books(
    sort_by: str = Query("title",description="title or author or genre"),
    order: str = Query("asc",description='asc or desc')
):
    valid_sort_fields = ["title", "author", "genre"]
    valid_order = ["asc", "desc"]

    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by. Choose from {valid_sort_fields}"
        )

    if order not in valid_order:
        raise HTTPException(
            status_code=400,
            detail="Invalid order. Use 'asc' or 'desc'"
        )

    reverse = True if order == "desc" else False

    sorted_books = sorted(
        books,
        key=lambda b: b[sort_by].lower(),
        reverse=reverse
    )

    return {
        "sort_by": sort_by,
        "order": order,
        "total": len(sorted_books),
        "books": sorted_books
    }

#-----------Creating the waiting list-------------------
queue=[]

@app.post("/queue/add")
def add_to_queue(
    member_name: str = Query(...),
    book_id: int = Query(...)
):

    book = find_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book["is_available"]:
        return {"message": "Book is available, you can borrow directly"}

    entry = {
        "member_name": member_name,
        "book_id": book_id
    }

    queue.append(entry)

    return {
        "message": "Added to waiting queue",
        "queue_entry": entry
    }


@app.get("/queue")
def get_queue():
    return {
        "total": len(queue),
        "waiting_list": queue
    }

#---------Returning the books -------------
@app.post("/return/{book_id}")
def return_book(book_id: int):
    global record_counter

    book = find_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book["is_available"] = True

    for entry in queue:
        if entry["book_id"] == book_id:
            
            next_user = entry

            
            queue.remove(entry)

            
            book["is_available"] = False

            
            new_record = {
                "record_id": record_counter,
                "member_name": next_user["member_name"],
                "member_id": "AUTO",   
                "book_id": book_id,
                "borrow_days": 7,      
                "due_date": calculate_due_date(7, "regular")
            }

            borrow_records.append(new_record)
            record_counter += 1

            return {
                "message": "Book returned and reassigned",
                "assigned_to": next_user["member_name"],
                "record": new_record
            }

    return {
        "message": "Book returned and available"
    }



#-----------DELETE a book----------------------

@app.delete("/books/{book_id}")
def delete_book(book_id: int):

    # 🔍 Find book
    book = find_book(book_id)

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 🗑 Remove book
    books.remove(book)

    return {
        "message": f"Book '{book['title']}' deleted successfully"
    }

#---------UPDATE BOOKS---------------------------
from typing import Optional
from fastapi import HTTPException

@app.put("/books/{book_id}")
def update_book(
    book_id: int,
    genre: Optional[str] = None,
    is_available: Optional[bool] = None
):
    # 🔍 Find book
    book = find_book(book_id)

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 🔄 Update only if values provided
    if genre is not None:
        book["genre"] = genre

    if is_available is not None:
        book["is_available"] = is_available

    return {
        "message": "Book updated successfully",
        "book": book
    }



#---------HOME-------------------
@app.get("/")
def home():
    return {"message":"Welcome to the Hindusthan Library"}


#----------Returning the summary--------------
@app.get("/books/summary")
def books_summary():
    total = len(books)

    available = len([b for b in books if b["is_available"]])
    borrowed = total - available

    genre_count = {}
    for b in books:
        genre = b["genre"]
        if genre in genre_count:
            genre_count[genre] += 1
        else:
            genre_count[genre] = 1

    return {
        "total_books": total,
        "available_books": available,
        "borrowed_books": borrowed,
        "genre_count": genre_count
    }

#----------CRUD operations------------
class NewBook(BaseModel):
    title: str = Field(min_length=2)
    author: str = Field(min_length=2)
    genre: str = Field(min_length=2)
    is_available: bool = True



@app.post("/books", status_code=201)
def add_book(book: NewBook):

    for b in books:
        if b["title"].lower() == book.title.lower():
            return {"error": "Book with this title already exists"}

    
    new_id = max([b["id"] for b in books]) + 1

    new_book = {
        "id": new_id,
        "title": book.title,
        "author": book.author,
        "genre": book.genre,
        "is_available": book.is_available
    }

    books.append(new_book)

    return new_book


#-----------Applying filters------------


@app.get("/books/filter")
def filter_books(
    genre: Optional[str] = None,
    author: Optional[str] = None,
    is_available: Optional[bool] = None
):
    filtered = filter_books_logic(genre, author, is_available)

    return {
        "count": len(filtered),
        "books": filtered
    }

#-------------Storing the Books-------
books = [
    {"id": 1, "title": "Python Basics", "author": "John", "genre": "Tech", "is_available": True},
    {"id": 2, "title": "History of India", "author": "Raj", "genre": "History", "is_available": True},
    {"id": 3, "title": "AI Future", "author": "Elon", "genre": "Tech", "is_available": False},
    {"id": 4, "title": "World War", "author": "Smith", "genre": "History", "is_available": True},
    {"id": 5, "title": "Science 101", "author": "Albert", "genre": "Science", "is_available": True},
    {"id": 6, "title": "Fiction Story", "author": "Harry", "genre": "Fiction", "is_available": False}
]

@app.get("/books")
def get_books():
    total = len(books)
    available = len([b for b in books if b["is_available"]])
    
    return {
        "total": total,
        "available_count": available,
        "books": books
    }

#----------Serching for the book by its id--------------------
@app.get("/books/{book_id}")
def get_book(book_id: int):
    b=find_book(book_id)
    if b:
        return b
    return {"error": "Book not found"}

#-------------------Returning the borrowed members---------
borrow_records = []   # stores all borrow data
record_counter = 1    # used for unique IDs

@app.get("/borrow-records")
def get_borrow_records():
    return {
        "total": len(borrow_records),
        "records": borrow_records
    } 

#-------Creating a class for the validation of the user input-------
class BorrowRequest(BaseModel):
    member_name: str = Field(min_length=2)
    book_id: int = Field(gt=0)
    borrow_days: int = Field(gt=0)   
    member_id: str = Field(min_length=4)
    member_type: str = "regular" 



@app.post("/borrow")
def borrow_book(request: BorrowRequest):
    global record_counter

    book = find_book(request.book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book["is_available"]:
        raise HTTPException(status_code=400, detail="Book already borrowed")

    
    book["is_available"] = False

    due_date = calculate_due_date(request.borrow_days, request.member_type)

  
    new_record = {
        "record_id": record_counter,
        "member_name": request.member_name,
        "member_id": request.member_id,
        "book_id": request.book_id,
        "borrow_days": request.borrow_days,
        "due_date": due_date
    }

    borrow_records.append(new_record)

    record_counter += 1


    return {
        "message": "Book borrowed successfully",
        "record": new_record
    }




