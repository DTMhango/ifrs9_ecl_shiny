import numpy as np
import pandas as pd
import sqlite3
import io
import base64


def parse_content(contents, filename):
    print("Received contents:", contents)
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    if '.csv' in filename:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        return df.to_dict('records')
    elif '.xls' in filename:
        df = pd.read_excel(io.BytesIO(decoded))
        return df.to_dict('records')


def decode_image(image_file):
    encoded = base64.b64encode(open(image_file, 'rb').read())
    return f"data:image/png;base64,{encoded.decode()}"


def connect_pd_database():
    db_path = 'C:\sqlite\Databases\ifrs9test.db'
    pd_table = 'ifrs9_PD_data'
    recoveries_table = 'ifrs9_recoveries_data'
    # loan_table = 'ifrs9_loanbook'

    connection = sqlite3.connect(db_path)
    query1 = f'SELECT * FROM {pd_table}'
    query2 = f'SELECT * FROM {recoveries_table}'
    # query3 = f'SELECT * FROM {loan_table}'


    pd_data = pd.read_sql_query(query1, connection)
    rec_data = pd.read_sql_query(query2, connection)
    # loan_book =pd.read_sql_query(query3, connection)

    connection.close()

    return pd_data, rec_data#, loan_book

def connect_loanbook_database():
    db_path = 'C:\sqlite\Databases\ifrs9loanbook.db'

    loan_book_table = 'ifrs9_loanbook'
    connection = sqlite3.connect(db_path)
    query1 = f'SELECT * FROM {loan_book_table}'

    loan_book = pd.read_sql_query(query1, connection)

    connection.close()

    return loan_book


def connect_fli():
    db_path = 'C:\sqlite\Databases\ifrs9fli.db'

    fli_table = 'fli'
    connection = sqlite3.connect(db_path)
    query1 = f'SELECT * FROM {fli_table}'

    fli = pd.read_sql_query(query1, connection)

    connection.close()

    return fli