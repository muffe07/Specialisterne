import numpy as np
import pandas as pd
import requests 
import mysql.connector
import json
from pathlib import Path
from io import StringIO

#I don't want to start the API locally for development. So it gets imported even though its not a module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import API

class Extract():
    def __init__(self):
        try:
            with open(Path(__file__).parent.parent/"config.json") as file:
                self.config = json.load(file)
        except FileNotFoundError as e:
            print("config file not found")
            print("you can use example_config.json to create a config.json file")
            exit()

        try:
            self.connector = mysql.connector.connect(
                port="3306",
                host=self.config["remote_IP"],
                user=self.config["remote_SQL_user"],
                password=self.config["remote_SQL_password"],
                connect_timeout=1
            )
        except Exception as e:
            print("SQL failed to connect to server. Using localhost")
            self.connector = mysql.connector.connect(
                host="localhost",
                port="3306",
                user=self.config["local_SQL_user"],
                password=self.config["local_SQL_password"]
            )
        self.cursor = self.connector.cursor()


    def access_api(self, table):
        try:
            url = f"http://{self.config["remote_IP"]}:8000/{table}"
            response = requests.get(url,timeout=1)
            string = json.loads(response.content.decode("utf-8"))
        except Exception as e:
            print("failed to access API. Using localhost")
            match table:
                case "orders":
                    string = API.read_orders()
                case "customers":
                    string = API.read_customers()
                case "order_items":
                    string = API.read_order_items()
                case _:
                    print("failed to find table using local API")
                    print("exiting")
                    exit()
        return pd.read_json(StringIO(string))

    def sql_to_pandas(self, table_name):
        self.cursor.execute(f"USE {self.config["remote_database_name"]}")
        self.cursor.execute(f"DESCRIBE {table_name}")
        header = np.array(self.cursor.fetchall())
        self.cursor.execute(f"select * from {table_name}")
        dataframe = pd.DataFrame(self.cursor.fetchall(),columns = header[:,0])
        return dataframe

    def get_data(self):
        csv_path = Path(__file__).parent.parent/"data"
        stores = pd.read_csv(csv_path/"stores.csv")
        staffs = pd.read_csv(csv_path/"staffs.csv")

        #bit wierd you can convert json to tables. But because the json is made from csv files it works
        orders = self.access_api("orders")
        customers = self.access_api("customers")
        order_items = self.access_api("order_items")

        brands = self.sql_to_pandas("brands")
        categories = self.sql_to_pandas("categories")
        products = self.sql_to_pandas("products")
        stocks = self.sql_to_pandas("stocks")

        tables = {}
        tables["stocks"] = stocks
        tables["stores"] = stores
        tables["staffs"] = staffs
        tables["orders"] = orders
        tables["customers"] = customers
        tables["order_items"] = order_items
        tables["brands"] = brands
        tables["categories"] = categories
        tables["products"] = products
        return(tables)

    def __del__(self):
        #don't need to commit as no changes will be made when reading
        self.connector.close()