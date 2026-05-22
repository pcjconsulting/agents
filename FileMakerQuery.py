import os
import json
import pyodbc


# Configuration
dsn_name = "FileMakerAccess"
server_name = "localhost"
db_name = "Assets"
user = "Admin"
password = "password"
ODBC_CONNECTION_STRING = f'DSN={dsn_name};UID={user};PWD={password}'

fm_query_str = """
 SELECT DISTINCT A.Name AS AssetName, V.Name AS VendorName, CAST(T.\"Date Returned\" AS VARCHAR) AS DateReturned, E.\"First Name\" AS EmployeeFirstName, E.\"Last Name\" AS EmployeeLastName
 FROM Employees AS E
 JOIN Assignments AS T ON E.PrimaryKey = T.EmployeeForeignKey
 JOIN Assets AS A ON A.PrimaryKey = T.AssetForeignKey
 LEFT JOIN Vendors AS V ON T.AssetForeignKey = V.ForeignKey
 ORDER BY T.EmployeeForeignKey
 FETCH FIRST 100 ROWS ONLY
 """


# Define the Database Tool
def execute_sql_query() -> str:
    """
    Returns a join of asset, assignment, employee, and vendor tables as a JSON-formatted string.
    """
    try:
        with pyodbc.connect(ODBC_CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            cursor.execute(fm_query_str)
        
            # Fetch results
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
                
        return json.dumps(results)
    except Exception as e:
        return f"Error executing database query: {str(e)}"


# Run the query
if __name__ == "__main__":
    
    answer = execute_sql_query()
    
    print(f"Response:\n{answer}")
