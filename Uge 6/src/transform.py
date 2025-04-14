import re
import pandas as pd

#renames all dataframe indexes to correct table key (multiindex in case of composite key)
def key_restructuring(tables):
    #rename index to key
    tables["stores"].index.rename("store_id", inplace = True)
    tables["staffs"].index.rename("staff_id", inplace = True)

    #change to 1-indexing
    tables["stores"].index += 1
    tables["staffs"].index += 1

    #change column to key
    tables["orders"].set_index("order_id", inplace = True)
    tables["customers"].set_index("customer_id", inplace = True)

    tables["brands"].set_index("brand_id", inplace = True)
    tables["categories"].set_index("category_id", inplace = True)
    tables["products"].set_index("product_id", inplace = True)

    #rename forgein keys to use id instead of name
    #store id
    stores_mapping = tables["stores"]["name"].to_dict()
    stores_mapping = {v:k for k,v in stores_mapping.items()}

    tables["stocks"]["store_id"] = tables["stocks"]["store_name"].map(stores_mapping)
    tables["stocks"].drop(["store_name"], axis = 1, inplace = True)

    tables["orders"]["store_id"] = tables["orders"]["store"].map(stores_mapping)
    tables["orders"].drop(["store"], axis = 1, inplace = True)

    tables["staffs"]["store_id"] = tables["staffs"]["store_name"].map(stores_mapping)
    tables["staffs"].drop(["store_name"], axis = 1, inplace = True)

    #staff id
    staffs_mapping = tables["staffs"]["name"].to_dict()
    staffs_mapping = {v:k for k,v in staffs_mapping.items()}

    tables["orders"]["staff_id"] = tables["orders"]["staff_name"].map(staffs_mapping)
    tables["orders"].drop(["staff_name"], axis = 1, inplace = True)

    #set composite keys after renamed foreign keys
    tables["order_items"].set_index(["order_id","product_id"],inplace = True) 
    tables["stocks"].set_index(["store_id", "product_id"], inplace = True) 

    #drop other unnecessary columns
    #equals to stores["street"]
    tables["staffs"].drop(["street"], axis = 1, inplace = True) 

    #not needed as order_id and product_id works as a key
    tables["order_items"].drop(["item_id"], axis = 1, inplace = True)

def product_rename(dataframe):
    regex = r"^[a-zA-Z0-9]+ (.*) - [\d/]+"
    dataframe["product_name"] = dataframe["product_name"].str.replace(regex, r"\1",regex = True)

def replace_phone_number(dataframe, column):
    def replace_function(string):
        if(string == "NULL"): return string
        return("+1"+"".join(re.findall(r'\d', string)))
    dataframe[column] = dataframe[column].map(replace_function)

def convert_to_multiindex(df):
    if(type(df.index) != pd.MultiIndex):
        df.index = pd.MultiIndex.from_arrays([df.index], names=[df.index.name])

def transform_tables(tables):
    key_restructuring(tables)
    tables["staffs"]["manager_id"] = tables["staffs"]["manager_id"].astype('Int64')

    product_rename(tables["products"])

    replace_phone_number(tables["customers"],"phone")
    replace_phone_number(tables["staffs"],"phone")
    replace_phone_number(tables["stores"],"phone")

    for k, v in tables.items():
        convert_to_multiindex(v)