import os
import psycopg2
import sqlite3

def open():
    try: DATABASE_URL = os.environ['DATABASE_URL']
    except: from passwords import DATABASE_URL
    
    global cursor
    global conn
    
    try: conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    except: print("Could not connect to database.")
    
    cursor = conn.cursor()
    
    return(cursor, conn)

def close():
    cursor.close()
    conn.close()
    print("The connection to the database has been closed.")

def select(table, columns=("*"), As=None, where=None, order_by=None, group_by=None, having=None, distinct=False, limit=None):
    open()
    
    command = f"SELECT {columns} FROM {table}"
    
    cursor.execute(command)
    results = cursor.fetchall()
    
    conn.commit()
    close()
    
    return(results)
    
def insert(table, *values, columns=None,):
    open()
    
    if columns == None:
        cursor.execute(f'''INSERT INTO {table}
                       VALUES {values};''')
    else:
        col = f'('
        for column in columns:
            col = col+column+", "
        col = col[:-2] + ")"
        cursor.execute(f'''INSERT INTO {table} {col}
VALUES {values};''')
    
    conn.commit()
    close()

def create(name, **values):
    open()
    command = f"CREATE TABLE {name} ("
    for key, value in values.items():
        command = command + "\n" + f"{key}    {value},"
    command = command[:-1] + "\n);"
    cursor.execute(command)
    conn.commit()
    close()

def drop(name):
    open()
    confirmation = input(f"Are you sure you want to delete table '{name}'? ")
    if confirmation.casefold() == "yes":
        cursor.execute(f"DROP TABLE {name};")
        print(f"Table {name} has been deleted")
        conn.commit()
    else:
        print("The command has been aborted")
    close()

def alter(table, add=[], drop=[], alter={}):
    open()
    command = f'ALTER TABLE {table}'
    if not add and not drop and not alter:
        print("There were no actions specified")
        return
    
    close()

def delete(table):
    pass

def update(table):
    pass