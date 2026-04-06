import logging
from aiogram import types, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database as db
import keyboards as kb
from urllib.parse import quote

# ---------- СОСТОЯНИЯ ----------
class AuthStates(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()
    waiting_for_register_login = State()
    waiting_for_register_password = State()
    waiting_for_register_name = State()
    waiting_for_register_surname = State()
    waiting_for_register_email = State()

class SearchStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_genre = State()
    waiting_for_director = State()

class ReviewStates(StatesGroup):
    waiting_for_rating = State()
    waiting_for_title = State()
    waiting_for_comment = State()

class RechargeStates(StatesGroup):
    waiting_for_custom_amount = State()

class AdminStates(StatesGroup):
    waiting_for_add_title = State()
    waiting_for_add_year = State()
    waiting_for_add_description = State()
    waiting_for_add_country = State()
    waiting_for_add_type = State()
    waiting_for_add_genres = State()
    waiting_for_add_directors = State()
    waiting_for_delete_title = State()
    waiting_for_ban_login = State()
    waiting_for_ban_minutes = State()
    waiting_for_unban_login = State()

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def get_kinopoisk_url(title):
    return f"https://www.kinopoisk.ru/index.php?kp_query={quote(title)}"

async def show_main_menu(message: types.Message, is_admin=False):
    if is_admin:
        await message.answer("🏠 *Главное меню*", parse_mode="HTML", reply_markup=kb.admin_main_menu())
    else:
        await message.answer("🏠 *Главное меню*", parse_mode="HTML", reply_markup=kb.main_menu())

# ---------- АВТОРИЗАЦИЯ ----------
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Добро пожаловать! Используйте /login для входа или /register для регистрации.")

async def cmd_login(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш логин:")
    await state.set_state(AuthStates.waiting_for_login)

async def process_login(message: types.Message, state: FSMContext):
    login = message.text.strip()
    await state.update_data(login=login)
    await message.answer("Введите пароль:")
    await state.set_state(AuthStates.waiting_for_password)

async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    login = data['login']
    user, error = db.login_user(login, password)
    if user:
        db.update_telegram_id(user['id_us'], message.from_user.id)
        if user['role'] == 'admin':
            await message.answer("Вход выполнен как администратор!")
            await show_main_menu(message, is_admin=True)
        else:
            await message.answer(f"Вход выполнен! Добро пожаловать, {user['name']}.")
            await show_main_menu(message, is_admin=False)
        await state.clear()
    else:
        await message.answer(f"Ошибка: {error}")
        await state.clear()

async def cmd_register(message: types.Message, state: FSMContext):
    await message.answer("Введите желаемый логин:")
    await state.set_state(AuthStates.waiting_for_register_login)

async def process_register_login(message: types.Message, state: FSMContext):
    await state.update_data(reg_login=message.text.strip())
    await message.answer("Введите пароль:")
    await state.set_state(AuthStates.waiting_for_register_password)

async def process_register_password(message: types.Message, state: FSMContext):
    await state.update_data(reg_password=message.text.strip())
    await message.answer("Введите ваше имя:")
    await state.set_state(AuthStates.waiting_for_register_name)

async def process_register_name(message: types.Message, state: FSMContext):
    await state.update_data(reg_name=message.text.strip())
    await message.answer("Введите вашу фамилию:")
    await state.set_state(AuthStates.waiting_for_register_surname)

async def process_register_surname(message: types.Message, state: FSMContext):
    await state.update_data(reg_surname=message.text.strip())
    await message.answer("Введите ваш email:")
    await state.set_state(AuthStates.waiting_for_register_email)

async def process_register_email(message: types.Message, state: FSMContext):
    email = message.text.strip()
    if "@" not in email:
        await message.answer("Email должен содержать '@'. Попробуйте снова.")
        return
    data = await state.get_data()
    login = data['reg_login']
    password = data['reg_password']
    name = data['reg_name']
    surname = data['reg_surname']
    success, msg = db.register_user(login, password, name, surname, email)
    await message.answer(msg)
    if success:
        await message.answer("Теперь вы можете войти с помощью /login")
    await state.clear()

# ---------- ЛИЧНЫЙ КАБИНЕТ ----------
async def profile_callback(callback: types.CallbackQuery):
    user = db.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text("Ошибка: пользователь не найден.")
        return
    text = (f"👤 *Ваш профиль*\n\n"
            f"Имя: {user['name']} {user['surname']}\n"
            f"Email: {user['email']}\n"
            f"Подписка: {user['name_sub']} ({user['video_quality']})\n"
            f"Цена: {user['price']} руб/мес\n"
            f"Баланс: {user['balance']} руб\n"
            f"Дата регистрации: {user['reg_date']}")
    buttons = [
        [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="recharge")],
        [InlineKeyboardButton(text="🎫 Купить подписку", callback_data="buy_sub")],
        [InlineKeyboardButton(text="🚪 Выйти из аккаунта", callback_data="logout")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

async def logout_callback(callback: types.CallbackQuery):
    db.logout_user(callback.from_user.id)
    await callback.message.edit_text("👋 Вы вышли из аккаунта. Для входа или регистрации нажмите /start")
    await callback.answer()

# ---------- ПОПОЛНЕНИЕ БАЛАНСА ----------
async def recharge_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "recharge":
        await callback.message.edit_text("💰 Выберите сумму пополнения:", reply_markup=kb.recharge_keyboard())
        await callback.answer()
    elif callback.data.startswith("recharge_"):
        amount_str = callback.data.split("_")[1]
        if amount_str == "custom":
            await callback.message.edit_text("✏️ Введите сумму (только число):")
            await state.set_state(RechargeStates.waiting_for_custom_amount)
            await callback.answer()
        else:
            amount = int(amount_str)
            db.update_balance(callback.from_user.id, amount)
            await callback.message.edit_text(f"✅ Баланс пополнен на {amount} руб.", reply_markup=kb.back_button())
            await callback.answer()

async def process_custom_recharge(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
        db.update_balance(message.from_user.id, amount)
        await message.answer(f"✅ Баланс пополнен на {amount} руб.", reply_markup=kb.back_button())
    except ValueError:
        await message.answer("❌ Введите положительное число.")
    await state.clear()

# ---------- ПОКУПКА ПОДПИСКИ ----------
async def buy_subscription_callback(callback: types.CallbackQuery):
    if callback.data == "buy_sub":
        subs = db.get_all_subscriptions()
        if not subs:
            await callback.message.edit_text("Подписки временно недоступны.")
            return
        await callback.message.edit_text("🎫 Выберите подписку:", reply_markup=kb.subscriptions_keyboard(subs))
        await callback.answer()
    elif callback.data.startswith("buy_sub_"):
        sub_id = int(callback.data.split("_")[2])
        success, msg = db.buy_subscription(callback.from_user.id, sub_id)
        await callback.message.edit_text(msg, reply_markup=kb.back_button())
        await callback.answer()

# ---------- ПОИСК ФИЛЬМОВ ----------
async def search_title_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔍 Введите название фильма (или его часть):")
    await state.set_state(SearchStates.waiting_for_title)
    await callback.answer()

async def process_title_search(message: types.Message, state: FSMContext):
    title_part = message.text.strip()
    movies = db.get_movies_by_title(title_part)
    if not movies:
        await message.answer("😔 Фильмы не найдены.", reply_markup=kb.back_button())
    else:
        for movie in movies:
            await send_movie_card(message, movie['id_mov'], message.from_user.id)
    await state.clear()

async def search_genre_callback(callback: types.CallbackQuery):
    genres = db.get_all_genres()
    if not genres:
        await callback.message.edit_text("Жанры не найдены.")
        return
    await callback.message.edit_text("🎭 Выберите жанр:", reply_markup=kb.genre_list_keyboard(genres))
    await callback.answer()

async def genre_selected_callback(callback: types.CallbackQuery):
    genre = callback.data.split("_", 1)[1]
    movies = db.get_movies_by_genre(genre)
    if not movies:
        await callback.message.edit_text(f"😔 Фильмы в жанре '{genre}' не найдены.", reply_markup=kb.back_button())
    else:
        await callback.message.edit_text(f"🎬 Фильмы в жанре *{genre}*:", parse_mode="HTML")
        for movie in movies:
            await send_movie_card(callback.message, movie['id_mov'], callback.from_user.id)
    await callback.answer()

async def search_director_callback(callback: types.CallbackQuery):
    directors = db.get_all_directors()
    if not directors:
        await callback.message.edit_text("Режиссёры не найдены.")
        return
    await callback.message.edit_text("🎬 Выберите режиссёра:", reply_markup=kb.director_list_keyboard(directors))
    await callback.answer()

async def director_selected_callback(callback: types.CallbackQuery):
    director = callback.data.split("_", 1)[1]
    movies = db.get_movies_by_director(director)
    if not movies:
        await callback.message.edit_text(f"😔 Фильмы режиссёра '{director}' не найдены.", reply_markup=kb.back_button())
    else:
        await callback.message.edit_text(f"🎬 Фильмы *{director}*:", parse_mode="HTML")
        for movie in movies:
            await send_movie_card(callback.message, movie['id_mov'], callback.from_user.id)
    await callback.answer()

# ---------- КАРТОЧКА ФИЛЬМА ----------
async def send_movie_card(message: types.Message, movie_id: int, telegram_id: int):
    movie = db.get_movie_details(movie_id)
    if not movie:
        await message.answer("Информация о фильме не найдена.")
        return
    genres_str = ", ".join(movie['genres']) if movie['genres'] else "Не указан"
    directors_str = ", ".join(movie['directors']) if movie['directors'] else "Не указан"
    text = (f"🎬 *{movie['title']}* ({movie['release_year']})\n"
            f"🌍 Страна: {movie['country'] or 'Не указана'}\n"
            f"🎭 Жанры: {genres_str}\n"
            f"🎬 Режиссёр: {directors_str}\n\n"
            f"📖 {movie['description'][:300]}{'...' if len(movie['description'])>300 else ''}")
    favs = db.get_favorites(telegram_id)
    is_fav = any(f['id_mov'] == movie_id for f in favs)
    keyboard = kb.movie_actions(movie_id, is_fav)
    for row in keyboard.inline_keyboard:
        for btn in row:
            if btn.text == "🎥 Смотреть на Кинопоиске":
                btn.url = get_kinopoisk_url(movie['title'])
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

async def update_movie_card_message(message: types.Message, movie_id: int, is_fav: bool):
    movie = db.get_movie_details(movie_id)
    if not movie:
        return
    genres_str = ", ".join(movie['genres']) if movie['genres'] else "Не указан"
    directors_str = ", ".join(movie['directors']) if movie['directors'] else "Не указан"
    text = (f"🎬 *{movie['title']}* ({movie['release_year']})\n"
            f"🌍 Страна: {movie['country'] or 'Не указана'}\n"
            f"🎭 Жанры: {genres_str}\n"
            f"🎬 Режиссёр: {directors_str}\n\n"
            f"📖 {movie['description'][:300]}{'...' if len(movie['description'])>300 else ''}")
    keyboard = kb.movie_actions(movie_id, is_fav)
    for row in keyboard.inline_keyboard:
        for btn in row:
            if btn.text == "🎥 Смотреть на Кинопоиске":
                btn.url = get_kinopoisk_url(movie['title'])
    await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

# ---------- ВСЕ ФИЛЬМЫ (ПАГИНАЦИЯ) ----------
async def all_movies_callback(callback: types.CallbackQuery):
    page = 1
    movies, total = db.get_all_movies_paginated(page, per_page=10)
    if not movies:
        await callback.message.edit_text("😔 Фильмы не найдены.", reply_markup=kb.back_button())
        await callback.answer()
        return
    total_pages = (total + 9) // 10
    keyboard = kb.all_movies_paginated_keyboard(movies, page, total_pages)
    await callback.message.edit_text(
        f"📋 *Все фильмы (страница {page} из {total_pages})*:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

async def all_movies_page_callback(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    movies, total = db.get_all_movies_paginated(page, per_page=10)
    if not movies:
        await callback.message.edit_text("😔 Фильмы не найдены.", reply_markup=kb.back_button())
        await callback.answer()
        return
    total_pages = (total + 9) // 10
    keyboard = kb.all_movies_paginated_keyboard(movies, page, total_pages)
    await callback.message.edit_text(
        f"📋 *Все фильмы (страница {page} из {total_pages})*:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

# ---------- ОТЗЫВЫ ----------
async def show_reviews(callback: types.CallbackQuery, state: FSMContext):
    movie_id = int(callback.data.split("_")[1])
    await state.update_data(movie_id=movie_id)
    reviews = db.get_last_reviews(movie_id)
    if not reviews:
        text = "⭐️ Отзывов пока нет. Будьте первым!"
    else:
        text = "⭐️ *Последние отзывы:*\n\n"
        for rev in reviews:
            text += f"👤 {rev['name']} {rev['surname']} | Оценка: {rev['rating']}/10\n📌 {rev['title']}\n💬 {rev['comment']}\n🕒 {rev['created_at']}\n\n"
    buttons = [
        [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data=f"leave_review_{movie_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_search")]
    ]
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

async def leave_review_start(callback: types.CallbackQuery, state: FSMContext):
    movie_id = int(callback.data.split("_")[2])
    await state.update_data(movie_id=movie_id)
    await callback.message.edit_text("⭐️ Введите оценку от 1 до 10:")
    await state.set_state(ReviewStates.waiting_for_rating)
    await callback.answer()

async def process_review_rating(message: types.Message, state: FSMContext):
    try:
        rating = int(message.text.strip())
        if rating < 1 or rating > 10:
            raise ValueError
        await state.update_data(rating=rating)
        await message.answer("✏️ Введите заголовок отзыва:")
        await state.set_state(ReviewStates.waiting_for_title)
    except ValueError:
        await message.answer("❌ Оценка должна быть целым числом от 1 до 10. Попробуйте снова:")

async def process_review_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("💬 Введите текст отзыва:")
    await state.set_state(ReviewStates.waiting_for_comment)

async def process_review_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    movie_id = data['movie_id']
    rating = data['rating']
    title = data['title']
    comment = message.text.strip()
    success = db.add_review(movie_id, message.from_user.id, rating, title, comment)
    if success:
        await message.answer("✅ Спасибо за отзыв!", reply_markup=kb.back_button())
    else:
        await message.answer("❌ Не удалось оставить отзыв. Попробуйте позже.", reply_markup=kb.back_button())
    await state.clear()

# ---------- ИЗБРАННОЕ ----------
async def favorites_callback(callback: types.CallbackQuery):
    favs = db.get_favorites(callback.from_user.id)
    if not favs:
        await callback.message.edit_text("❤️ У вас пока нет избранных фильмов.", reply_markup=kb.back_button())
    else:
        await callback.message.edit_text("❤️ *Ваши избранные фильмы:*", parse_mode="HTML", reply_markup=kb.favorites_list_keyboard(favs))
    await callback.answer()

async def add_favorite_callback(callback: types.CallbackQuery):
    movie_id = int(callback.data.split("_")[2])
    if db.add_favorite(callback.from_user.id, movie_id):
        await callback.answer("✅ Добавлено в избранное!", show_alert=True)
        await update_movie_card_message(callback.message, movie_id, is_fav=True)
    else:
        await callback.answer("❌ Уже в избранном или ошибка", show_alert=True)

async def remove_favorite_callback(callback: types.CallbackQuery):
    movie_id = int(callback.data.split("_")[2])
    if db.remove_favorite(callback.from_user.id, movie_id):
        await callback.answer("🗑 Удалено из избранного!", show_alert=True)
        await update_movie_card_message(callback.message, movie_id, is_fav=False)
    else:
        await callback.answer("❌ Не удалось удалить", show_alert=True)

async def movie_callback(callback: types.CallbackQuery):
    movie_id = int(callback.data.split("_")[1])
    await send_movie_card(callback.message, movie_id, callback.from_user.id)
    await callback.answer()

# ---------- РЕКОМЕНДАЦИИ ----------
async def random_movie_callback(callback: types.CallbackQuery):
    movie = db.get_random_high_rated_movie()
    if not movie:
        await callback.message.edit_text("😔 Не удалось найти фильм с высоким рейтингом.")
    else:
        await send_movie_card(callback.message, movie['id_mov'], callback.from_user.id)
    await callback.answer()

async def top_movies_callback(callback: types.CallbackQuery):
    conn = db.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.id_mov, m.title, AVG(r.rating) as avg_rating
        FROM movies m
        JOIN reviews r ON m.id_mov = r.movies_id_mov
        GROUP BY m.id_mov
        ORDER BY avg_rating DESC
        LIMIT 10
    """)
    top = cursor.fetchall()
    cursor.close()
    conn.close()
    if not top:
        await callback.message.edit_text("Нет данных для топа.")
        return
    text = "🏆 *Топ-10 фильмов по рейтингу:*\n\n"
    for i, movie in enumerate(top, 1):
        text += f"{i}. {movie['title']} — {movie['avg_rating']:.1f}\n"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.back_button())
    await callback.answer()

# ---------- О БОТЕ ----------
async def about_bot_callback(callback: types.CallbackQuery):
    text = "🤖 *О боте*\n\nЭтот бот для онлайн-кинотеатра. Позволяет искать фильмы, оставлять отзывы, добавлять в избранное, покупать подписки и пополнять баланс.\n\nРазработан в рамках учебного проекта."
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.back_button())
    await callback.answer()

# ---------- НАВИГАЦИЯ ----------
async def back_to_main(callback: types.CallbackQuery):
    user = db.get_user_by_telegram_id(callback.from_user.id)
    if user and user.get('role') == 'admin':
        await callback.message.edit_text("🏠 *Главное меню*", parse_mode="HTML", reply_markup=kb.admin_main_menu())
    else:
        await callback.message.edit_text("🏠 *Главное меню*", parse_mode="HTML", reply_markup=kb.main_menu())
    await callback.answer()

async def back_to_profile(callback: types.CallbackQuery):
    await profile_callback(callback)

async def back_to_search(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Выберите действие:", reply_markup=kb.main_menu())
    await callback.answer()

# ---------- АДМИН-ПАНЕЛЬ ----------
async def admin_panel_callback(callback: types.CallbackQuery):
    user = db.get_user_by_telegram_id(callback.from_user.id)
    if not user or user.get('role') != 'admin':
        await callback.answer("У вас нет прав администратора.", show_alert=True)
        return
    await callback.message.edit_text("👑 Админ-панель:", reply_markup=kb.admin_menu())
    await callback.answer()

async def admin_add_movie_start(callback: types.CallbackQuery, state: FSMContext):
    user = db.get_user_by_telegram_id(callback.from_user.id)
    if not user or user.get('role') != 'admin':
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    await callback.message.edit_text("Введите название фильма:")
    await state.set_state(AdminStates.waiting_for_add_title)
    await callback.answer()

async def admin_add_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("Введите год выпуска (целое число):")
    await state.set_state(AdminStates.waiting_for_add_year)

async def admin_add_year(message: types.Message, state: FSMContext):
    try:
        year = int(message.text.strip())
        if year < 1888 or year > 2030:
            raise ValueError
        await state.update_data(release_year=year)
        await message.answer("Введите описание фильма:")
        await state.set_state(AdminStates.waiting_for_add_description)
    except ValueError:
        await message.answer("❌ Введите корректный год (от 1888 до 2030).")

async def admin_add_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer("Введите страну производства:")
    await state.set_state(AdminStates.waiting_for_add_country)

async def admin_add_country(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text.strip())
    types = db.get_movie_types()
    if not types:
        await message.answer("Нет доступных типов фильмов. Сначала добавьте типы в БД.")
        await state.clear()
        return
    await message.answer("Выберите тип фильма:", reply_markup=kb.admin_types_keyboard(types))
    await state.set_state(AdminStates.waiting_for_add_type)

async def admin_add_type_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "admin_types_done":
        data = await state.get_data()
        if 'type_id' not in data:
            await callback.answer("Вы не выбрали тип фильма!", show_alert=True)
            return
        await callback.message.edit_text("Теперь выберите жанры (можно несколько, после выбора нажмите 'Готово'):")
        genres = db.get_all_genres_list()
        await state.update_data(selected_genres=[])
        await callback.message.edit_reply_markup(reply_markup=kb.admin_genres_keyboard(genres, selected=[]))
        await state.set_state(AdminStates.waiting_for_add_genres)
        await callback.answer()
        return
    if callback.data.startswith("admin_type_"):
        type_id = int(callback.data.split("_")[2])
        await state.update_data(type_id=type_id)
        await callback.answer(f"Выбран тип ID {type_id}", show_alert=True)

async def admin_add_genres_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "admin_genres_done":
        data = await state.get_data()
        if not data.get('selected_genres'):
            await callback.answer("Выберите хотя бы один жанр!", show_alert=True)
            return
        await callback.message.edit_text("Теперь выберите режиссёров (можно несколько, после выбора нажмите 'Готово'):")
        directors = db.get_all_directors_list()
        await state.update_data(selected_directors=[])
        await callback.message.edit_reply_markup(reply_markup=kb.admin_directors_keyboard(directors, selected=[]))
        await state.set_state(AdminStates.waiting_for_add_directors)
        await callback.answer()
        return
    if callback.data.startswith("admin_genre_"):
        genre_id = int(callback.data.split("_")[2])
        data = await state.get_data()
        selected = data.get('selected_genres', [])
        if genre_id in selected:
            selected.remove(genre_id)
        else:
            selected.append(genre_id)
        await state.update_data(selected_genres=selected)
        genres = db.get_all_genres_list()
        await callback.message.edit_reply_markup(reply_markup=kb.admin_genres_keyboard(genres, selected=selected))
        await callback.answer()

async def admin_add_directors_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "admin_directors_done":
        data = await state.get_data()
        if not data.get('selected_directors'):
            await callback.answer("Выберите хотя бы одного режиссёра!", show_alert=True)
            return
        success, msg = db.add_movie(
            telegram_id=callback.from_user.id,
            title=data['title'],
            release_year=data['release_year'],
            description=data['description'],
            country=data['country'],
            type_id=data['type_id'],
            genre_ids=data['selected_genres'],
            director_ids=data['selected_directors']
        )
        await callback.message.edit_text(msg, reply_markup=kb.back_button())
        await state.clear()
        return
    if callback.data.startswith("admin_director_"):
        director_id = int(callback.data.split("_")[2])
        data = await state.get_data()
        selected = data.get('selected_directors', [])
        if director_id in selected:
            selected.remove(director_id)
        else:
            selected.append(director_id)
        await state.update_data(selected_directors=selected)
        directors = db.get_all_directors_list()
        await callback.message.edit_reply_markup(reply_markup=kb.admin_directors_keyboard(directors, selected=selected))
        await callback.answer()

async def admin_delete_movie_start(callback: types.CallbackQuery, state: FSMContext):
    user = db.get_user_by_telegram_id(callback.from_user.id)
    if not user or user.get('role') != 'admin':
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    await callback.message.edit_text("Введите точное название фильма, который хотите удалить:")
    await state.set_state(AdminStates.waiting_for_delete_title)
    await callback.answer()

async def admin_delete_movie_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    success, msg = db.delete_movie_by_title(message.from_user.id, title)
    await message.answer(msg, reply_markup=kb.back_button())
    await state.clear()

async def admin_ban_user_start(callback: types.CallbackQuery, state: FSMContext):
    user = db.get_user_by_telegram_id(callback.from_user.id)
    if not user or user.get('role') != 'admin':
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    await callback.message.edit_text("Введите логин пользователя, которого хотите забанить:")
    await state.set_state(AdminStates.waiting_for_ban_login)
    await callback.answer()

async def admin_ban_user_login(message: types.Message, state: FSMContext):
    await state.update_data(ban_login=message.text.strip())
    await message.answer("Введите время бана в минутах (целое число):")
    await state.set_state(AdminStates.waiting_for_ban_minutes)

async def admin_ban_user_minutes(message: types.Message, state: FSMContext):
    try:
        minutes = int(message.text.strip())
        if minutes <= 0:
            raise ValueError
        data = await state.get_data()
        ban_login = data['ban_login']
        success, msg = db.ban_user(message.from_user.id, ban_login, minutes)
        await message.answer(msg, reply_markup=kb.back_button())
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите целое положительное число (минуты).")

async def admin_unban_user_start(callback: types.CallbackQuery, state: FSMContext):
    user = db.get_user_by_telegram_id(callback.from_user.id)
    if not user or user.get('role') != 'admin':
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    await callback.message.edit_text("Введите логин пользователя, которого хотите разбанить:")
    await state.set_state(AdminStates.waiting_for_unban_login)
    await callback.answer()

async def admin_unban_user_login(message: types.Message, state: FSMContext):
    unban_login = message.text.strip()
    success, msg = db.unban_user(message.from_user.id, unban_login)
    await message.answer(msg, reply_markup=kb.back_button())
    await state.clear()

# ---------- РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ----------
def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_login, Command("login"))
    dp.message.register(cmd_register, Command("register"))
    dp.message.register(process_login, AuthStates.waiting_for_login)
    dp.message.register(process_password, AuthStates.waiting_for_password)
    dp.message.register(process_register_login, AuthStates.waiting_for_register_login)
    dp.message.register(process_register_password, AuthStates.waiting_for_register_password)
    dp.message.register(process_register_name, AuthStates.waiting_for_register_name)
    dp.message.register(process_register_surname, AuthStates.waiting_for_register_surname)
    dp.message.register(process_register_email, AuthStates.waiting_for_register_email)
    dp.callback_query.register(profile_callback, lambda c: c.data == "profile")
    dp.callback_query.register(logout_callback, lambda c: c.data == "logout")
    dp.callback_query.register(recharge_callback, lambda c: c.data and c.data.startswith("recharge"))
    dp.callback_query.register(buy_subscription_callback, lambda c: c.data and (c.data == "buy_sub" or c.data.startswith("buy_sub_")))
    dp.callback_query.register(search_title_callback, lambda c: c.data == "search_title")
    dp.callback_query.register(search_genre_callback, lambda c: c.data == "search_genre")
    dp.callback_query.register(search_director_callback, lambda c: c.data == "search_director")
    dp.callback_query.register(genre_selected_callback, lambda c: c.data and c.data.startswith("genre_"))
    dp.callback_query.register(director_selected_callback, lambda c: c.data and c.data.startswith("director_"))
    dp.callback_query.register(movie_callback, lambda c: c.data and c.data.startswith("movie_"))
    dp.callback_query.register(all_movies_callback, lambda c: c.data == "all_movies")
    dp.callback_query.register(all_movies_page_callback, lambda c: c.data and c.data.startswith("all_movies_page_"))
    dp.callback_query.register(show_reviews, lambda c: c.data and c.data.startswith("reviews_"))
    dp.callback_query.register(leave_review_start, lambda c: c.data and c.data.startswith("leave_review_"))
    dp.callback_query.register(favorites_callback, lambda c: c.data == "favorites")
    dp.callback_query.register(add_favorite_callback, lambda c: c.data and c.data.startswith("fav_add_"))
    dp.callback_query.register(remove_favorite_callback, lambda c: c.data and c.data.startswith("fav_remove_"))
    dp.callback_query.register(random_movie_callback, lambda c: c.data == "random_movie")
    dp.callback_query.register(top_movies_callback, lambda c: c.data == "top_movies")
    dp.callback_query.register(about_bot_callback, lambda c: c.data == "about_bot")
    dp.callback_query.register(back_to_main, lambda c: c.data == "back_to_main")
    dp.callback_query.register(back_to_profile, lambda c: c.data == "back_to_profile")
    dp.callback_query.register(back_to_search, lambda c: c.data == "back_to_search")
    dp.callback_query.register(admin_panel_callback, lambda c: c.data == "admin_panel")
    dp.callback_query.register(admin_add_movie_start, lambda c: c.data == "admin_add_movie")
    dp.callback_query.register(admin_delete_movie_start, lambda c: c.data == "admin_delete_movie")
    dp.callback_query.register(admin_ban_user_start, lambda c: c.data == "admin_ban_user")
    dp.callback_query.register(admin_unban_user_start, lambda c: c.data == "admin_unban_user")
    dp.message.register(admin_add_title, AdminStates.waiting_for_add_title)
    dp.message.register(admin_add_year, AdminStates.waiting_for_add_year)
    dp.message.register(admin_add_description, AdminStates.waiting_for_add_description)
    dp.message.register(admin_add_country, AdminStates.waiting_for_add_country)
    dp.callback_query.register(admin_add_type_callback, lambda c: c.data and (c.data.startswith("admin_type_") or c.data == "admin_types_done"))
    dp.callback_query.register(admin_add_genres_callback, lambda c: c.data and (c.data.startswith("admin_genre_") or c.data == "admin_genres_done"))
    dp.callback_query.register(admin_add_directors_callback, lambda c: c.data and (c.data.startswith("admin_director_") or c.data == "admin_directors_done"))
    dp.message.register(admin_delete_movie_title, AdminStates.waiting_for_delete_title)
    dp.message.register(admin_ban_user_login, AdminStates.waiting_for_ban_login)
    dp.message.register(admin_ban_user_minutes, AdminStates.waiting_for_ban_minutes)
    dp.message.register(admin_unban_user_login, AdminStates.waiting_for_unban_login)
    dp.message.register(process_custom_recharge, RechargeStates.waiting_for_custom_amount)
    dp.message.register(process_review_rating, ReviewStates.waiting_for_rating)
    dp.message.register(process_review_title, ReviewStates.waiting_for_title)
    dp.message.register(process_review_comment, ReviewStates.waiting_for_comment)
    dp.message.register(process_title_search, SearchStates.waiting_for_title)