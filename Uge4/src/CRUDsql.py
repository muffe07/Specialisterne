import pandas as pd
from pathlib import Path
from SqlConnector import SqlConnector
import numpy as np
import re

class CRUDsql:
    def __init__(self):
        self.conn = SqlConnector("Uge2DB").authenticate()
        self.cursor = self.conn.cursor()

    def validate_expression(self, string):
        match_variable = r"[A-Za-z][A-Za-z0-9]*"
        match_comparison = r"[=!<>]+|LIKE|IN"
        match_string = r".+"

        match = re.match(f"^\\s*({match_variable})\\s*({match_comparison})\\s*({match_string})\\s*$",string)
        if(not match): raise Exception("invalid expression")

    def validate_string(self, string, error_message):
        match = re.match(r"^[A-Za-z][A-Za-z0-9_]*$",string)
        if(not match): raise Exception(error_message)
    
    def validate_iterable(self, iter, error_message):
        for i in iter:
            self.validate_string(i, error_message)
    

    def append_dataframe(self, table_name, dataframe):
        header = ", ".join(dataframe.columns.values)
        data_substitute = ", ".join(["%s"]*len(dataframe.columns))
        query = f"INSERT INTO {table_name} ({header}) VALUES ({data_substitute})"

        self.cursor.executemany(query,dataframe.to_numpy().tolist())

    def create_table_from_csv(self, file_name, replace = False):
        data_path = Path(__file__).parent.parent.joinpath("data")
        with open(data_path.joinpath(file_name)) as csv_file:
            table_name = file_name.split(".")[0]
            self.validate_string(table_name, "can't convert filename to tablename (filename must be formatted as tablename.csv)")

            dataframe = pd.read_csv(csv_file)
            headers = dataframe.columns.values
            self.validate_iterable(headers, "invalid header")

            pandas_to_msql_dtype = {
                np.dtype('int64'): "INT",  
                np.dtype('float64'): "FLOAT"
            }
            schema = []
            for name, dtype in zip(headers,dataframe.dtypes):
                schema.append(f"{name} {pandas_to_msql_dtype.get(dtype, "VARCHAR(255)")}")
            schema[0]+=" PRIMARY KEY"
            schema = ", ".join(schema)

            if(replace): 
                self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema});")
            self.append_dataframe(table_name, dataframe)

    def delete_table(self, table_name):
        self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        

    def read_table(self, table_name, expression = None, orderby = None):
        query = f"SELECT * FROM {table_name}"

        if(expression):
            self.validate_expression(expression)
            query+=f" WHERE {expression}"

        if(orderby):
            self.validate_string(orderby, "order by only supports simple columns_names")
            query+=f" ORDER BY {orderby}"

        self.cursor.execute(query)
        header = [i[0] for i in self.cursor.description]
        return(pd.DataFrame(self.cursor.fetchall(),columns = header))

    def delete_rows(self, table_name, expression = None):
        if(expression):
            self.validate_expression(expression)
            self.cursor.execute(f"DELETE FROM {table_name} WHERE {expression}")
        else:
            self.cursor.execute(f"DELETE FROM {table_name}")

    def update_rows(self, table_name, dataframe):
        primary_key = dataframe.columns.values[0]
        keys = tuple(dataframe[primary_key])
        self.delete_rows(table_name,expression = f"{primary_key} IN {str(keys)}")
        self.append_dataframe(table_name, dataframe)

    def __del__(self):
        self.conn.commit()

def main():
    interface = CRUDsql()

    try:
        pass
        interface.create_table_from_csv("malicious.csv", replace = True)
    except Exception as e:
        pass

    interface.create_table_from_csv("orders_combined.csv", replace = True)
    interface.create_table_from_csv("orders.csv", replace = True)

    interface.delete_table("customers")
    interface.create_table_from_csv("customers.csv", replace = False)
    print(interface.read_table("customers"))
    interface.create_table_from_csv("products.csv", replace = True)
    interface.delete_rows("orders_combined", "ID>10")

    new_data = pd.DataFrame(
        [
            (4,None,28,3),
            (5,None,29,5)
        ],
        columns = ["id", "date_time", "customer", "product"]
    )

    interface.update_rows("orders",new_data)
    print(interface.read_table("orders"))


if __name__ == "__main__":
    main()
