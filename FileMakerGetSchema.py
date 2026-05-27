import json
import pyodbc
from openai import OpenAI


# Configuration
# OPENAI_API_KEY = "sk-proj-DesK9m...8_DkA"
dsn_name = "FileMakerAccess"
server_name = "localhost"
db_name = "Assets"
user = "Admin"
password = "password"
ODBC_CONNECTION_STRING = f'DSN={dsn_name};UID={user};PWD={password}'

fm_tables_query_str = "SELECT TableName FROM FileMaker_Tables"
fm_fields_query_str  = "SELECT FieldName, FieldType FROM FileMaker_Fields"

# Define the Database Tool
def execute_table_schema_query() -> str:
    """
    Returns the schema of database tables and their fields as a JSON-formatted string.
    """
    try:
        with pyodbc.connect(ODBC_CONNECTION_STRING) as conn:
            cursor = conn.cursor()

            # Fetch tables
            cursor.execute(fm_tables_query_str)
            table_properties = ["TableName", "Fields"]
            result = []
            for table in cursor.fetchall():
                table_str = f"{table}"
                table_name = table_str.replace(",","").replace("(", "").replace(")", "").replace("'", "")

                # Fetch fields
                sql_query = f"{fm_fields_query_str} WHERE TableName = '{table_name}'"
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                table_fields = [dict(zip(columns, row)) for row in rows]
                result.append(dict(zip(table_properties, [table_name, table_fields])))

        return json.dumps(result)

    except Exception as e:
        return f"Error executing database query: {str(e)}"


# Run the query
if __name__ == "__main__":
    
    answer = execute_table_schema_query()
    
    print(f"Response:\n{answer}")
