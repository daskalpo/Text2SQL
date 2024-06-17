import streamlit as st
import openai
import pandas as pd

pd.set_option('display.max_columns', None)
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import sqlite3
import ast
from pathlib import Path


load_dotenv()
API_TYPE = os.getenv("OPENAI_API_TYPE")
API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE")
API_VERSION = os.getenv("OPENAI_API_VERSION")
GPT35_TURBO_MODEL_NAME = os.getenv("GPT35_TURBO_MODEL_NAME")


def azureclient():
    client = AzureOpenAI(
        api_key=API_KEY,
        azure_endpoint=API_BASE,
    )
    return client


# Function to generate response from OpenAI's GPT-3 model
def generate_response(client, messages):
    openai.api_type = API_TYPE
    openai.api_base = API_BASE
    openai.api_version = API_VERSION
    openai.api_key = API_KEY
    
    # st.write(messages)
    response = client.chat.completions.create(
        model=GPT35_TURBO_MODEL_NAME,
        messages=messages,
        temperature=0.5,
        top_p=0.95,
        max_tokens=1000
        # seed=123,
        # frequency_penalty=0,
        # presence_penalty=0,
        # stop=None
    )
    generated_report = response.choices[0].message.content
    # messages.append({"role": "Assistant", "content": generated_report})
    return generated_report


def process_data(csv_file, run_first):
    dataset_name = Path(csv_file.name).stem
    df = pd.read_csv(csv_file)
    st.write(df)

    if run_first:
        create_Table(df, dataset_name)
    else:
        df = getTableData(dataset_name)

    return df, dataset_name


def create_Table(df, table_name, db_name='dq_demo_database'):
    conn = sqlite3.connect(db_name)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()


def execute_sql_statement(sql_statement, db_name='dq_demo_database'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute(sql_statement)
        conn.commit()
        print("SQL statement executed successfully.")
    except sqlite3.Error as e:
        print(f"Error executing SQL statement: {e}")
    conn.close()


# Function for the DQ function prompt
@st.cache_resource(show_spinner=False)
def dq_function(_client, df, dataset_name, user_input):
    query_template = {
        "user_input_type": "",
        "query_response": ""
    }
    system_message = f'''
    ROLE: You are an expert data analyst and data quality specialist. Follow the instructions strictly.
    You will provide accurate and precise responses.
    ***********************

    $USER_INPUT: {user_input}
    $DATA: {df}
    $DATASET_NAME: {dataset_name}
    CRITICAL INSTRUCTIONS:
    1. Analyse the $USER_INPUT and identify if it is an "analysis" or an "operation".
    2. Analyze the data enclosed in ###DATA###.
    3. If $USER_INPUT is of type "analysis" then:
    3.1. Analyze the $USER_INPUT and produce output in following JSON structure strictly:

    {query_template}

    4. else if $USER_INPUT is of type "operation" then:
    4.1. Understand and execute the instruction on the data
    4.2. Generate optimized SQL statement for the described $USER_INPUT for the $DATASET_NAME
    4.3. Make sure that you do not remove any column or data which is not mentioned in $USER_INPUT
    4.4. Suppress all thought process and steps and output solely the final JSON data:
    '''
    system_message += '''{
    "user_input_type":"",
    "sql_queries":["",]
    }

    *********************
    OUTPUT:
    Suppress all thought process and steps in the output
    Strictly return only JSON output in the given JSON format
    '''
    response = generate_response(_client, system_message)

    # prompt_response = prompt_template(_client, df, dataset_name, user_input)

    # data.append(ast.literal_eval(prompt_response))
    st.write(response)
    return response


def prompt_template(_client, df, dataset_name, user_input):
    system_message = f'''
    ROLE: You are an expert data analyst and data quality specialist. Follow the instructions strictly.
    You will provide accurate and precise responses.
    ***********************

    $USER_INPUT: {user_input}
    $DATA: {df}
    $DATASET_NAME: {dataset_name}

    CRITICAL INSTRUCTIONS:
    1. Analyse the $USER_INPUT.
    2. Analyze the data enclosed in $DATA.
    3.1. Understand and execute the instruction on the data
    3.2. Generate updated data in python list format for the described $USER_INPUT for the $DATASET_NAME
    3.3. Make sure that you do not remove any column or data which is not mentioned in $USER_INPUT
    3.4. Suppress all thought process and steps and output solely the final JSON data:
    '''
    system_message += '''{
    "python_list_format":["",]
    }

    *********************
    OUTPUT:
    Suppress all thought process and steps in the output
    Strictly return only JSON output in the given JSON format
    '''
    response = generate_response(_client, system_message)
    # st.write(response)
    return response


def getTableData(table_name, db_name='dq_demo_database'):
    conn = sqlite3.connect(db_name)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        return df
    except sqlite3.Error as e:
        print(f"Error selecting rows from the table: {e}")
        return None
    finally:
        conn.close()


def generate_prompt(_client, question, messages):
    data = '''###
		DATABASE NAME=INV_DATABASE, Description: Database of all invoices related tables
		TABLE NAME=INV_DATABASE.INVOICES_TABLE, Description: Table containing invoices related data
		COLUMN NAME=INVOICES_TABLE.VENDOR, Description: Name of the Vendor, Additional Info: This is primary key
		COLUMN NAME=INVOICES_TABLE.AGING_BRACKET, Description: This bucket captures the aging of invoices in number of days
		COLUMN NAME=INVOICES_TABLE.AMOUNT, Description: This field indicates the total amount of invoice in USD
		COLUMN NAME=INVOICES_TABLE.ACCOUNT_NUMBER, Description: Account number of the vendor
		COLUMN NAME=INVOICES_TABLE.HEADER_NUMBER, Description: Header number of the vendor invoice accounting
		COLUMN NAME=INVOICES_TABLE.PAYMENT_STATUS, Description: Current status of the payment
		COLUMN NAME=INVOICES_TABLE.CLEAR_DTS, Description: Date and time when the invoice was cleared
		COLUMN NAME=INVOICES_TABLE.DUE_DTS_BY, Description: Due date and time for the invoice and due expenses
		COLUMN NAME=INVOICES_TABLE.DUE_PERIOD, Description: Period within which the invoice is due
		COLUMN NAME=INVOICES_TABLE.DUE_STATUS, Description: Status indicating if the invoice is due or overdue
		COLUMN NAME=INVOICES_TABLE.AGING, Description: The aging of the invoice
		### '''

    prompt = f'''
    $DATA = {data}
    CRITICAL INSTRUCTIONS:
    1. Analyse the {question}.
    2. Analyze the data enclosed in $DATA.
    3. Understand and write SQL code to fetch appropriate data.
    4. Exclude any explanations.
    '''
    messages.append({"role": "function", "content": prompt, "name": "user_prompt"})
    response = generate_response(_client, messages)

    return response, prompt