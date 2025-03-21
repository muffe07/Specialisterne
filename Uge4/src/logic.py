from GUI import GUI
from CRUDsql import CRUDsql
from tkinter import filedialog
from pathlib import Path
import pandas as pd

class Logic:
    def __init__(self):
        self.gui = GUI(self)
        self.crud = CRUDsql()
        self.current_dataframe = None
        self.table_name = None
        self.gui.run()


    def open_file(self):
        current_path = Path(filedialog.askopenfilename())
        self.crud.create_table_from_csv(current_path, replace = True)
        self.create_table_from_database(current_path.stem)


    def create_table_from_database(self, database_table:pd.DataFrame):
        dataframe = self.crud.read_table(database_table)
        self.gui.create_table(dataframe)
        self.current_dataframe = dataframe
        self.table_name = database_table


    def open_file(self):
        current_path = Path(filedialog.askopenfilename())
        self.crud.create_table_from_csv(current_path, replace = True)
        self.create_table_from_database(current_path.stem)


    def delete_row(self,dataframe):
        self.crud.delete_rows(self.table_name, dataframe)


    def add_row(self, dataframe):
        dataframe.iloc[:,0] = max(self.current_dataframe.iloc[:,0])+1
        self.crud.append_dataframe(self.table_name, dataframe)


    def update_cell(self, cell_string: str, row: int, column: int):
        column_name = self.current_dataframe.columns.values[column]
        key = self.current_dataframe.iloc[[row],[0]]
        data = pd.DataFrame([[cell_string]], columns = [column_name], index = key.values[0])

        keys = pd.DataFrame(key.values, columns = key.columns, index = key.values[0])
        self.crud.update_rows(self.table_name,data,keys)


if (__name__ == "__main__"):
    Logic()