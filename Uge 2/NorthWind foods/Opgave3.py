import mysql.connector 
from getpass import getpass
import pandas as pd
import matplotlib.pyplot as plt

try:
    mydb = mysql.connector.connect(
        host='localhost',
        user='root',
        password=getpass("password: ")
    )
except Exception as e:
    print("error connecting")
    exit()

mycursor = mydb.cursor()
mycursor.execute("use northwind;")

def country_shipping_graph(db):
    country_shipping_query = """
    select shipcountry, sum(unitprice * quantity) as totalprice from 
    (select * from orders) as a
    join
    (select * from orderdetails) as b
    on a.orderID = b.orderID
    group by shipcountry;
    """
    a = pd.read_sql(country_shipping_query, db)
    plt.bar(a["ShipCountry"],a["totalprice"])
    plt.xticks(rotation=90)
    plt.show()

def earnings_per_customer(db,entries_count):
    earnings_per_customer_query = """
    select customerid, sum(unitprice * quantity) as money_spent from 
    (select * from orders) as a
    join
    (select * from orderdetails) as b
    on a.orderID = b.orderID
    group by customerid
    order by sum(unitprice*quantity) desc
    """
    a = pd.read_sql(earnings_per_customer_query, db)
    if(entries_count>len(a)): entries_count = len(a)

    print(a)
    plt.bar(a.iloc[:entries_count,0],a.iloc[:entries_count,1])
    plt.xticks(rotation=90)
    plt.show()

def earnings_per_product(db,entries_count):
    earnings_per_product = """
    select c.productname,sum(b.unitprice*b.quantity) as revenue from
    (select * from orders) as a
    join
    (select * from orderdetails) as b
    on a.orderID = b.orderID
    join
    (select * from products) as c
    on b.productid = c.productid
    group by b.productid
    order by sum(b.unitprice*b.quantity) desc
    """
    a = pd.read_sql(earnings_per_product,db)
    plt.bar(a.iloc[:entries_count,0],a.iloc[:entries_count,1])
    plt.xticks(rotation=90)
    plt.show()
#earnings_per_customer(mydb,20)
earnings_per_product(mydb,20)