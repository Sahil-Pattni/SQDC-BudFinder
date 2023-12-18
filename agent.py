import logging
import urllib
from time import sleep
from typing import List

import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.by import By
from tqdm import tqdm

from utils.custom_logger import Logger
from strain import Strain

logger = Logger().get_logger()


def pause():
    sleep(0.5)


class Agent:
    def __init__(self, day: int, month: int, year: int) -> None:
        """
        Initializes the agent.
        :param day: The day of birth
        :param month: The month of birth
        :param year: The year of birth
        """
        self.__debug = logger.level > logging.DEBUG
        self.__DAY = str(day)
        self.__MONTH = str(month)
        self.__YEAR = str(year)

    def run(
        self, store_id: int, filters: dict = None, save_files: bool = True
    ) -> List[Strain]:
        """
        Extracts strain data from the SQDC website.
        :param store_id: The store ID to extract data from.
        :param filters: The filters to apply to the SQDC website. See `build_filter_url` for more info.
        :param save_files: Whether to save the strain objects to file.
        :return: A list of strain objects.
        """
        self.__init_driver()
        self.__login()
        self.__set_cookies()

        default_filter = {
            "InStock": "in store",
            "DominantSpecies": ["Indica", "Sativa"],
            "ProductAccessibilityLookupValue": "3",  # Weed strength (1-3)
            "Format": "3.5 g",
        }
        filters = filters or default_filter
        url = self.build_filter_url(filters)

        # Find all product elements
        self.driver.get(url)
        strains: dict[str, Strain] = self.__extract_strain_data(store_id, filters)

        # Get info from all pages
        current_page = 1
        while True:
            logger.info(f"Processing page {current_page:,}...")
            num_updated = self.__extract_names(strains)
            logger.debug(f"Updated {num_updated:,} strains.")
            # Load next page or break
            if not self.__load_next_page():
                logger.info("No more pages to load. Stopping scan...")
                break
            else:
                current_page += 1

        # Close the driver
        self.driver.quit()

        # Save strains to file
        if save_files:
            logger.debug("Saving strains to file...")
            for strain in strains.values():
                if strain.is_processed:
                    strain.save("out/strains")
                    logger.info(f'Strain "{strain.name}" saved.')
                else:
                    logger.debug(
                        f'Skipping strain "{strain.sku}" as it is not fully processed.'
                    )

        return list(strains.values())

    def __load_next_page(self) -> bool:
        """
        Clicks the 'Next' button if it is not disabled.
        :return: True if there is a next page, False otherwise.
        """
        # Find the 'Next' button
        next_button = self.driver.find_element(
            By.CSS_SELECTOR, "li.page-item.next a.page-link"
        )

        # Check if the 'Next' button is disabled
        is_disabled = "disabled" in next_button.find_element(
            By.XPATH, ".."
        ).get_attribute("class")

        if not is_disabled:
            next_button.click()

        return not is_disabled

    def __extract_names(self, strains: dict[str, Strain]) -> int:
        """
        Extracts the names of the strains from the website.
        :param strains: The strains dictionary to update.
        :return: The number of strains updated.
        """
        strains_updated: int = 0
        product_listing = self.driver.find_elements(
            By.CSS_SELECTOR, "a.js-equalized-name[data-productid]"
        )

        # Update strain objects
        for product in tqdm(
            product_listing, disable=self.__debug, desc="Extracting names"
        ):
            # Corner case, should not run, as no unseen strains should be in the list
            product_id: str = product.get_attribute("data-productid")
            if product_id not in strains.keys():
                logger.warning(f"Strain {product_id} not found in priced strains")
                continue

            # Update strain object
            strains[product_id].name = product.text
            strains[product_id].url = product.get_attribute("href")
            strains_updated += 1
            logger.debug(f"Strain `{strains[product_id].name}` extracted.")

        return strains_updated

    def __extract_strain_data(self, store_id: int, filters: dict) -> dict[str, Strain]:
        """
        Extracts the SKU and quantity of each strain from the website.
        :param store_id: The store ID to extract data from.
        :param filters: The filters to apply to the SQDC website. See `build_filter_url` for more info.
        :return: A list of strain objects.
        """
        items: List[dict] = self.__get_store_inventory(store_id, filters)
        logger.debug(f"Found {len(items):,} items in store {store_id}")

        strains: dict[str, Strain] = {}

        # --- Step 1: Filter out strains with 0 quantity --- #
        for item in tqdm(
            items, disable=self.__debug, desc="Filtering strains with no quantity"
        ):
            # Ignore items with 0 quantity
            _q = item["Quantity"]
            if _q["Quantity"] == 0 or _q["AvailableToPromiseQuantity"] == 0:
                continue
            # Build strain object
            current_strain = Strain(
                sku=item["Sku"],
                quantity=_q["Quantity"],
                promised_quantity=_q["AvailableToPromiseQuantity"],
            )

            # Add strain to dictionary
            strains[current_strain.product_id] = current_strain

        # --- Step 2: Calculate prices --- #
        prices = self.__get_prices([s.sku for s in strains.values()], store_id)

        # --- Step 3: Remove strains with no/wrong pricing --- #
        strains_to_remove = self.__price_strains(prices, strains)
        for product_id in strains_to_remove:
            del strains[product_id]

        # Filter to only processed and return
        return strains

    def __price_strains(self, prices: List[dict], strains: dict[str, Strain]):
        """
        Applies the prices to the strains.
        :param prices: A list of price JSON dict from the SQDC API.
        :param strains: A dictionary of strains to update.
        :return: A list of strains with no price or with an unreasonably low price, to remove.
        """
        strains_to_remove: List[str] = []
        for _p in tqdm(
            prices, disable=self.__debug, desc="Filtering strains with no price"
        ):
            # Corner case, should not run, as no unseen strains should be in the list
            product_id = _p["ProductId"]
            if product_id not in strains.keys():
                logger.warning(f"Strain {_p['ProductId']} not found in all_strains")
                continue

            # If no variant price set, try default price. If that fails, skip
            if "VariantPrices" not in _p or len(_p["VariantPrices"]) == 0:
                try:
                    display_price = float(_p["DisplayPrice"].replace("$", ""))
                    list_price = float(_p["DefaultListPrice"].replace("$", ""))
                except Exception as _:
                    strains_to_remove.append(product_id)
                    continue
            # If variant price set, use that
            else:
                _v = _p["VariantPrices"][0]
                display_price = float(_v["DisplayPrice"].replace("$", ""))
                list_price = float(_v["ListPrice"].replace("$", ""))

            # Ignore very low prices, probably a mistake
            if display_price < 1 or list_price < 1:
                strains_to_remove.append(product_id)
                continue

            # Update strain object
            strains[product_id].display_price = display_price
            strains[product_id].list_price = list_price

        return strains_to_remove

    def __init_driver(self) -> None:
        """
        Initializes the Selenium driver, and sets the window size.
        """
        self.driver = webdriver.Chrome()
        ActionBuilder(self.driver).clear_actions()
        self.driver.implicitly_wait(2)
        self.driver.set_window_size(1024, 768)

    def __login(self) -> None:
        """
        Accepts the cookies and enters the date of birth
        on the SQDC website.
        """
        logger.info("Starting log-in sequence...")
        self.driver.get("https://www.sqdc.ca/en-CA/")

        # Step 1: Accept Cookies
        logger.info("Attempting to accept cookies")
        cookie_box = self.driver.find_element(By.ID, "didomi-notice-agree-button")
        ActionChains(self.driver).move_to_element(cookie_box).click().perform()
        pause()

        # Step 2: Enter Date of Birth
        logger.info("Attempting to find DoB fields...")
        month_input = self.driver.find_element(By.ID, "month")
        day_input = self.driver.find_element(By.ID, "day")
        year_input = self.driver.find_element(By.ID, "year")

        # Enter the date of birth
        # Replace these with the desired date
        logger.info("Entering date of birth...")
        month_input.send_keys(self.__MONTH)
        day_input.send_keys(self.__DAY)
        year_input.send_keys(self.__YEAR)

        # Locate the submit button and click it
        submit_button = self.driver.find_element(
            By.CSS_SELECTOR, "button[type='submit']"
        )
        submit_button.click()
        logger.info("Log-in sequence complete.")

    def __set_cookies(self):
        """
        Extracts the cookies from Selenium and stores them for requests.
        :return:
        """
        logger.debug("Extracting cookies...")
        # Extract cookies from Selenium and format them for requests
        selenium_cookies = self.driver.get_cookies()
        self.__cookies = {
            cookie["name"]: cookie["value"] for cookie in selenium_cookies
        }
        logger.debug("Cookies extracted.")

    def __build_cookie_header(self, store_id: int) -> str:
        """
        Builds the cookie header for requests.
        :param store_id: The store ID to use.
        :return: The cookie header.
        """
        cookie_header: str = "; ".join(
            [f"{key}={value}" for key, value in self.__cookies.items()]
        )
        idk_what_this_is_for = '_hd={"heyday-widget-state": "welcome"}'
        cookie_header = (
            f"SelectedStore={store_id}; {idk_what_this_is_for}; {cookie_header}"
        )
        return cookie_header

    def __build_header(self, store_id: int, referer: str = None) -> dict:
        """
        Builds the header for requests.
        :param store_id: The store ID to use.
        :param referer: The website to use as the referer.
        :return: The header.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-CA",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Host": "www.sqdc.ca",
            "Cookie": self.__build_cookie_header(store_id),
            "Origin": "https://www.sqdc.ca",
            "Referer": referer or "https://www.sqdc.ca/en-CA/Stores",
            "Connection": "keep-alive",
            "X-Requested-With": "XMLHttpRequest",
            "WebsiteId": "f3dbd28d-365f-4d3e-91c3-7b730b39b294",
        }
        return headers

    def __build_url(self, endpoint: str) -> str:
        """
        Builds the URL for requests.
        :param endpoint: The endpoint to use.
        :return: The URL.
        """
        return f"https://www.sqdc.ca/api/{endpoint}"

    def build_filter_url(self, filters: dict = None) -> str:
        """
        Builds the URL for the SQDC website with the given filters.
        These can include:
        - InStock: "in store", "online", or both as ["in store", "online"]
        - DominantSpecies: "Indica", "Sativa", or both as ["Indica", "Sativa"]
        - ProductAccessibilityLookupValue: "1", "2", or "3" (weed strength)
        - Format: "3.5 g", "7 g", "15 g", "28 g", or "1 g"

        :param filters: The filters to apply to the SQDC website.
        :return: The URL.
        """
        base_url = "https://www.sqdc.ca/en-CA/dried-cannabis/dried-flowers?&"
        params = {}
        if filters:
            i = 1
            for key, value in filters.items():
                params[f"fn{i}"] = key
                if type(value) == list:
                    params[f"fv{i}"] = "|".join(value)
                else:
                    params[f"fv{i}"] = value
                i += 1

        return base_url + urllib.parse.urlencode(params)

    def __get_prices(self, skus: List[str], store_id) -> List[dict]:
        """
        Gets the prices of the given SKUs.
        :param skus: The SKUs to get the prices of.
        :param store_id: The store ID to use.
        :return: The response from the SQDC API as a list of JSON dicts.
        """
        logger.info(f"Requesting prices for {len(skus):,} sku(s)...")
        url = self.__build_url("product/calculatePrices")
        payload = {"products": [f"{sku}-P" for sku in skus]}
        headers = self.__build_header(store_id)

        response = requests.post(
            url, json=payload, headers=headers, cookies=self.__cookies
        )

        if response.status_code != 200:
            logger.error(f"Failed to calculate prices. Message: {response.text}")
            raise Exception("Failed to calculate prices")

        logger.info("Prices calculated.")
        return response.json()["ProductPrices"]

    def __get_store_inventory(self, store_id: int, filters: dict = None) -> List[dict]:
        """
        Gets the inventory of a store.
        :param store_id: The store ID to get the inventory of.
        :param filters: The filters to apply to the SQDC website. See `build_filter_url` for more info.
        :return: The inventory of the store as a list of JSON dicts.
        """
        url = self.__build_url("olivestoreinventory/getmystoreinventory")
        payload = {"InventoryLocationId": store_id}
        referer = self.build_filter_url(filters=filters)
        headers = self.__build_header(store_id, referer=referer)

        response = requests.post(
            url, json=payload, headers=headers, cookies=self.__cookies
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to get store inventory for store {store_id}. Message: {response.text}"
            )

        items = response.json()["InventoryItems"]

        return items
