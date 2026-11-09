from sqlalchemy import Column, Integer, String, DateTime, REAL, Enum
from database import Base

class User(Base):
    """Store a user's account information."""
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    surname = Column(String(50))
    password = Column(String(255))
    email = Column(String(120), unique=True)
    birth_date = Column(DateTime)
    country = Column(String(50), nullable=True)

    def __repr__(self):
        """Return a readable representation of the user."""
        return f'<User {self.name!r}>'

class Catgeory(Base):
    """Store a system or user-owned transaction category."""
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    owner = Column(Integer)

    def __repr__(self):
        """Return a readable representation of the category."""
        return f"<Category(id={self.id}, name='{self.name}', owner={self.owner})>"



class Transaction(Base):
    """Store an income or spending transaction."""
    __tablename__ = 'transaction'
    id = Column(Integer, primary_key=True)
    description = Column(String(100))
    category = Column(Integer)
    amount = Column(REAL)
    date = Column(String)
    owner = Column(Integer)
    type = Column(Integer)

    def __repr__(self):
        """Return a readable representation of the transaction."""
        return (
            f"""<Transaction(id={self.id}, description='{self.description}',
            category={self.category}, amount={self.amount},
            date='{self.date}', owner={self.owner}, type={self.type})>"""
        )
