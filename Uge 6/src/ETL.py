import transform
from extract import Extract
from load import Load

if __name__ == "__main__":
    tables = Extract().get_data()
    transform.transform_tables(tables)
    Load().create_schema(tables)