from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Price
from datetime import date, timedelta
import random

DB_URL = "mysql+mysqlconnector://root:@127.0.0.1:3306/farm_market"

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

base = date(2025, 10, 10)
markets = ["Lusaka Central", "Kabwe Main"]
commodities = ["Maize", "Tomatoes"]

for m in markets:
    for c in commodities:
        for i in range(15):
            session.add(Price(
                market=m,
                commodity=c,
                price=1500 + random.randint(-40, 60) if c == "Maize" else 5000 + random.randint(-150, 150),
                volume=400 + random.randint(-50, 50),
                recorded_at=base + timedelta(days=i)
            ))

session.commit()
session.close()
print("✅ Sample data loaded successfully!")
