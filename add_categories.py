from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

newCategory= Category(name = "Audi")
session.add(newCategory)
newCategory= Category(name = "BMW")
session.add(newCategory)
newCategory= Category(name = "Chevrolet")
session.add(newCategory)
newCategory= Category(name = "Ford")
session.add(newCategory)
newCategory= Category(name = "Honda")
session.add(newCategory)
newCategory= Category(name = "Jeep")
session.add(newCategory)
newCategory= Category(name = "Mazda")
session.add(newCategory)
newCategory= Category(name = "Nissan")
session.add(newCategory)
newCategory= Category(name = "Subaru")
session.add(newCategory)
newCategory= Category(name = "Tesla")
session.add(newCategory)
newCategory= Category(name = "Volvo")
session.add(newCategory)
session.commit()