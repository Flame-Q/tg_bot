import mysql.connector
from config import DB_CONFIG
import hashlib
from datetime import datetime, timedelta

import io
from openpyxl import Workbook

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def hash_secret_word(word):
    """Хэширование секретного слова (можно использовать тот же алгоритм)"""
    return hashlib.sha256(word.encode()).hexdigest()

# ---------- ПОЛЬЗОВАТЕЛИ И АУТЕНТИФИКАЦИЯ ----------
def register_user(login, password, name, surname, email, secret_word):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hash_password(password)
    secret_hash = hash_secret_word(secret_word)
    try:
        cursor.execute("""
            INSERT INTO users (login, password_hash, secret_word_hash, name, surname, email, subscriptions_id_sub, balance, role)
            VALUES (%s, %s, %s, %s, %s, %s, 1, 0.00, 'user')
        """, (login, password_hash, secret_hash, name, surname, email))
        conn.commit()
        return True, "Регистрация успешна!"
    except mysql.connector.IntegrityError as e:
        if "Duplicate entry" in str(e):
            return False, "Логин или email уже заняты."
        return False, "Ошибка регистрации."
    finally:
        cursor.close()
        conn.close()

def login_user(login, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE login = %s", (login,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and user['password_hash'] == hash_password(password):
        if user.get('is_banned', False):
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT ban_until FROM bans WHERE user_id = %s AND ban_until > NOW()", (user['id_us'],))
            ban = cursor.fetchone()
            cursor.close()
            conn.close()
            if ban:
                return None, f"Ваш аккаунт забанен до {ban['ban_until']}"
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET is_banned = FALSE WHERE id_us = %s", (user['id_us'],))
                conn.commit()
                cursor.close()
                conn.close()
        return user, None
    return None, "Неверный логин или пароль"

def get_user_by_login(login):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE login = %s", (login,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def get_user_by_email(email):
    """ДОБАВЛЕНО ДЛЯ ВОССТАНОВЛЕНИЯ"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def verify_secret_word(email, word):
    """ДОБАВЛЕНО ДЛЯ ВОССТАНОВЛЕНИЯ"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT secret_word_hash FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and user['secret_word_hash'] == hash_secret_word(word):
        return True
    return False

def update_password_by_email(email, new_password):
    """ДОБАВЛЕНО ДЛЯ ВОССТАНОВЛЕНИЯ"""
    conn = get_db_connection()
    cursor = conn.cursor()
    new_hash = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (new_hash, email))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def get_user_by_telegram_id(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.*, s.name_sub, s.price, s.video_quality
        FROM users u
        LEFT JOIN subscriptions s ON u.subscriptions_id_sub = s.id_sub
        WHERE u.telegram_id = %s
    """, (telegram_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def update_telegram_id(user_id, telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Сначала обнуляем telegram_id у всех других пользователей, у которых он совпадает с новым
    cursor.execute("UPDATE users SET telegram_id = NULL WHERE telegram_id = %s AND id_us != %s", (telegram_id, user_id))
    # Затем обновляем текущего пользователя
    cursor.execute("UPDATE users SET telegram_id = %s WHERE id_us = %s", (telegram_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def logout_user(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET telegram_id = NULL WHERE telegram_id = %s", (telegram_id,))
    conn.commit()
    cursor.close()
    conn.close()

# ---------- ПОДПИСКИ И БАЛАНС ----------
def get_all_subscriptions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_sub, name_sub, price, video_quality FROM subscriptions ORDER BY price")
    subs = cursor.fetchall()
    cursor.close()
    conn.close()
    return subs

def update_balance(telegram_id, delta):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + %s WHERE telegram_id = %s", (delta, telegram_id))
    conn.commit()
    cursor.close()
    conn.close()

def buy_subscription(telegram_id, subscription_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT price FROM subscriptions WHERE id_sub = %s", (subscription_id,))
    sub = cursor.fetchone()
    if not sub:
        return False, "Подписка не найдена"
    cursor.execute("SELECT balance FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    if user['balance'] < sub['price']:
        return False, "Недостаточно средств"
    cursor.execute("UPDATE users SET balance = balance - %s, subscriptions_id_sub = %s WHERE telegram_id = %s",
                   (sub['price'], subscription_id, telegram_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True, f"Подписка успешно приобретена! Списано {sub['price']} руб."

def is_user_banned(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT is_banned FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and user.get('is_banned'):
        return True
    return False

# ---------- АДМИНКА: ФИЛЬМЫ ----------
def get_movie_types():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_type, name FROM movie_types")
    types = cursor.fetchall()
    cursor.close()
    conn.close()
    return types

def get_all_genres_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_gen, name_gen FROM genres")
    genres = cursor.fetchall()
    cursor.close()
    conn.close()
    return genres

def get_all_directors_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_dir, CONCAT(name, ' ', surname) AS full_name FROM directors")
    directors = cursor.fetchall()
    cursor.close()
    conn.close()
    return directors

def add_movie(telegram_id, title, release_year, description, country, type_id, genre_ids, director_ids):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    if not user or user['role'] != 'admin':
        return False, "Недостаточно прав"
    try:
        cursor.execute("""
            INSERT INTO movies (title, release_year, description, country, movie_types_id_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, release_year, description, country, type_id))
        movie_id = cursor.lastrowid
        for genre_id in genre_ids:
            cursor.execute("INSERT INTO movies_has_genres (movies_id_mov, genres_id_gen) VALUES (%s, %s)", (movie_id, genre_id))
        for director_id in director_ids:
            cursor.execute("INSERT INTO movies_has_directors (movies_id_mov, directors_id_dir) VALUES (%s, %s)", (movie_id, director_id))
        conn.commit()
        return True, f"Фильм '{title}' добавлен"
    except Exception as e:
        conn.rollback()
        return False, f"Ошибка: {e}"
    finally:
        cursor.close()
        conn.close()

def delete_movie_by_title(telegram_id, title):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    if not user or user['role'] != 'admin':
        return False, "Недостаточно прав"
    cursor.execute("SELECT id_mov FROM movies WHERE title = %s", (title,))
    movie = cursor.fetchone()
    if not movie:
        return False, "Фильм не найден"
    try:
        cursor.execute("DELETE FROM movies WHERE id_mov = %s", (movie['id_mov'],))
        conn.commit()
        return True, f"Фильм '{title}' удалён"
    except Exception as e:
        conn.rollback()
        return False, f"Ошибка: {e}"
    finally:
        cursor.close()
        conn.close()

def get_banned_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.login, u.name, u.surname, b.ban_until
        FROM users u
        JOIN bans b ON u.id_us = b.user_id
        WHERE b.ban_until > NOW()
    """)
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

def ban_user(telegram_id, user_login, minutes):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (telegram_id,))
    admin = cursor.fetchone()
    if not admin or admin['role'] != 'admin':
        return False, "Недостаточно прав"
    cursor.execute("SELECT id_us, role FROM users WHERE login = %s", (user_login,))
    user = cursor.fetchone()
    if not user:
        return False, "Пользователь не найден"
    if user['role'] == 'admin':
        return False, "Нельзя забанить администратора"
    ban_until = datetime.now() + timedelta(minutes=minutes)
    cursor.execute("INSERT INTO bans (user_id, ban_until, reason) VALUES (%s, %s, %s)", (user['id_us'], ban_until, f"Бан на {minutes} минут"))
    cursor.execute("UPDATE users SET is_banned = TRUE WHERE id_us = %s", (user['id_us'],))
    conn.commit()
    cursor.close()
    conn.close()
    return True, f"Пользователь {user_login} забанен на {minutes} минут"

def unban_user(telegram_id, user_login):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (telegram_id,))
    admin = cursor.fetchone()
    if not admin or admin['role'] != 'admin':
        return False, "Недостаточно прав"
    cursor.execute("SELECT id_us, is_banned FROM users WHERE login = %s", (user_login,))
    user = cursor.fetchone()
    if not user:
        return False, "Пользователь не найден"
    if not user['is_banned']:
        return False, "Пользователь не находится в бане"
    cursor.execute("DELETE FROM bans WHERE user_id = %s", (user['id_us'],))
    cursor.execute("UPDATE users SET is_banned = FALSE WHERE id_us = %s", (user['id_us'],))
    conn.commit()
    cursor.close()
    conn.close()
    return True, f"Пользователь {user_login} разбанен"

# ---------- ПОИСК ФИЛЬМОВ ----------
def get_movies_by_title(title_part):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_mov, title, release_year, description, country FROM movies WHERE title LIKE %s", (f"%{title_part}%",))
    movies = cursor.fetchall()
    cursor.close()
    conn.close()
    return movies

def get_movies_by_genre(genre_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.id_mov, m.title, m.release_year, m.description, m.country
        FROM movies m
        JOIN movies_has_genres mhg ON m.id_mov = mhg.movies_id_mov
        JOIN genres g ON mhg.genres_id_gen = g.id_gen
        WHERE g.name_gen = %s
    """, (genre_name,))
    movies = cursor.fetchall()
    cursor.close()
    conn.close()
    return movies

def get_movies_by_director(director_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.id_mov, m.title, m.release_year, m.description, m.country
        FROM movies m
        JOIN movies_has_directors mhd ON m.id_mov = mhd.movies_id_mov
        JOIN directors d ON mhd.directors_id_dir = d.id_dir
        WHERE CONCAT(d.name, ' ', d.surname) LIKE %s
    """, (f"%{director_name}%",))
    movies = cursor.fetchall()
    cursor.close()
    conn.close()
    return movies

def get_all_genres():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name_gen FROM genres ORDER BY name_gen")
    genres = cursor.fetchall()
    cursor.close()
    conn.close()
    return [g['name_gen'] for g in genres]

def get_all_directors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT CONCAT(name, ' ', surname) AS full_name FROM directors ORDER BY full_name")
    directors = cursor.fetchall()
    cursor.close()
    conn.close()
    return [d['full_name'] for d in directors]

def get_movie_details(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT g.name_gen FROM genres g
        JOIN movies_has_genres mhg ON g.id_gen = mhg.genres_id_gen
        WHERE mhg.movies_id_mov = %s
    """, (movie_id,))
    genres = [row['name_gen'] for row in cursor.fetchall()]
    cursor.execute("""
        SELECT CONCAT(d.name, ' ', d.surname) AS director FROM directors d
        JOIN movies_has_directors mhd ON d.id_dir = mhd.directors_id_dir
        WHERE mhd.movies_id_mov = %s
    """, (movie_id,))
    directors = [row['director'] for row in cursor.fetchall()]
    cursor.execute("SELECT title, release_year, description, country FROM movies WHERE id_mov = %s", (movie_id,))
    movie = cursor.fetchone()
    cursor.close()
    conn.close()
    if movie:
        movie['genres'] = genres
        movie['directors'] = directors
    return movie

# ---------- ОТЗЫВЫ ----------
def get_last_reviews(movie_id, limit=3):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.rating, r.title, r.comment, r.created_at, u.name, u.surname
        FROM reviews r
        JOIN users u ON r.users_id_us = u.id_us
        WHERE r.movies_id_mov = %s
        ORDER BY r.created_at DESC
        LIMIT %s
    """, (movie_id, limit))
    reviews = cursor.fetchall()
    cursor.close()
    conn.close()
    return reviews

def add_review(movie_id, user_telegram_id, rating, title, comment):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_us FROM users WHERE telegram_id = %s", (user_telegram_id,))
    user = cursor.fetchone()
    if not user:
        return False
    cursor.execute("""
        INSERT INTO reviews (users_id_us, movies_id_mov, rating, title, comment)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE rating=VALUES(rating), title=VALUES(title), comment=VALUES(comment)
    """, (user['id_us'], movie_id, rating, title, comment))
    conn.commit()
    cursor.close()
    conn.close()
    return True

# ---------- ИЗБРАННОЕ ----------
def add_favorite(telegram_id, movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_us FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        return False
    try:
        cursor.execute("INSERT INTO favorites (user_id, movie_id) VALUES (%s, %s)", (user[0], movie_id))
        conn.commit()
        result = True
    except mysql.connector.IntegrityError:
        result = False
    cursor.close()
    conn.close()
    return result

def remove_favorite(telegram_id, movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_us FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        return False
    cursor.execute("DELETE FROM favorites WHERE user_id = %s AND movie_id = %s", (user[0], movie_id))
    conn.commit()
    deleted = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return deleted

def get_favorites(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.id_mov, m.title, m.release_year
        FROM favorites f
        JOIN movies m ON f.movie_id = m.id_mov
        JOIN users u ON f.user_id = u.id_us
        WHERE u.telegram_id = %s
    """, (telegram_id,))
    favs = cursor.fetchall()
    cursor.close()
    conn.close()
    return favs

# ---------- РЕКОМЕНДАЦИИ ----------
def get_random_high_rated_movie():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.id_mov, m.title, m.release_year, AVG(r.rating) as avg_rating
        FROM movies m
        JOIN reviews r ON m.id_mov = r.movies_id_mov
        GROUP BY m.id_mov
        HAVING AVG(r.rating) > 8.0
        ORDER BY RAND()
        LIMIT 1
    """)
    movie = cursor.fetchone()
    cursor.close()
    conn.close()
    return movie

# ---------- ПАГИНАЦИЯ ВСЕХ ФИЛЬМОВ ----------
def get_all_movies_paginated(page=1, per_page=10):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM movies")
    total = cursor.fetchone()['total']
    offset = (page - 1) * per_page
    cursor.execute("""
        SELECT id_mov, title, release_year
        FROM movies
        ORDER BY title
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    movies = cursor.fetchall()
    cursor.close()
    conn.close()
    return movies, total

# ---------- ДОБАВЛЕНИЕ НОВЫХ РЕЖИССЁРОВ И ТИПОВ ----------
def add_director(telegram_id, name, surname):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    if not user or user['role'] != 'admin':
        return False, "Недостаточно прав"
    try:
        cursor.execute("INSERT INTO directors (name, surname) VALUES (%s, %s)", (name, surname))
        conn.commit()
        new_id = cursor.lastrowid
        return True, f"Режиссёр {name} {surname} добавлен (ID {new_id})"
    except Exception as e:
        conn.rollback()
        return False, f"Ошибка: {e}"
    finally:
        cursor.close()
        conn.close()

def add_movie_type(telegram_id, name, description):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    if not user or user['role'] != 'admin':
        return False, "Недостаточно прав"
    try:
        cursor.execute("INSERT INTO movie_types (name, description) VALUES (%s, %s)", (name, description))
        conn.commit()
        new_id = cursor.lastrowid
        return True, f"Тип фильма '{name}' добавлен (ID {new_id})"
    except Exception as e:
        conn.rollback()
        return False, f"Ошибка: {e}"
    finally:
        cursor.close()
        conn.close()

def export_movies_and_directors_to_excel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id_mov, title, release_year, description, country FROM movies ORDER BY id_mov")
    movies = cursor.fetchall()
    
    cursor.execute("SELECT id_dir, name, surname FROM directors ORDER BY id_dir")
    directors = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    wb = Workbook()
    
    ws_movies = wb.active
    ws_movies.title = "Фильмы"
    ws_movies.append(["ID", "Название", "Год выпуска", "Описание", "Страна"])
    for m in movies:
        ws_movies.append([m['id_mov'], m['title'], m['release_year'], m['description'], m['country']])
    
    ws_directors = wb.create_sheet("Режиссёры")
    ws_directors.append(["ID", "Имя", "Фамилия"])
    for d in directors:
        ws_directors.append([d['id_dir'], d['name'], d['surname']])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output