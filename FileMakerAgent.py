import pyodbc

# Build your connection string
dsn_name = "FileMakerAccess"
server_name = "localhost"
db_name = "Assets"
user = "Admin"
password = "password"
conn_str = f'DSN={dsn_name};UID={user};PWD={password}'

query_str = """
 SELECT A.Name AS AssetName, A.Description AS AssetDescription , V.Name AS VendorName, T.Note AS AssignmentNote, T.\"Date Returned\", E.\"First Name\" AS EmployeeFirstName, E.\"Last Name\" AS EmployeeLastName
 FROM Employees AS E
 JOIN Assignments AS T ON E.PrimaryKey = T.EmployeeForeignKey
 JOIN Assets AS A ON A.PrimaryKey = T.AssetForeignKey
 LEFT JOIN Vendors AS V ON T.AssetForeignKey = V.ForeignKey
 ORDER BY T.EmployeeForeignKey
 FETCH FIRST 1000 ROWS ONLY
 """

# Connect and execute
with pyodbc.connect(conn_str) as conn:
    cursor = conn.cursor()
    cursor.execute(query_str)
    for row in cursor:
        print(row)
