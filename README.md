# SQDC BudFinder

---

## Description
This is a tool to help you find all the strains that are in stock at a given store, 
along with its listed and display prices, and a url to the product's page on the SQDC website.

I am currently working on integrating the data with Leafly to provide more information about the strains.

## Usage
Please install the required packages with `pip install -r requirements.txt` before running the script.

The following script is an exerpt from the full example in `main.py`:
```python
filters = {
    "InStock": "in store",
    "DominantSpecies": ["Indica", "Sativa"],
    "ProductAccessibilityLookupValue": "3",  # Weed strength (1-3)
    "Format": "3.5 g",
}

# Replace the following with your own values
get_env = lambda period: int(os.getenv(period))
agent = Agent(
    day=1, month=1, year=2991)
)

# Get all the strains in store that match the filters
strains = agent.run(store_id=get_env("STORE_ID"), filters=filters)

# Filter to only the strains that have all values set
processed = [s for s in strains if s.is_processed]
processed.sort(key=lambda x: x.display_price)

for strain in processed:
    print("---------------------------------")
    print(f"NAME:       {strain.name}")
    print(f"PRICE:      CAD ${strain.display_price}")
    print(f"LIST PRICE: CAD ${strain.list_price}")
    print(f"QTY:        {strain.quantity_to_promise:,.0f} packets")
    print(f"URL:        {strain.url}")
    print("---------------------------------\n")
```
Example output:
```
---------------------------------
NAME:       Bruce Banner
PRICE:      CAD $23.5
LIST PRICE: CAD $20.44
QTY:        46 packets
URL:        https://www.sqdc.ca/en-CA/p-bruce-banner/870814000042-P/870814000042
---------------------------------

---------------------------------
NAME:       Bruce Banner
PRICE:      CAD $23.5
LIST PRICE: CAD $20.44
QTY:        46 packets
URL:        https://www.sqdc.ca/en-CA/p-bruce-banner/870814000042-P/870814000042
---------------------------------

---------------------------------
NAME:       Bruce Banner
PRICE:      CAD $23.5
LIST PRICE: CAD $20.44
QTY:        46 packets
URL:        https://www.sqdc.ca/en-CA/p-bruce-banner/870814000042-P/870814000042
---------------------------------

```