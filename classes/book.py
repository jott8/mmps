from functions import convert_url


class Book:
    def __init__(self, title: str, pages: int, medium: str, medimops_url: str):
        self.title = title
        self.pages = pages
        self.medimops_url = medimops_url
        self.api_url = convert_url(medimops_url)

        if (medium == "Gebundene Ausgabe"):
            medium = "Gebunden"

        elif (medium == "Broschiert"):
            medium = "Taschenbuch"

        self.medium = medium
