from CRUDsql import CRUDsql
import tkinter as Tk
from tkinter import ttk
from tkinter import Text
from tkinter import filedialog
from pathlib import Path
import pandas as pd
import numpy as np


class GUI:
    def __init__(self):
        self.max_height = 20
        self.max_width = 5
        self.crud = CRUDsql()
        self.root = Tk.Tk()
        self.current_dataframe = None

        self.create_title_bar()

    def create_title_bar(self):
        ttk.Button(self.root, text = "import csv",command = self.open_file).grid(row = 0, column = 0)
        ttk.Button(self.root, text = "open sql",command = self.create_selection_menu).grid(row = 1, column = 0)

    def open_file(self):
        current_path = Path(filedialog.askopenfilename())
        self.crud.create_table_from_csv(current_path, replace = True)
        self.create_table_from_database(current_path.stem)

    def button_clicked(self,event, table_name, root):
        root.destroy()
        self.create_table_from_database(table_name)
    
    def create_selection_menu(self):
        table_names = self.crud.get_database_tables()
        popup = Tk.Toplevel(self.root)
        for index, table_name in enumerate(table_names):
            button = ttk.Button(popup, text = table_name)
            button.bind("<Button-1>",lambda e, t=table_name: self.button_clicked(e, t, popup))
            button.grid(row = index, column=0)

    def destroy_table(self, grid):
        for i in grid:
            for j in i:
                j.destroy()

    def create_table(self,dataframe):
        height,width = dataframe.shape

        header = []
        grid = []
        for x,column_name in enumerate(dataframe.columns.values):
            T = Text(self.root, height = 1, width = 8)
            T.insert(1.0, column_name) 
            T.grid(row = 0, column = x+1)
            header.append(T)

        self.table_frame = Tk.Frame(self.root)
        self.table_frame.grid(row = 1, column = 1, rowspan = min(height,self.max_height), columnspan = min(width,self.max_width))
        for x in range(width):
            for y in range(height):
                T = Text(self.table_frame, height = 1, width = 8)
                T.insert(1.0, dataframe.iloc[y,x])
                T.bind("<Return>", self.on_enter_pressed)
                T.bind("<Button-3>", self.create_click_menu)
                T.grid(row = y, column = x)
                grid.append(T)
        return(header, grid)

    def slice_from_widget(self, widget, entire_row = False, entire_column = False):
        data = self.current_dataframe
        if(not entire_row):
            data = data.iloc[:, [widget.grid_info()["column"]]]
        if(not entire_column):
            data = data.iloc[[widget.grid_info()["row"]]]
        return data
    
    def update_table(self):
        self.table_frame.destroy()
        self.create_table_from_database(self.table_name)

    def delete_row(self,new_window,widget):
        data = self.slice_from_widget(widget,entire_row = True)
        self.crud.delete_rows(self.table_name, data)
        new_window.destroy()
        self.update_table()

    def add_row(self, new_window, widget, offset = 0):
        dataframe = self.slice_from_widget(widget, entire_row = True)
        new_window.destroy()
        dataframe.iloc[:,0] = max(self.current_dataframe.iloc[:,0])+1
        self.crud.append_dataframe(self.table_name, dataframe)
        self.update_table()

    def create_click_menu(self, event):
        #create right_click menu
        popup = Tk.Toplevel(self.root)
        options = {
            "Delete row": lambda e: self.delete_row(popup,event.widget),
            "Dublicate row":lambda e: self.add_row(popup, event.widget),
        }
        for i, (name, method) in enumerate(options.items()):
            button = ttk.Button(popup, text = name)
            button.bind("<Button-1>",method) 
            button.grid(row = i, column = 0)

    def on_enter_pressed(self,event):
        widget = event.widget
        
        cell_string = event.widget.get("1.0",'end-1c')

        column = self.current_dataframe.columns.values[widget.grid_info()["column"]]
        key_column = self.current_dataframe.columns.values[0]
        row = widget.grid_info()["row"]

        key = self.current_dataframe.loc[[row],[key_column]]
        data = pd.DataFrame([[cell_string]], columns = [column], index = key.values[0])

        self.crud.update_rows(self.table_name,data,key)
        return "break"

    def confirm_selection(self, text_widget):
        print(text_widget.grid_info())

    def create_table_from_database(self, database_table):
        dataframe = self.crud.read_table(database_table)
        self.current_dataframe = dataframe
        self.create_table(dataframe)
        self.table_name = database_table
    
    def run(self):
        self.root.mainloop()

def main():
    gui = GUI()
    gui.run()

if (__name__ == "__main__"):
    main()