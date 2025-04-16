import os
from dotenv import load_dotenv
from langchain.sql_database import SQLDatabase
import google.generativeai as genai
from decimal import Decimal
from sqlalchemy import create_engine, inspect, text
import json  # Import the json module
import time

def load_environment_variables():
    """Loads API keys and database credentials from .env file."""
    load_dotenv()  # Load environment variables from .env file
    api_key = os.environ.get("GOOGLE_API_KEY")  # Get API key from environment
    if not api_key:
        raise ValueError(
            "Google API key not found in .env file. Set the GOOGLE_API_KEY variable."
        )
    db_uri = os.environ.get("DATABASE_URI")
    if not db_uri:
        raise ValueError(
            "Database URI not found in .env file. Set the DATABASE_URI variable."
        )

    return api_key, db_uri


def get_gemini_response(question, prompt, api_key):
    """Uses the Gemini model to generate SQL from a natural language question."""
    genai.configure(api_key=api_key)  # Ensure the API key is configured each call.
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    response = model.generate_content([prompt[0], question])
    return response.text


class CustomSQLDatabase(SQLDatabase):
    def get_columns_for_table(self, table_name):
        """Retrieves column names for a given table using the instance's engine."""
        inspector = inspect(self._engine)
        columns = inspector.get_columns(table_name)
        column_names = [col['name'] for col in columns]
        return column_names

    def get_table_count(self):
        """Returns the number of tables in the database."""
        inspector = inspect(self._engine)
        return len(inspector.get_table_names())

    def get_database_size(self):
        """Returns the approximate database size in MB for MySQL."""
        engine = self._engine  # use existing engine
        conn = engine.raw_connection()
        cursor = conn.cursor()
        try:
            if engine.dialect.name == 'mysql':
                db_name = engine.url.database
                cursor.execute(
                    f"SELECT SUM(data_length + index_length) / (1024 * 1024) FROM information_schema.TABLES WHERE table_schema = '{db_name}';"
                )
                size_mb = cursor.fetchone()[0]
                return round(size_mb, 2) if size_mb else 0.0
            else:
                return "N/A (Size estimation not implemented for this database type)"
        finally:
            cursor.close()
            conn.close()

    def get_execution_time(self, sql_query):
        """Executes a simple query and returns the execution time in seconds."""
        engine = self._engine
        try:
            start_time = time.time()
            with engine.connect() as connection:
                connection.execute(text(sql_query))  # Using text clause to protect from SQL injections
            end_time = time.time()
            return round(end_time - start_time, 3)
        except Exception as e:
            print(f"Error measuring execution time: {e}")
            return None


def get_db(db_uri):
    return SQLDatabase.from_uri(db_uri)


def get_prompt():
    prompt = [
        """
        You are a SQL generation assistant for a t-shirts inventory database. 
    Generate a SQL SELECT query that fetches only the relevant fields asked by the user.

    DO:
    - Use only SELECT queries.
    - Select only the columns mentioned in the question (like `price`, `size`, `color`, `brand`) — do NOT use `t_shirt_id` unless explicitly asked.
    - Always filter using WHERE if conditions are given.
    - Use lowercase SQL syntax and backticks for table and column names.
    - The table is called `t_shirts`.

    DO NOT:
    - Do NOT select columns not asked (e.g., avoid `t_shirt_id` or `*` unless user says so).
    - Do NOT alias columns or add explanation.
    - Do NOT return anything other than SQL code.

    Examples:

    Q: List the price of all the white t-shirts from Nike Brand in all the sizes.
    A: SELECT `size`, `price` FROM `t_shirts` WHERE `brand` = 'Nike' AND `color` = 'white';

    Q: What colors are available for Puma?
    A: SELECT DISTINCT `color` FROM `t_shirts` WHERE `brand` = 'Puma';

    Q: Show me all stock data for large size.
    A: SELECT * FROM `t_shirts` WHERE `size` = 'large';

    Return only the SQL query. No explanation.
        """
    ]
    return prompt


def execute_sql_and_convert(db, sql_query):
    """Executes the SQL query and converts Decimal results to integers."""
    try:
        # Get raw result from the database
        result = db.run(sql_query)
        
        # If the result is empty, return an empty list
        if not result or result == "[]":
            return []
            
        # Convert Decimal values to integers/floats in the result
        converted_result = []
        
        # Parse the result string to a Python object
        rows = eval(result)  # Safe eval because result comes from SQLDatabase
        
        for row in rows:
            converted_row = []
            for item in row:
                if isinstance(item, Decimal):
                    converted_row.append(int(item) if item % 1 == 0 else float(item))
                else:
                    converted_row.append(item)
            converted_result.append(tuple(converted_row))
            
        return converted_result

    except Exception as e:
        return f"Error executing SQL: {e}"

if __name__ == "__main__":
    try:
        # Load environment variables
        api_key, db_uri = load_environment_variables()

        # Initialize the SQL database
        db = get_db(db_uri)

        # Get the prompt
        prompt = get_prompt()

        # Example question
        question = "How many t-shirts do we have left for Nike in extra small size and white color?"

        # Generate SQL query using Gemini
        sql_query = get_gemini_response(question, prompt, api_key)
        print(f"Generated SQL Query: {sql_query}")

        # Execute the SQL query and convert decimals
        result = execute_sql_and_convert(db, sql_query)
        print(f"Result: {result}")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
