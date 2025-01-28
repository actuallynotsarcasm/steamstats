from pydantic import BaseModel


class Item(BaseModel):
    name: str
    item_type: str
    buy_price: float
    sell_price: float
    listings: int