use northwind;

select a.table_name,a.column_name as primary_keys, b.column_list from
(select table_name,column_name from information_schema.key_column_usage where constraint_schema = 'northwind' and constraint_name = "PRIMARY") as a
join
(select table_name, group_concat(column_name separator ', ') as column_list
from information_schema.columns 
where table_schema = 'northwind' 
group by table_name) as b
on a.table_name = b.table_name;
