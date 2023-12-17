class Strain:
    def __init__(
        self,
        sku: str,
        name: str = "(name not assigned)",
        list_price: float = None,
        display_price: float = None,
        quantity: int = None,
        promised_quantity: int = None,
        url: str = "(url not assigned)",
    ):
        """
        :param sku: The SKU of the strain
        :param name: The name of the strain
        :param list_price: The list price of the strain
        :param display_price:  The display price of the strain
        :param quantity: The quantity of the strain
        :param promised_quantity: The available to promise quantity of the strain
        :param url: The URL of the strain
        """
        self.__sku = sku
        self.__name = name
        self.__list_price = list_price
        self.__display_price = display_price
        self.__quantity = quantity
        self.__promised_quantity = promised_quantity
        self.__url = url

    @property
    def sku(self):
        return self.__sku

    @property
    def product_id(self):
        return self.__sku + "-P"

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def list_price(self):
        return self.__list_price

    @list_price.setter
    def list_price(self, value):
        self.__list_price = value

    @property
    def display_price(self):
        return self.__display_price

    @display_price.setter
    def display_price(self, value):
        self.__display_price = value

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, value):
        self.__url = value

    @property
    def quantity(self):
        return self.__quantity

    @quantity.setter
    def quantity(self, value):
        self.__quantity = value

    @property
    def promised_quantity(self):
        return self.__promised_quantity

    @promised_quantity.setter
    def promised_quantity(self, value):
        self.__promised_quantity = value

    def __str__(self):
        return f"Name: {self.name}\nSKU: ({self.sku})"
