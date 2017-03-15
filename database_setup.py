import os
import sys
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	__tablename__='user'
	id = Column(Integer, primary_key=True)
	name = Column(String(40), nullable=False)
	email = Column(String(100), nullable=False)
	picture = Column(String(250))


class Category(Base):
	__tablename__='category'

	id = Column(Integer, primary_key=True)
	name = Column(String(20), nullable=False)


class Item(Base):
	__tablename__ = 'item'

	id = Column(Integer, primary_key=True)
	name = Column(String(50), nullable=False)
	description = Column(String(250))
	category_id = Column(Integer, ForeignKey('category.id'))
	category = relationship(Category)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	last_updated = Column(DateTime, nullable=False, default=datetime.utcnow(), onupdate=datetime.utcnow())

	@property
	def serialize(self):
		return{
			'id' : self.id,
			'name' : self.name,
			'description' : self.description,
			'last_updated' : self.last_updated
		}

engine = create_engine('sqlite:///catalog.db')


Base.metadata.create_all(engine)