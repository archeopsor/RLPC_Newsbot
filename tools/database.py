import os
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
import pandas as pd

DATABASE_URL = None
try: DATABASE_URL = os.environ['DATABASE_URL']
except: from passwords import DATABASE_URL

engine = create_engine(DATABASE_URL)

Base = declarative_base()

def select(string):
    sql = engine.connect()
    data = pd.read_sql(string, sql)
    sql.close()
    return data
