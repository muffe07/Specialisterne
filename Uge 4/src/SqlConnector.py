import mysql.connector
from pathlib import Path
from getpass import getpass

class SqlConnector:
    def __init__(self, database):
        self.database = database

    def get_password(self):
        password_path = Path(__file__).parent.parent.joinpath("password")
        if(not password_path.exists()):
            with open(password_path, "w") as password_file:
                password_file.write(getpass())

        with open(password_path) as password_file:
            return(password_file.read())
    
    def __enter__(self):
        self.authenticate()
        return(self.conn)

    def authenticate(self):
        password = self.get_password()
        self.conn = mysql.connector.connect(
            username="root",
            password=password,
            host="localhost",
            database=self.database,
        )
        return(self.conn)
    def __exit__(self,exc_type,exc_value,traceback):
        self.conn.close()
