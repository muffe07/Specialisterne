The goal of this program is to perform an ETL process. 
We gather data from multiple sources. Perform transformations to normalize the data and store it in a database.  

Sources:  
 - CSV  
    Read locally from ./data/

 - SQL  
    Server at the time of writing:  
    IP: 192.168.20.171  
    Port: 3306  
    Username: curseist  
    Database name: productdb

 - API  
    Server at the time of writing:  
    IP: 192.168.20.171  
    Port: 8000  
    
Local Database:  

    IP: localhost  
    Port: 3306  
    Username: root  
    Database name: bicycledb  

Tables:

|order_items(API)|customers(API)|orders(API)|stocks(SQL)|product(SQL)|category(SQL)|brands(SQL)| staffs.csv | stores.csv
|-|-|-|-|-|-|-|-|-|
|4722 rows|1445 rows|1615 rows|939 rows|321 rows|7 rows|9 rows|10 rows|3 rows|
|*-*|*-*|*-*|*-*|*-*|*-*|*-*|*-*|*-*|
|order_id|customer_id|order_id|store_name|product_id|category_id| brand_id | name | name |
|item_id|first_name|customer_id|product_id|product_name|category_name| brand_name | last_name | phone |
|product_id|last_name|order_status|quantity|brand_id||| email | email |
|quantity|phone|order_date||category_id||| phone | street |
|list_price|email|required_date||model_year||| active | city |
|discount|street|shipped_date||||| store_name | state |
||city|store||||| street | zip_code |
||state|staff_name||||| manager_id ||
||zip_code|||||||

Target database:  

    The target is a mysql database on the local machine.
    IP: localhost
    port: 3306

Transformations:

    one of the goals of these transformations is to convert the database to be 5th Normal form

    1st normal form:  
        - No duplicate rows (partially satisfied)
        - atomic values (already satisfied)
        - unique column names (already satisfied)  
        - indepentent of order (already satisfied)  

    2nd normal form:  
        - no partial dependency (already satisfied)  
    
    3rd normal form:  
        - no transitive depedency   

    4th normal form:  
        - no multi-valued dependencies  
    
    5th normal form:  
        - no join dependencies (already satisfied)

Main issues:  

    staff and store names are used as keys however these keys are not necessarily unique. This violates 1st normal form.  
    Before the ETL process its not possible to have 2 staff that has the same first name. Additionally its not possible to have 2 stores with the same name. Even though this might actually happen (multiple cities have the same name for example)

    Staff has a reference to street, and a reference to store. staffs street is the same as stores street. This violates 3rd normal form.  
    This is a cause for data duplication. If this is not fixed when you update. the data you could only update 1 instance. Creating contradictions in the dataset.

    Orders store and staffs store are the same this violates 3rd normal form if we assume they are the same. However this is not necesarrily always the case. If an order always has staff and order store and staff store are the same this column would need to be removed. However I assume orders can have null staff if it has not been processed yet.  

    Product name depends on brand and year. This violates 4th normal form.  
    This is an issue of data duplication. 



Changes:
 - Key restructuring  
    A key have been added to staffs and stores. These keys use 1-indexed. 
    1-indexing has been chosen as this is what all other tables uses. Additionally staffs already has a reference to manager ID which is also 1-indexed.

    All references to store name and staff name from other tables have been altered such that they reference the id instead.

 - Data Standardization  
    Product names have been simplified to not include information that can be gathered from other columns. brand name and year have been removed from the name.

    Phone numbers have their formatting removed and country code has been added. '+1' For all current data.

    Order items have their items_id column removed as its unnecesarry. The only information this column gives is what order items have been added to customers basket. This has been considered too arbitary to be useful. 
    If this information would be useful in future analytics, then it will require alot of additional information that needs to be collected anyways. 

    staff have their steet column removed as this street is not the street of their address but the street of the store they work in. As such the street is stored in the stores tables.

 - Null Handling  
    cases of null is represented as stings "NULL" and will be replaced by proper null values in the database.

 - Data Types  
    dates have been converted from strings of format dd/mm/yyyy into mysql Date

    floats have been converted to decimal(16,2) which means the maximum number supported is 999 Trillion. While this may be on the larger side it is expected it is easier to reduce this later than it would be to fix any issues that could arise from not having enough precision.


Performance:  
- Local SQL connection: 0.07s  
- Remote SQL connection: 0.08s  
- Retrive data: 0.34s  
- restructere keys: 0.01s  
- standardize data: 0.00s  
- Create schema: 0.59s  
- Added foreign keys constraints: 0.50s  
- Changed date datatypes: 0.21s  

Total time usage: 1.80s.

Most performance is as expected except foreign keys and date datatypes. 2ommon for these 2 functions is that they alter the tables after creation. Foreign keys requires 2 tables to exist.
For the date; Pandas does not support the type needed in MySQL.



Final Entity-Relationship Diagram
![Entity-Relationship Diagram png](ERD.png)
    