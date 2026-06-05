from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Price
import pandas as pd

DB_USER = "root"
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_NAME = "farm_market"

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

session = Session()

# Sample market price data for Zambia
data = [
    {"market": "Lusaka", "commodity": "Maize", "price": 5.5, "volume": 200},
    {"market": "Ndola", "commodity": "Maize", "price": 5.8, "volume": 180},
    {"market": "Kitwe", "commodity": "Groundnuts", "price": 12.0, "volume": 90},
    {"market": "Kabwe", "commodity": "Soya Beans", "price": 9.5, "volume": 150},
    {"market": "Lusaka", "commodity": "Tomatoes", "price": 7.0, "volume": 300},
]

for d in data:
    price = Price(
        market=d["market"],
        commodity=d["commodity"],
        price=d["price"],
        volume=d["volume"],
        recorded_at=pd.Timestamp.now().date(),
    )
    session.add(price)

session.commit()
session.close()
print("✅ Sample market data inserted successfully!")
