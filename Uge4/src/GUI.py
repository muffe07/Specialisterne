import tkinter as Tk
from tkinter import ttk
from tkinter import Text


class GUI:
    def __init__(self, logic_instance):
        self.root = Tk.Tk()
        self.logic = logic_instance

        self.create_title_bar()
        self.table_frame = None
        self.header = None


    def create_title_bar(self):
        ttk.Button(self.root, text = "import csv",command = self.logic.open_file).grid(row = 0, column = 0)
        ttk.Button(self.root, text = "open sql",command = self.create_selection_menu).grid(row = 1, column = 0)

    def create_table(self,dataframe):
        if(self.table_frame): 
            self.table_frame.destroy()
        if(self.header):
            for i in self.header:
                i.destroy()
        
        height,width = dataframe.shape

        self.header = []
        grid = []
        for x,column_name in enumerate(dataframe.columns.values):
            T = Text(self.root, height = 1, width = 8)
            T.insert(1.0, column_name) 
            T.grid(row = 0, column = x+1)
            self.header.append(T)

        self.table_frame = Tk.Frame(self.root)
        self.table_frame.grid(row = 1, column = 1, rowspan = height, columnspan = width)
        for x in range(width):
            for y in range(height):
                T = Text(self.table_frame, height = 1, width = 8)
                T.insert(1.0, dataframe.iloc[y,x])
                T.bind("<Return>", self.on_return_pressed)
                T.bind("<Button-3>", self.create_click_menu)
                T.grid(row = y, column = x)
                grid.append(T)


    def slice_from_widget(self, widget, entire_row = False, entire_column = False):
        data = self.logic.current_dataframe
        if(not entire_row):
            data = data.iloc[:, [widget.grid_info()["column"]]]
        if(not entire_column):
            data = data.iloc[[widget.grid_info()["row"]]]
        return data


    def delete_row(self,new_window,widget):
        dataframe = self.slice_from_widget(widget,entire_row = True)
        new_window.destroy()
        self.logic.delete_row(dataframe)
        self.update_table()


    def add_row(self, popup_window, widget):
        dataframe = self.slice_from_widget(widget, entire_row = True)
        popup_window.destroy()
        self.logic.add_row(dataframe)
        self.update_table()


    def button_clicked(self, event, table_name:str, root):
        root.destroy()
        self.logic.create_table_from_database(table_name)
    

    def create_selection_menu(self):
        table_names = self.logic.crud.get_database_tables()
        popup = Tk.Toplevel(self.root)
        for index, table_name in enumerate(table_names):
            button = ttk.Button(popup, text = table_name)
            button.bind("<Button-1>",lambda e, t=table_name: self.button_clicked(e, t, popup))
            button.grid(row = index, column=0)


    

    def update_table(self):
        self.table_frame.destroy()
        self.logic.create_table_from_database(self.logic.table_name)


    def create_click_menu(self, event):
        popup = Tk.Toplevel(self.root)
        options = {
            "Delete row": lambda e: self.delete_row(popup, event.widget),
            "Dublicate row":lambda e: self.add_row(popup, event.widget),
        }
        for i, (name, method) in enumerate(options.items()):
            button = ttk.Button(popup, text = name)
            button.bind("<Button-1>",method) 
            button.grid(row = i, column = 0)


    def on_return_pressed(self,event):
        widget = event.widget
      
        #reads reads a text widget
        cell_string = event.widget.get("1.0",'end-1c') 

        column_index = widget.grid_info()["column"]
        row_index = widget.grid_info()["row"]

        self.logic.update_cell(cell_string, row_index, column_index)
        #break to prevent <return> becomming a newline in the text box
        return "break" 


    def run(self):
        self.root.mainloop()