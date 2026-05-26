import os
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

fm_query_str = """
 SELECT DISTINCT A.Name AS Asset, V.Name AS Vendor, CAST(T.\"Date Returned\" AS VARCHAR) AS Returned, E.PrimaryKey AS Employee
 FROM Employees AS E
 JOIN Assignments AS T ON E.PrimaryKey = T.EmployeeForeignKey
 JOIN Assets AS A ON A.PrimaryKey = T.AssetForeignKey
 LEFT JOIN Vendors AS V ON T.AssetForeignKey = V.ForeignKey
ORDER BY
    E.PrimaryKey
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

# Map available tools to their actual Python functions
available_tools = {
    "execute_sql_query": execute_sql_query
}

# Define the Tool Schema for ChatGPT
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql_query",
            "description": "Fetch data required to answer user questions.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Agent Loop
def run_ai_agent(user_prompt: str):
    # Initialize conversation with system prompt
    messages = [
        {"role": "system", "content": """
         You are a helpful database assistant.
          You have access to a local database, which contains four tables,
          assets, assignments (of assets to employees), employees, and vendors. 
         Use the execute_sql_query tool to fetch a flattened view of all assets, assignments, employees, and vendors data to answer the user's questions.
         """},
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
                # function_args = json.loads(tool_call.function.arguments)
                # print(f"\n[Agent Action] Executing: {function_name} with args: {function_args}")
                print(f"\n[Agent Action] Executing: {function_name}")
                
                # Execute the local ODBC function
                # function_response = function_to_call(query=function_args.get("query"))
                function_response = function_to_call()

                # Print snippet of result
                print(f"[Agent Observation] Data fetched: {function_response[:200]}...") 
                
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

# Run the Agent
if __name__ == "__main__":
    user_questions = ["How many employees have an undefined returned date?",
    "How many assets have vendors?",
    "How many employees have multiple assets assigned to them?",
    "How many assets are assigned to multiple employees?",
    "What is the date today?",
    "How many assigned assets have a defined return date before today?",
    "How many assigned assets have a defined return date after today?"]

    for user_question in user_questions: 
        print(f"User: {user_question}")    
        answer = run_ai_agent(user_question)
        print(f"Response:\n{answer}")
