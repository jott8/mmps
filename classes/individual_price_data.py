class IndividualPriceData:
    def __init__(self, price: float, price_new: float, condition: str, on_sale: bool, sale_percentage, sale_abs, stock: int):
        self.price = price
        self.price_new = price_new
        self.condition = condition
        self.on_sale = on_sale
        self.sale_percentage = sale_percentage
        self.sale_abs = sale_abs
        self.stock = stock
