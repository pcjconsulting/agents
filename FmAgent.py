import os
import json
import pyodbc
from openai import OpenAI
from FmRelationshipsSchema import RelationshipsSchema
from FmTablesSchema import TablesSchema

content_message = """
You are a database analysis assistant. When answering a user's questions you must ALWAYS follow this sequence strictly, and you must ALWAYS perform ALL the steps in this sequence:
<start sequence>
1. Call the get_schema tool one time per conversation.
2. Use the table, column, and relationships schema provided in the get_schema tool response, to answer the user's questions.
3. For each of the user's questions, perform the following steps:
a. Call the execute_sql tool with a valid SQL query.
b. Analyze the dataset provided in the execute_sql tool response, to answer the user's question.
<end sequence>
You must apply these rules at all times:
NEVER guess column names or relationships.
ALWAYS use the response from get_schema to determine column names and relationships.
NEVER provide a text-based analysis of the data without first calling execute_sql.
"""

dsn_name = "FileMakerAccess"
server_name = "localhost"
db_name = "Assets"
user = "Admin"
password = "password"
ODBC_CONNECTION_STRING = f'DSN={dsn_name};UID={user};PWD={password}'

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_schema() -> str:
    """
    Fetch the schema of database tables and relationships as a JSON-formatted string.
    """
    try:
        relationships = RelationshipsSchema("Assets").ReadFile()
        tables = TablesSchema("Assets").ReadFile()
        result = (f"{{ \"Tables\": {tables}, \"Relationships:\": {relationships} }}")
        return result
    
    except Exception as e:
        return f"Error reading database relationships schema: {str(e)}"


def execute_sql(query: str) -> str:
    """
    Executes the sql query, and returns a dataset as a JSON-formatted string.
    """
    try:
        fm_query = query.replace(";", "").replace("]", r"\"").replace("[", r"\"")
        with pyodbc.connect(ODBC_CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            cursor.execute(fm_query)
        
            # Fetch results
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
                
        return json.dumps(results)
    
    except Exception as e:
        return f"Error executing database query: {str(e)}"

# Mapping dictionary for execution routing
tools_mapping = {
    "execute_sql": execute_sql,
    "get_schema": get_schema
}

# Declarative schema blueprints provided to OpenAI
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": "Get the schema listing all tables and their columns and all relationships between tables specified by columns.  Call this initially to understand the entity relationships.",
            }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "Execute a SQL SELECT query on the local ODBC database to gather data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The exact SQL query to execute (e.g., SELECT * FROM CUSTOMERS)."
                    }
                },
                "required": ["query"],
            },
        },
    }
]

def run_agent_turn(messages):
    """
    Submits a message history block to OpenAI.
    Handles potential tool calling phases before returning a natural language result.
    """
    # Use gpt-4o or gpt-4-turbo for complex SQL operations and tool calling reliability
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools_definition,
        tool_choice="auto",
        parallel_tool_calls=False
    )
    
    response_message = response.choices[0].message
    messages.append(response_message)
    
    # Process multiple tools sequentially if requested by the LLM
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_to_call = tools_mapping[function_name]
            function_args = json.loads(tool_call.function.arguments)
            
            # Execute the function and collect results
            print(f"   [Agent calling tool -> {function_name}({function_args})]")
            tool_output = function_to_call(**function_args)
            
            # Send the execution results back to ChatGPT
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": tool_output,
            })
        
        # Recursively run a follow-up turn so the model can process the tool data
        return run_agent_turn(messages)
    
    return response_message.content

# System prompt sets the constraints and instructions for operating safely
conversation_history = [
    {
        "role": "system", "content": content_message
    }
]

user_questions = [
    "Today's date June 8, 2026. How many assigned assets have a defined return date before today?",
    "How many assigned assets have a defined return date after today?",
    "How many employees have an undefined returned date?",
    "How many assets have vendors?",
    "List employees that have multiple assets assigned to them.",
    "List assets that are assigned to multiple employees."
]

for idx, user_question in enumerate(user_questions, 1):
    print(f"\nUser Question {idx}: {user_question}")
    
    # Append new user prompt into conversation memory
    conversation_history.append({"role": "user", "content": user_question})
    
    # Let the agent evaluate and resolve the answer
    answer = run_agent_turn(conversation_history)
    print(f"Agent Answer: {answer}")
