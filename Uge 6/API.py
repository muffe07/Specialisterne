from typing import Union
import polars as pl
from fastapi import FastAPI
from os.path import join
from pathlib import Path

app = FastAPI()

path = Path(__file__).parent/"API_data"
orders = pl.read_csv(join(path,"orders.csv"))
order_items = pl.read_csv(join(path,"order_items.csv"))
customers = pl.read_csv(join(path,"customers.csv"))

@app.get("/orders")
def read_orders():
    return orders.write_json()

@app.get("/order_items")
def read_order_items():
    return order_items.write_json()

@app.get("/customers")
def read_customers():
    return customers.write_json()
