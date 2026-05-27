SELECT DISTINCT
    Assets.Name AS Asset,
    Vendors.Name AS Vendor,
    Employees.[First Name] + ' ' + Employees.[Last Name] AS Employee,
    Assignments.[Date Returned] AS DateReturned
FROM
    Vendors
    RIGHT JOIN (
        (
            Assignments
            INNER JOIN Employees ON Assignments.EmployeeForeignKey = Employees.PrimaryKey
        )
        INNER JOIN Assets ON Assignments.AssetForeignKey = Assets.PrimaryKey
    ) ON Vendors.ForeignKey = Assets.PrimaryKey
ORDER BY
    Employees.[First Name] + ' ' + Employees.[Last Name];

-------------------------------------------------------------

SELECT
    PrimaryKey,
    Count(*) AS Q
FROM
    Assets
GROUP BY
    PrimaryKey
ORDER BY
    PrimaryKey DESC;

-------------------------------------------------------------

SELECT
    Name,
    Count(*) AS Q
FROM
    Assets
GROUP BY
    Name
ORDER BY
    Name DESC;

-------------------------------------------------------------

SELECT
    Assets.Name,
    Vendors.Name
FROM
    Vendors
    INNER JOIN Assets ON Vendors.ForeignKey = Assets.PrimaryKey;

-------------------------------------------------------------

SELECT
    AssetForeignKey,
    EmployeeForeignKey,
    Count(*) AS Q
FROM
    Assignments
GROUP BY
    AssetForeignKey,
    EmployeeForeignKey
ORDER BY
    AssetForeignKey,
    EmployeeForeignKey DESC;

-------------------------------------------------------------

SELECT
    [Date Returned],
    Name
FROM
    Assignments
ORDER BY
    [Date Returned] DESC;

-------------------------------------------------------------

SELECT DISTINCT
    Assignments.EmployeeForeignKey,
    Employees.PrimaryKey
FROM
    Employees
    INNER JOIN Assignments ON Employees.PrimaryKey = Assignments.EmployeeForeignKey
ORDER BY
    Employees.PrimaryKey;

-------------------------------------------------------------

SELECT
    PrimaryKey,
    Count(*) AS Q
FROM
    Employees
GROUP BY
    PrimaryKey
ORDER BY
    PrimaryKey DESC;

-------------------------------------------------------------

SELECT DISTINCT
    [First Name],
    [Last Name]
FROM
    Employees;

-------------------------------------------------------------

SELECT
    Name,
    Count(*) AS Q
FROM
    Vendors
GROUP BY
    Name
ORDER BY
    Name DESC;