#database.py
import mysql.connector 

def get_connection():
    return mysql.connector.connect (
        host = "127.0.0.1",
        port='3306',
        user='root',
        password ='Algonex@123',
        database ='jobnex'
    )
