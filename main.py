
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
            port="8080"
        )
        print("Подключение прошло успешно")
        return conn
    except Exception as e:
        print("Ошибка:", e)
        return None

#1
def insert_user(username, email):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "INSERT INTO users (username, email) VALUES (%s, %s)"
            cursor.execute(stmt, (username, email))
            conn.commit()
            print("У нас появился новый пользователь")

insert_user('Anna', 'anna@gmail.com')
insert_user('Ivan', 'vanya@mail.com')

#2
def select_all_users():
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "SELECT * FROM users"
            cursor.execute(stmt)
            result = cursor.fetchall()
            print("Все пользователи:")
            for i in result:
                print(i)
            return result

select_all_users()

#3
def select_user(user_id):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "SELECT * FROM users WHERE user_id = %s"
            cursor.execute(stmt, (user_id,))
            result = cursor.fetchone()
            print(Пользователь найден)
            return result

select_user(1)

# 4
def update_email(user_id, new_email):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "UPDATE users SET email = %s WHERE user_id = %s"
            cursor.execute(stmt, (new_email, user_id))
            conn.commit()
            print("Email пользователя обновлен")

update_email(2, 'ivan@gmail.com')

# 5
def delete_user(user_id):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "DELETE FROM users WHERE user_id = %s"
            cursor.execute(stmt, (user_id,))
            conn.commit()
            print("Пользователь удален")

delete_user(2)

# 6
def insert_category(category_name, category_slug):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "INSERT INTO categories (category_name, category_slug) VALUES (%s, %s)"
            cursor.execute(stmt, (category_name, category_slug))
            conn.commit()
            print("Появилась новая категория")

insert_category('license', 'A')
insert_category('license', 'B')

# 7
def select_all_categories():
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "SELECT * FROM categories"
            cursor.execute(stmt)
            result = cursor.fetchall()
            print("Все категории:")
            for i in result:
                print(i)
            return result

select_all_categories()

# 8
def select_category(category_id):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "SELECT * FROM categories WHERE category_id = %s"
            cursor.execute(stmt, (category_id,))
            result = cursor.fetchone()
            print("Категория с ID, result)
            return result

select_category(1)

# 9
def update_category_name(category_id, new_name):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "UPDATE categories SET category_name = %s WHERE category_id = %s"
            cursor.execute(stmt, (new_name, category_id))
            conn.commit()
            print("Название категории обновлено")

update_category_name(1, 'rigrt')

# 10
def delete_category(category_id):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "DELETE FROM categories WHERE category_id = %s"
            cursor.execute(stmt, (category_id,))
            conn.commit()
            print("Категория удалена")

delete_category(1)

# 11
def insert_article(title, content, category_id, author_id):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "INSERT INTO articles (title, content, category_id, author_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(stmt, (title, content, category_id, author_id))
            conn.commit()
            print("Новая статья добавлена")

insert_article('Interesting facts', 'The largest representatives of Household breeds are Maine Coons.', 2, 1)

# 12
def select_all_articles():
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "SELECT * FROM articles"
            cursor.execute(stmt)
            result = cursor.fetchall()
            print("Все статьи:")
            for i in result:
                print(i)
            return result

select_all_articles()

# 13
def select_article(article_id):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "SELECT * FROM articles WHERE article_id = %s"
            cursor.execute(stmt, (article_id,))
            result = cursor.fetchone()
            print("Статья", result)
            return result

select_article(1)

# 14
def update_content(article_id, new_content):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "UPDATE articles SET content = %s WHERE article_id = %s"
            cursor.execute(stmt, (new_content, article_id))
            conn.commit()
            print("Содержание статьи обновлено")

update_content(1, 'Each cat`s nose print is as unique as a human`s fingerprints.')

# 15
def delete_article(article_id):
    with connect_to_db() as conn:
        with conn.cursor() as cursor:
            stmt = "DELETE FROM articles WHERE article_id = %s"
            cursor.execute(stmt, (article_id,))
            conn.commit()
            print("Статья удалена")

delete_article(1)