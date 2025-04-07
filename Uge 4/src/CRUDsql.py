import pandas as pd
from pathlib import Path
from SqlConnector import SqlConnector
import numpy as np
import re

class CRUDsql:
    def __init__(self):
        self.conn = SqlConnector("Uge2DB").authenticate()
        self.cursor = self.conn.cursor()

    #validates a string and makes sure it only supports safe sql characters
    def validate_string(self, string: str, error_message: str):
        match = re.match(r"^[A-Za-z][A-Za-z0-9_]*$",string)
        if(not match): raise Exception((error_message,string))
    

    def validate_iterable(self, iter: iter, error_message):
        for i in iter:
            self.validate_string(i, error_message)
    

    def append_dataframe(self, table_name:str, dataframe:pd.DataFrame):
        header = ", ".join(dataframe.columns.values)
        data_substitute = ", ".join(["%s"]*len(dataframe.columns))
        query = f"INSERT INTO {table_name} ({header}) VALUES ({data_substitute})"
        self.cursor.executemany(query,dataframe.to_numpy().tolist())


    def create_table_from_csv(self, file_path:Path, replace = False):
        table_name = file_path.name.split(".")[0]
        self.validate_string(table_name, "can't convert filename to tablename (filename must be formatted as tablename.csv)")
        with open(file_path) as csv_file:
            dataframe = pd.read_csv(csv_file)
            headers = dataframe.columns.values
            self.validate_iterable(headers, "invalid header")

            schema = []
            for name, dtype in zip(headers,dataframe.dtypes):
                schema.append(f"{name} VARCHAR(255)")
            schema[0]+=" PRIMARY KEY"
            schema = ", ".join(schema)

            if(replace): 
                self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.cursor.execute(f"CREATE TABLE {table_name} ({schema});")
            self.append_dataframe(table_name, dataframe)


    def delete_table(self, table_name:str):
        self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        

    def read_table(self, table_name:str, orderby = None):
        query = f"SELECT * FROM {table_name}"

        if(orderby):
            self.validate_string(orderby, "order by only supports simple column_names")
            query+=f" ORDER BY {orderby}"

        self.cursor.execute(query)
        header = [i[0] for i in self.cursor.description]
        data = pd.DataFrame(self.cursor.fetchall(),columns = header)
        return data


    def delete_rows(self, table_name:str, keys:pd.DataFrame):
        key = keys.columns.values[0]

        sql_keys = ", ".join([str(i) for i in keys[key].values])
        query = f"DELETE FROM {table_name} WHERE {key} IN ({sql_keys})"

        self.cursor.execute(query)


    #note key currently does not support composite keys and should therefore only have 1 column
    def update_rows(self, table_name:str, data:pd.DataFrame, keys:pd.DataFrame):
        assert data.index == keys.index, "row index must match"
        self.validate_iterable(data.columns.values, "invalid header")
        self.validate_iterable(keys.columns.values, "invalid header")

        set_value = ", ".join([f"{i} = %s" for i in data.columns.values])
        choose_row = ", ".join([f"{i} = %s" for i in keys.columns.values])
        query = f"UPDATE {table_name} SET {set_value} WHERE {choose_row}"

        self.cursor.executemany(query,pd.concat([data, keys],axis = 1).to_numpy().tolist())
    

    def commit(self):
        self.conn.commit()


    def __del__(self):
        self.conn.commit()


    def get_database_tables(self):
        self.cursor.execute(f"SHOW TABLES")
        return([table[0] for table in self.cursor.fetchall()])


def test():
    interface = CRUDsql()
    data_path = Path(__file__).parent.parent.joinpath("data")
    interface.create_table_from_csv(data_path.joinpath("orders.csv"), replace = True)
    assert interface.read_table("orders").shape==(100,4), "create or read error"
    interface.update_rows(
        "orders", 
        pd.DataFrame([["a", "b"]],columns = ["customer", "product"]),
        pd.DataFrame([["99"]],columns = ["id"])
        )
    new_line = (interface.read_table("orders").loc[99:])
    new_line["id"] = 100
    assert new_line["customer"].values[0] == "a", "update error"
    interface.append_dataframe("orders", new_line)
    assert interface.read_table("orders").shape==(101,4), "append error"

    try:
        interface.create_table_from_csv(data_path.joinpath("malicious.csv"), replace = True)
    except Exception as e:
        malicious_exception = True
    assert malicious_exception, "validation error"


if __name__ == "__main__":
    test()
