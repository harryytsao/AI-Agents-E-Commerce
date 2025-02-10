import json
import psycopg2
from psycopg2.extras import Json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters (from Railway)
DB_URL = os.getenv('DATABASE_URL')

def connect_to_db():
    try:
        conn = psycopg2.connect(DB_URL)
        print("Connected to database successfully!")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def create_table(conn):
    # First drop the existing table if it exists
    drop_table_query = """
    DROP TABLE IF EXISTS products;
    """
    
    # Create new table with proper structure
    create_table_query = """
    CREATE TABLE IF NOT EXISTS products (
        product_id UUID PRIMARY KEY,
        name VARCHAR(255),
        category VARCHAR(100),
        price DECIMAL(10,2),
        attributes JSONB,
        history JSONB
    );
    """
    try:
        with conn.cursor() as cur:
            cur.execute(drop_table_query)
            cur.execute(create_table_query)
            conn.commit()
            print("Table recreated successfully!")
    except Exception as e:
        print(f"Error creating table: {e}")

def load_json_data(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None

def insert_data(conn, data):
    insert_query = """
    INSERT INTO products (product_id, name, category, price, attributes, history)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        with conn.cursor() as cur:
            for item in data:
                cur.execute(insert_query, (
                    item['id'],
                    item['name'],
                    item['category'],
                    item['price'],
                    Json(item['attributes']),
                    Json(item['history'])
                ))
            conn.commit()
            print("Data inserted successfully!")
    except Exception as e:
        print(f"Error inserting data: {e}")

def main():
    # Replace with your JSON file path
    json_file_path = './generated_products.json'
    
    # Connect to database
    conn = connect_to_db()
    if not conn:
        return
    
    # Create table
    create_table(conn)
    
    # Load JSON data
    data = load_json_data(json_file_path)
    if not data:
        conn.close()
        return
    
    # Insert data
    insert_data(conn, data)
    
    # Close connection
    conn.close()
    print("Database connection closed.")

if __name__ == "__main__":
    main()