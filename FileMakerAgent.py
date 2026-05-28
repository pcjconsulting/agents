import os
import json
import pyodbc
from openai import OpenAI
from FmRelationshipsSchema import RelationshipsSchema
from FmTablesSchema import TablesSchema

# Configuration
# OPENAI_API_KEY = "sk-proj-DesK9m...8_DkA"
dsn_name = "FileMakerAccess"
server_name = "localhost"
db_name = "Assets"
user = "Admin"
password = "password"
ODBC_CONNECTION_STRING = f'DSN={dsn_name};UID={user};PWD={password}'

content_message = """
You are a database analysis assistant. When answering a user's question you must ALWAYS follow this sequence strictly, and you must ALWAYS preform ALL the steps in this sequence:
1. Call the get_schema tool.
2. Analyze the table, column, and relationships schema provided in the tool response, to answer the user's question.
3. Call the execute_sql tool with a valid SQL query.
4. Analyze the dataset provided in the tool response, to answer the user's question.
NEVER guess column names or relationships, or execute a query, without first calling get_schema.
NEVER provide a text-based analysis of the data without first calling execute_sql.
"""


def get_schema() -> str:
    """
    Fetch the schema of database tables and relationships as a JSON-formatted string.
    """
    try:
        obj = RelationshipsSchema("Assets")
        relationships = obj.ReadFile()
        obj = TablesSchema("Assets")
        tables = obj.ReadFile()
        result = (f"{{ \"Tables\": {tables}, \"Relationships:\": {relationships} }}")
        return result
    
    except Exception as e:
        return f"Error reading database relationships schema: {str(e)}"


def get_relationships_schema() -> str:
    """
    Fetch the schema of database relationships as a JSON-formatted string.
    """
    try:
        obj = RelationshipsSchema("Assets")
        return obj.ReadFile()
    
    except Exception as e:
        return f"Error reading database relationships schema: {str(e)}"

def get_tables_schema() -> str:
    """
    Fetch the schema of database tables and their fields as a JSON-formatted string.
    """
    try:
        obj = TablesSchema("Assets")
        return obj.ReadFile()
    
    except Exception as e:
        return f"Error reading database tables schema: {str(e)}"


def execute_sql(query: str) -> str:
    """
    Executes the sql query, and returns a dataset as a JSON-formatted string.
    """
    try:
        with pyodbc.connect(ODBC_CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
        
            # Fetch results
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
                
        return json.dumps(results)
    
    except Exception as e:
        return f"Error executing database query: {str(e)}"


# Map available tools to their actual Python functions
available_tools = {
    "execute_sql": execute_sql,
    "get_schema": get_schema
    # "get_tables_schema": get_tables_schema,
    # "get_relationships_schema": get_relationships_schema
}

# Define the Tool Schema for ChatGPT
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": "Get the schema listing all tables and their columns and all relationships between tables specified by columns.  Call this initially to understand the entity relationships.",
            }
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "get_relationships_schema",
    #         "description": "Get the schema listing all relationships between tables specified by columns.  Call this initially to understand the entity relationships.",
    #         }
    # },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "get_tables_schema",
    #         "description": "Get the schema listing all tables and their columns.  Call this initially to understand the table structure.",
    #         }
    # },
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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Agent Loop
def run_agent_loop(user_prompt: str):
    try:
        # Initialize conversation with system prompt
        messages = [
            {"role": "system", "content": content_message},
            {"role": "user", "content": user_prompt}
        ]
        
        # Send user prompt and tool definitions to ChatGPT.
        response = client.chat.completions.create(
            model="gpt-5.5",
            messages=messages,
            tools=tools_definition,
            tool_choice="auto",
            parallel_tool_calls=False,
        )
        
        message = response.choices[0].message
        messages.append(message)
        
        # Check if ChatGPT decided to call a function.
        if message.tool_calls:
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_tools.get(function_name)
                
                if function_to_call:
                    function_args = json.loads(tool_call.function.arguments)
                    print(f"\n[Agent Action] Invoking: {function_name} with args: {function_args}")
                    
                    function_response = function_to_call(**function_args)

                    # Print snippet of result
                    print(f"[Agent Observation] Data fetched: {function_response[:200]}...") 
                    
                    # Append the function result to conversation memory.
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
                    
            # Send the fetched data back to ChatGPT to get a final answer.
            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            return final_response.choices[0].message.content 
        else:
            # ChatGPT didn't need the database, just return its text response.
            return message.content

    except Exception as e:
            return f"Error in agent loop: {str(e)}"


# Run the Agent
if __name__ == "__main__":
    user_questions = ["How many employees have an undefined returned date?",
    "How many assets have vendors?",
    "How many employees have multiple assets assigned to them?",
    "How many assets are assigned to multiple employees?",
    "What is the date today?",
    "How many assigned assets have a defined return date before today?",
    "How many assigned assets have a defined return date after today?"]

    # for user_question in user_questions: 
    #     print(f"User: {user_question}")    


    answer = run_agent_loop("How many employees have multiple assets assigned to them?")
    print(f"Response:\n{answer}")
