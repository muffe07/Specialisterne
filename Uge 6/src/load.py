from pathlib import Path
import json
import mysql.connector
import pandas as pd
import numpy as np

class Load():
    def __init__(self):
        try:
            with open(Path(__file__).parent.parent/"config.json") as file:
                self.config = json.load(file)
        except FileNotFoundError as e:
            print("config file not found")
            print("you can use example_config.json to create a config.json file")
            exit()

        self.connector = mysql.connector.connect(
            host="localhost",
            port="3306",
            user=self.config["local_SQL_user"],
            password=self.config["local_SQL_password"]
        )

        self.cursor = self.connector.cursor()

    #def create_database(self, name):
        #self.cursor.execute(f"DROP DATABASE IF EXISTS {name}")
        #self.cursor.execute(f"CREATE DATABASE {name}")
        #self.connector.commit()

    def create_table(self, dataframe, table_name, database):
        #setup
        self.cursor.execute(f"USE {database}")
        self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        #create table and header
        column_dtypes = pd.concat([dataframe.index.dtypes, dataframe.dtypes])
        
        key = ", ".join([str(k) for k,v in dataframe.index.dtypes.items()])
        dtype_dict = {"int64":"int", "Int64":"int", "object":"varchar(255)","float64":"decimal(16,2)"}
        column_header = ",\n".join([f"{k} {dtype_dict[str(v)]}" for k,v in column_dtypes.items()])

        query = (f"""CREATE TABLE {table_name} (\n{column_header},\nPRIMARY KEY ({key})\n)""")
        self.cursor.execute(query)

        #insert data
        data_substitude = ", ".join(["%s"]*len(column_dtypes))
        query = f"INSERT INTO {table_name} ({", ".join(column_dtypes.keys())}) VALUES ({data_substitude})"
        data = dataframe.reset_index().replace({np.nan:None,"NULL":None}).to_numpy().tolist()
        self.cursor.executemany(query,data)
        #print(f"added {table_name} to {database}")

        #make key autoincrement
        if(len(dataframe.index.levels)==1):
            query = f"ALTER TABLE {table_name} MODIFY {dataframe.index.names[0]} INT AUTO_INCREMENT"
            self.cursor.execute(query)
        self.connector.commit()

    def convert_to_multiindex(self, df):
        if(type(df.index) != pd.MultiIndex):
            df.index = pd.MultiIndex.from_arrays([df.index], names=[df.index.name])


    def create_foreign_key(self, table1, table2, column_name, primary_key):
        query = f"""
            ALTER TABLE {table1} 
            ADD CONSTRAINT fk_{table1}_{column_name} 
            FOREIGN KEY ({column_name}) 
            REFERENCES {table2}({primary_key})
        """
        self.cursor.execute(query)
    
    def update_string_to_date(self, table, column):
        query = f"UPDATE {table} SET {column} = STR_TO_DATE({column}, '%d/%m/%Y')"
        self.cursor.execute(query)
        query = f"ALTER TABLE {table} MODIFY COLUMN {column} DATE"
        self.cursor.execute(query)
    
    def create_schema(self, tables):
        try:
            database_name = self.config["local_database_name"]
            #self.create_database(database_name)
            for k, v in tables.items():
                self.convert_to_multiindex(v)
                self.create_table(v,k,database_name)
            self.data_standadization()
            return True

        except Exception as e:
            print("Load failed")
            return False

    def data_standadization(self):
        #foreign key requires both tables to exist
        self.create_foreign_key("products", "categories", "category_id", "category_id")
        self.create_foreign_key("products", "brands", "brand_id", "brand_id")
        self.create_foreign_key("orders", "customers", "customer_id", "customer_id")
        self.create_foreign_key("orders", "staffs", "staff_id", "staff_id")
        self.create_foreign_key("staffs", "staffs", "manager_id", "staff_id")
        self.create_foreign_key("staffs", "stores", "store_id", "store_id")
        self.create_foreign_key("stocks", "products", "product_id", "product_id")
        self.create_foreign_key("stocks", "stores", "store_id", "store_id")
        self.create_foreign_key("order_items", "orders", "order_id", "order_id")
        self.create_foreign_key("order_items", "products", "product_id", "product_id")
        self.create_foreign_key("orders", "stores", "store_id", "store_id")

        #pandas does not support dates without time therefore dtype is changed after creation in SQL
        self.update_string_to_date("orders", "order_date")
        self.update_string_to_date("orders", "required_date")
        self.update_string_to_date("orders", "shipped_date")
    
    def commit(self):
        self.connector.commit()

    def __del__(self):
        self.connector.commit()
        self.connector.close()