from classes.author import Author
from classes.book import Book


class EntryData:
    def __init__(self, book: Book, author: Author):
        self.book = book
        self.author = author
