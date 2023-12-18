import pickle
import os

from utils.custom_logger import Logger

logger = Logger().get_logger()


class Strain:
    def __init__(
        self,
        sku: str,
        name: str = None,
        list_price: float = None,
        display_price: float = None,
        quantity: int = None,
        promised_quantity: int = None,
        url: str = None,
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

    @staticmethod
    def load(directory: str, filename: str):
        """
        Loads the strain object from a pickle file.
        :param directory: The directory to load the file from.
        :param filename: The name of the file to load.
        :return: The strain object.
        """
        filepath: str = os.path.join(directory, filename)
        with open(filepath, "rb") as f:
            return pickle.load(f)

    def save(self, directory: str) -> None:
        """
        Saves the strain object to a pickle file.
        :param directory: The directory to save the file to.
        """
        # Base case: if directory does not exist, create it
        if not os.path.exists(directory):
            logger.debug(f"Directory `{directory}` does not exist. Creating it...")
            os.makedirs(directory)
        filename: str = f"{self.name}.weed"
        filepath: str = os.path.join(directory, filename)
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @property
    def is_processed(self) -> bool:
        """
        :return: Returns true if all the instance variables have been assigned.
        """
        return not any(x is None for x in self.__dict__.values())

    @property
    def sku(self):
        """
        :return: The SQDC SKU of the strain.
        """
        return self.__sku

    @property
    def product_id(self):
        """
        :return: The SKU of the strain with a "-P" appended to the end. Used as a unique key.
        """
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
