import json
import pyodbc


class TablesSchema:
    def __init__(self, name):
        self.name = name
        self.json_file_path = "table-schema.json"
        self.dsn_name = "FileMakerAccess"
        self.server_name = "localhost"
        self.db_name = "Assets"
        self.user = "Admin"
        self.password = "password"
        self.ODBC_CONNECTION_STRING = f'DSN={self.dsn_name};UID={self.user};PWD={self.password}'
        self.fm_tables_query_str = "SELECT TableName FROM FileMaker_Tables"
        self.fm_fields_query_str  = "SELECT FieldName, FieldType FROM FileMaker_Fields"

# Configuration
# OPENAI_API_KEY = "sk-proj-DesK9m...8_DkA"

    def ReadFile(self) -> str:
        """
        Returns the schema of database tables and their fields as a JSON-formatted string.
        """
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as json_file:
                return json_file.read()

        except Exception as e:
            return f"Error reading file: {str(e)}"


    def CreateFile(self):
        """
        Creates the json file of the schema of database tables and their fields.
        """
        try:
            with pyodbc.connect(self.ODBC_CONNECTION_STRING) as conn:
                cursor = conn.cursor()

                # Fetch tables
                cursor.execute(self.fm_tables_query_str)
                table_properties = ["TableName", "Fields"]
                result = []
                for table in cursor.fetchall():
                    table_str = f"{table}"
                    table_name = table_str.replace(",","").replace("(", "").replace(")", "").replace("'", "")

                    # Fetch fields
                    sql_query = f"{self.fm_fields_query_str} WHERE TableName = '{table_name}'"
                    cursor.execute(sql_query)
                    rows = cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    table_fields = [dict(zip(columns, row)) for row in rows]
                    result.append(dict(zip(table_properties, [table_name, table_fields])))

            with open(self.json_file_path, 'w', encoding='utf-8') as json_file:
                json.dump(self.formatted_relationships, json_file, indent=4)

        except Exception as e:
            return f"Error executing database query: {str(e)}"
