from classes.author import Author
from classes.book import Book
from classes.individual_price_data import IndividualPriceData


class ScanData:
    def __init__(self, book: Book, author: Author, individual_scan_data: IndividualPriceData):
        self.book = book
        self.author = author
        self.individual_scan_data = individual_scan_data
