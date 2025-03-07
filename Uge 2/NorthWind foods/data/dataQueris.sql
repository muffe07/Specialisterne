use northwind;

/*
select * from 
(select * from orders) as a
join
(select * from orderdetails) as b
on a.orderID = b.orderID
*/
/*
select shipcountry, sum(unitprice * quantity) as totalprice from 
(select * from orders) as a
join
(select * from orderdetails) as b
on a.orderID = b.orderID
group by shipcountry
*/
/*
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
*/
