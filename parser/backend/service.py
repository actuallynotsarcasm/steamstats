from sqlalchemy.orm import Session

from schemas import Item


def get_items(engine, limit=20):
    session = Session(bind=engine)
    query = session.query(Item.name, Item.buy_price, Item.sell_price, Item.listings, Item.item_type).limit(limit)
    session.close()
    resp = [row._asdict() for row in query]
    return resp


def insert_items(engine, items):
    session = Session(bind=engine)
    session.add_all(items)
    session.commit()
    session.close()
    return True


def delete_item(engine, name):
    session = Session(bind=engine)
    session.query(Item).filter(Item.name == name).delete()
    session.commit()
    session.close()
    return True