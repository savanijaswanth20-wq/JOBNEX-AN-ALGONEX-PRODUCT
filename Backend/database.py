import os
import mysql.connector 

def get_connection():
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "root")
    database = os.getenv("DB_NAME", "jobnex")
    
    password_env = os.getenv("DB_PASSWORD")
    candidate_passwords = [password_env] if password_env else ["Algonex@123", "Algonex@2003"]
    
    last_err = None
    for pwd in candidate_passwords:
        try:
            return mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=pwd,
                database=database
            )
        except mysql.connector.Error as err:
            last_err = err
            if err.errno != 1045:
                raise
    if last_err:
        raise last_err