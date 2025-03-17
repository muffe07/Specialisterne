import pandas as pd
from pathlib import Path
import MySqlConnector
from sqlalchemy import text

class CRUDsql:
    def __init__():
        pass

    def create_table_from_csv(filename, conn):
        data_path = Path(__file__).parent.parent.joinpath("data")
        with open(data_path.joinpath(filename)) as csv_file:
            table_name = filename.split(".")[0]
            dataframe = pd.read_csv(csv_file)
            dataframe.to_sql(name = table_name, con = conn, if_exists="replace", index = False)

    def read_table(table_name, conn):
        return(pd.read_sql_table(table_name = table_name,con = conn))

    def delete_table(table_name, conn):
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        conn.commit()

    def main():
        with MySqlConnector.MySqlConnector("Uge2DB") as conn:
            create_table_from_csv("orders_combined.csv", conn)
            create_table_from_csv("orders.csv",conn)
            create_table_from_csv("customers.csv",conn)
            create_table_from_csv("products.csv",conn)

            read_table("orders_combined", conn)
            delete_table("orders_combined", conn)

if __name__ == "__main__":
    main()
