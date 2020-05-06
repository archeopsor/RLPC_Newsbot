import os
# import psycopg2
from sqlalchemy import create_engine
import pandas as pd

DATABASE_URL = None
try: DATABASE_URL = os.environ['DATABASE_URL']
except: from passwords import DATABASE_URL

engine = create_engine(DATABASE_URL)

def select(string):
    sql = engine.connect()
    data = pd.read_sql(string, sql)
    sql.close()
    return data