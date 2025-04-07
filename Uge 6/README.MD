The goal of this program is to perform an ETL process. 
Here we gather data from multiple sources. Perform transformations to normalize the data and store it in a database.  
sources:  
 - CSV  
    read locally from file

 - SQL  
    server at the time of writing:  
    ip: 192.168.20.171  
    port: 3306  
    username: curseist  

 - API  
    server at the time of writing:  
    ip: 192.168.20.171  
    port: 8000  
    
Tables:
|order_items(API)|customers(API)|orders(API)|stocks(SQL)|product(SQL)|category(SQL)|brands(SQL)| staffs.csv | stores.csv
|-|-|-|-|-|-|-|-|-|
|order_id|first_name|order_id|store_name|product_id|category_id| brand_id | name | name |
|item_id|last_name|customer_id|product_id|product_name|category_name| brand_name | last_name | phone |
|product_id|phone|order_status|quantity|brand_id||| email | email |
|quantity|email|order_date||category_id||| phone | street |
|list_price|street|required_date||model_year||| active | city |
|discount|city|shipped_date||||| store_name | state |
||state|store||||| street | zip_code |
||zip_code|staff_name||||| manager_id ||

target database   
    the target is a mysql database on the local machine
    ip: localhost
    port: 3306

Transformations
 - key restructuring
    a key column has been added to both staffs and stores. These keys use 1 indexing. 
    1 indexing has been chosen as this is what all other tables uses. Additionally staffs already has a refrence to manager ID which is also 1 indexed

    All refrences to store name and staff name from other tables have been altered such that they refrence the id instead

    
 - Data Standardization  
    Product names have been simplified to not include information that can be gathered from other columns. brand name and year have been removed from the name.

    Phone numbers is have their formatting removed and country code has been added +1 in this case for all data

 - Null Handling
    cases of null is represented as stings "NULL" and will be replaced by empty values.
 - Data Types 
    dates have been converted from strings of format dd/mm/yyyy into mysql Date

    floats have been converted to decimal(16,2) which means the maximum number supported is 999 Trillion. While this may be on the larger side it is expected it is easier to reduce this later than it would be to fix any issues that could arise from not having enough presision.

Final ERD Diagram
![Entity-Relationship Diagram png](ERD.png)
    