import os

from agent import Agent
from utils.custom_logger import Logger
import logging
from dotenv import load_dotenv

load_dotenv()


if __name__ == "__main__":
    Logger.set_level(level=logging.DEBUG)
    filters = {
        "InStock": "in store",
        "DominantSpecies": ["Indica", "Sativa"],
        "ProductAccessibilityLookupValue": "3",  # Weed strength (1-3)
        "Format": "3.5 g",
    }

    get_env = lambda period: int(os.getenv(period))

    agent = Agent(
        day=int(get_env("DAY")), month=int(get_env("MONTH")), year=int(get_env("YEAR"))
    )
    strains = agent.run(store_id=get_env("STORE_ID"), filters=filters)
    processed = [s for s in strains if s.is_processed]
    processed.sort(key=lambda x: x.display_price)

    for strain in processed:
        print("---------------------------------")
        print(f"NAME: {strain.name}")
        print(f"PRICE: CAD ${strain.display_price}")
        print(f"QTY: {strain.quantity_to_promise:,.0f} packets")
        print(f"URL: {strain.url}")
        print("---------------------------------\n")
