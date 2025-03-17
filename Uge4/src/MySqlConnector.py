import mysql.connector
from sqlalchemy import create_engine
from sqlalchemy import URL

class MySqlConnector:
    def __init__(self, database):
        self.database = database

    def __enter__(self):
        self.authenticate()
        return(self.conn)

    def authenticate(self):
        url_object = URL.create(
            "mysql+mysqlconnector",
            username="root",
            password="Velkommen25",
            host="localhost",
            database=self.database,
        )
        self.conn = create_engine(url_object).connect()

    def __exit__(self,exc_type,exc_value,traceback):
        self.conn.close()