
#базовые операции на питоне 
import psycopg2
from psycopg2 import sql
from psycopg2 import errors

def connect_to_db():
    try:
        print("Попытка подключения к БД")
        conn = psycopg2.connect(
            host="localhost",
            database="mydb",
            user="postgres",
            password="postgres",
            port="5432"
        )
        print("Подключение прошло успешно")
        return conn
    except Exception as e:
        print("Ошибка:", e)
        return None

def select_first_user():
    with connect_to_db().cursor() as cursor:
        stmt = "SELECT * FROM test_table"
        cursor.execute(stmt)
        print(cursor.fetchall()[0][0])

def insert_user(name):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "INSERT INTO test_table (name) VALUES (%s)"
            cursor.execute(stmt, (name,))
            conn.commit()
            print("У нас появился новый пользователь")

def update_user(old_name, new_name):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "UPDATE test_table SET name = %s WHERE name = %s"
            cursor.execute(stmt, (new_name, old_name, old_name))
            conn.commit() 
            print("Операция прошла успешно")

def delete_user(name):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "DELETE FROM test_table WHERE name = %s"
            cursor.execute(stmt, (name,))
            conn.commit()
            print("Операция завершена")

delete_user('VASILISA1')
