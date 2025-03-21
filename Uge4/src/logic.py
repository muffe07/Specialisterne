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

    def create_table_from_database(self, database_table):

        dataframe = self.crud.read_table(database_table)
        self.gui.create_table(dataframe)
        self.current_dataframe = dataframe
        self.table_name = database_table

    def slice_from_widget(self, widget, entire_row = False, entire_column = False):
        data = self.current_dataframe
        if(not entire_row):
            data = data.iloc[:, [widget.grid_info()["column"]]]
        if(not entire_column):
            data = data.iloc[[widget.grid_info()["row"]]]
        return data

    def open_file(self):
        current_path = Path(filedialog.askopenfilename())
        self.crud.create_table_from_csv(current_path, replace = True)
        self.create_table_from_database(current_path.stem)

    def delete_row(self,new_window,widget):
        data = self.slice_from_widget(widget,entire_row = True)
        self.crud.delete_rows(self.table_name, data)
        new_window.destroy()
        self.gui.update_table()

    def add_row(self, popup_window, widget, offset = 0):
        dataframe = self.slice_from_widget(widget, entire_row = True)
        popup_window.destroy()
        dataframe.iloc[:,0] = max(self.current_dataframe.iloc[:,0])+1
        self.crud.append_dataframe(self.table_name, dataframe)
        self.gui.update_table()

    def update_cell(self, cell_string: str, row: int, column: int):
        #column_name = self.current_dataframe.columns.values[column_name]

        key_column = self.current_dataframe.columns.values[0]
        key = self.current_dataframe.loc[[row],[key_column]]
        column_name = self.current_dataframe.columns.values[column]


        data = pd.DataFrame([[cell_string]], columns = [column_name], index = key.values[0])
        self.crud.update_rows(self.table_name,data,key)

if (__name__ == "__main__"):
    Logic()