use northwind;

#2
#select * from products order by unitPrice desc;

#3
#select * from customers where country = "UK" or country = "Spain";

#4
#select * from products where unitsinstock>100 and unitprice>=25;

#5
#select shipcountry from orders group by shipcountry;

#6
#select * from orders where extract(year from orderdate) = 1996 and extract(month from orderdate) = 10;

#7
#select * from orders where shipregion is null and freight>=100 and employeeid = 1 and extract(year from orderdate) = 1996;

#8
#select * from orders where shippeddate>requireddate

#9
#select * from orders where orderdate between '1997-01-01' and '1997-05-01' and shipcountry = 'Canada';

#10
#select * from orders where employeeid in (2,5,8) and shipregion is not null and shipvia in (1,3) order by employeeid, shipvia;

#11
#select * from employees where region is null and birthdate<"1961-01-01";