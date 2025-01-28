from sqlalchemy import String, Integer, Column, Float
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Item(Base):
    __tablename__ = 'items'
    id = Column('id', Integer(), primary_key=True)
    name = Column('name', String(100), nullable=False)
    item_type = Column('type', String(100), nullable=False)
    buy_price = Column('buy_price', Float(), nullable=False)
    sell_price = Column('sell_price', Float(), nullable=False)
    listings = Column('listings', Integer(), nullable=False)