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


import os
import json
import pyodbc
from openai import OpenAI

# 1. Configuration
OPENAI_API_KEY = "your-openai-api-key-here"
# Example DSN-less connection string (e.g., for SQL Server)
# Change to 'DRIVER={PostgreSQL};... for Postgres'
ODBC_CONNECTION_STRING = "DSN=your_dsn_name;UID=user;PWD=password;DATABASE=your_db"

client = OpenAI(api_key=OPENAI_API_KEY)

# 2. Define the Database Tool
def execute_sql_query(query: str) -> str:
    """
    Executes a read-only SQL query against the local ODBC database 
    and returns the results as a JSON-formatted string.
    """
    try:
        conn = pyodbc.connect(ODBC_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Fetch results
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        
        cursor.close()
        conn.close()
        
        return json.dumps(results)
    except Exception as e:
        return f"Error executing database query: {str(e)}"

# Map available tools to their actual Python functions
available_tools = {
    "execute_sql_query": execute_sql_query
}

# 3. Define the Tool Schema for ChatGPT
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql_query",
            "description": "Run a SQL query on the local database to fetch data required to answer user questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The valid SQL query to execute. e.g., SELECT * FROM Users WHERE active=1",
                    }
                },
                "required": ["query"],
            },
        },
    }
]

# 4. Agent Loop
def run_ai_agent(user_prompt: str):
    # Initialize conversation with system prompt
    messages = [
        {"role": "system", "content": "You are a helpful database assistant. You have access to a local database. Use the execute_sql_query tool to fetch data needed to answer the user's questions."},
        {"role": "user", "content": user_prompt}
    ]
    
    # First turn: Send user prompt and tool definitions to ChatGPT
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools_definition,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    messages.append(response_message)
    
    # Check if ChatGPT decided to call a function
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_tools.get(function_name)
            
            if function_to_call:
                function_args = json.loads(tool_call.function.arguments)
                print(f"\n[Agent Action] Executing: {function_name} with args: {function_args}")
                
                # Execute the local ODBC function
                function_response = function_to_call(
                    query=function_args.get("query")
                )
                print(f"[Agent Observation] Data fetched: {function_response[:200]}...") # Print snippet of result
                
                # Add the function result to conversation memory
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
                
                # Second turn: Send the fetched data back to ChatGPT for a final answer
                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                )
                return final_response.choices[0].message.content
                
    else:
        # If ChatGPT didn't need the database, just return its text response
        return response_message.content

# 5. Run the Agent
if __name__ == "__main__":
    user_question = "How many total products do we have in our inventory?"
    print(f"User: {user_question}")
    
    answer = run_ai_agent(user_question)
    
    print(f"\nFinal Answer:\n{answer}")
