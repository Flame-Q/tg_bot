from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню для обычного пользователя
def main_menu():
    buttons = [
        [InlineKeyboardButton(text="🔍 Поиск по названию", callback_data="search_title")],
        [InlineKeyboardButton(text="🎭 Поиск по жанру", callback_data="search_genre")],
        [InlineKeyboardButton(text="🎬 Поиск по режиссёру", callback_data="search_director")],
        [InlineKeyboardButton(text="⭐️ Топ фильмов", callback_data="top_movies")],
        [InlineKeyboardButton(text="🎲 Мне повезёт", callback_data="random_movie")],
        [InlineKeyboardButton(text="📋 Все фильмы", callback_data="all_movies")],
        [InlineKeyboardButton(text="❤️ Избранное", callback_data="favorites")],
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="profile")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about_bot")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Главное меню для администратора (добавлена кнопка "Админка")
def admin_main_menu():
    buttons = [
        [InlineKeyboardButton(text="🔍 Поиск по названию", callback_data="search_title")],
        [InlineKeyboardButton(text="🎭 Поиск по жанру", callback_data="search_genre")],
        [InlineKeyboardButton(text="🎬 Поиск по режиссёру", callback_data="search_director")],
        [InlineKeyboardButton(text="⭐️ Топ фильмов", callback_data="top_movies")],
        [InlineKeyboardButton(text="🎲 Мне повезёт", callback_data="random_movie")],
        [InlineKeyboardButton(text="📋 Все фильмы", callback_data="all_movies")],
        [InlineKeyboardButton(text="❤️ Избранное", callback_data="favorites")],
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="profile")],
        [InlineKeyboardButton(text="👑 Админка", callback_data="admin_panel")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about_bot")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Меню авторизации (если используется, но можно не использовать)
def auth_menu():
    buttons = [
        [InlineKeyboardButton(text="🔑 Войти", callback_data="login")],
        [InlineKeyboardButton(text="📝 Зарегистрироваться", callback_data="register")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Кнопка "Назад" в главное меню
def back_button():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]])

# Клавиатура для выбора подписки
def subscriptions_keyboard(subscriptions):
    buttons = []
    for sub in subscriptions:
        buttons.append([InlineKeyboardButton(text=f"{sub['name_sub']} - {sub['price']} руб.", callback_data=f"buy_sub_{sub['id_sub']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_profile")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для пополнения баланса
def recharge_keyboard():
    buttons = [
        [InlineKeyboardButton(text="💰 100 руб", callback_data="recharge_100")],
        [InlineKeyboardButton(text="💰 500 руб", callback_data="recharge_500")],
        [InlineKeyboardButton(text="💰 1000 руб", callback_data="recharge_1000")],
        [InlineKeyboardButton(text="✏️ Другая сумма", callback_data="recharge_custom")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_profile")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для карточки фильма (избранное, отзывы, кинопоиск)
def movie_actions(movie_id, is_favorite=False):
    if is_favorite:
        fav_text = "❤️ Убрать из избранного"
        fav_callback = f"fav_remove_{movie_id}"
    else:
        fav_text = "🤍 В избранное"
        fav_callback = f"fav_add_{movie_id}"
    buttons = [
        [InlineKeyboardButton(text="🎥 Смотреть на Кинопоиске", url=f"https://www.kinopoisk.ru/index.php?kp_query={movie_id}")],
        [InlineKeyboardButton(text="⭐️ Отзывы", callback_data=f"reviews_{movie_id}")],
        [InlineKeyboardButton(text=fav_text, callback_data=fav_callback)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_search")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для выбора жанра (список)
def genre_list_keyboard(genres):
    buttons = []
    for genre in genres:
        buttons.append([InlineKeyboardButton(text=genre, callback_data=f"genre_{genre}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для выбора режиссёра (список)
def director_list_keyboard(directors):
    buttons = []
    for director in directors:
        buttons.append([InlineKeyboardButton(text=director, callback_data=f"director_{director}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для списка избранных фильмов
def favorites_list_keyboard(favorites):
    buttons = []
    for fav in favorites:
        buttons.append([InlineKeyboardButton(text=f"{fav['title']} ({fav['release_year']})", callback_data=f"movie_{fav['id_mov']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для пагинации "Все фильмы"
def all_movies_paginated_keyboard(movies, current_page, total_pages):
    buttons = []
    for movie in movies:
        buttons.append([InlineKeyboardButton(
            text=f"{movie['title']} ({movie['release_year']})",
            callback_data=f"movie_{movie['id_mov']}"
        )])
    # Строка пагинации
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"all_movies_page_{current_page-1}"))
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"all_movies_page_{current_page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    # Кнопка возврата в главное меню
    buttons.append([InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Меню администратора (действия)
def admin_menu():
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить фильм", callback_data="admin_add_movie")],
        [InlineKeyboardButton(text="➖ Удалить фильм", callback_data="admin_delete_movie")],
        [InlineKeyboardButton(text="🚫 Забанить пользователя", callback_data="admin_ban_user")],
        [InlineKeyboardButton(text="✅ Разбанить пользователя", callback_data="admin_unban_user")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для выбора типа фильма (при добавлении)
def types_keyboard(types):
    buttons = []
    for t in types:
        buttons.append([InlineKeyboardButton(text=t['name'], callback_data=f"type_{t['id_type']}")])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="types_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для выбора жанров (с возможностью множественного выбора)
def genres_keyboard(genres, selected=None):
    if selected is None:
        selected = []
    buttons = []
    for g in genres:
        text = g['name_gen']
        if g['id_gen'] in selected:
            text = "✅ " + text
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"genre_{g['id_gen']}")])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="genres_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для выбора режиссёров (с возможностью множественного выбора)
def directors_keyboard(directors, selected=None):
    if selected is None:
        selected = []
    buttons = []
    for d in directors:
        text = d['full_name']
        if d['id_dir'] in selected:
            text = "✅ " + text
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"director_{d['id_dir']}")])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="directors_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для выбора типа фильма (админка)
def admin_types_keyboard(types, selected_id=None):
    buttons = []
    for t in types:
        text = t['name']
        if selected_id == t['id_type']:
            text = "✅ " + text
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"admin_type_{t['id_type']}")])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="admin_types_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_directors_keyboard(directors, selected=None):
    if selected is None:
        selected = []
    buttons = []
    for d in directors:
        text = d['full_name']
        if d['id_dir'] in selected:
            text = "✅ " + text
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"admin_director_{d['id_dir']}")])
    buttons.append([InlineKeyboardButton(text="➕ Добавить режиссёра", callback_data="admin_add_director")])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="admin_directors_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для выбора жанров (админка)
def admin_genres_keyboard(genres, selected=None):
    if selected is None:
        selected = []
    buttons = []
    for g in genres:
        text = g['name_gen']
        if g['id_gen'] in selected:
            text = "✅ " + text
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"admin_genre_{g['id_gen']}")])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="admin_genres_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для выбора режиссёров (админка)
def admin_directors_keyboard(directors, selected=None):
    if selected is None:
        selected = []
    buttons = []
    for d in directors:
        text = d['full_name']
        if d['id_dir'] in selected:
            text = "✅ " + text
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"admin_director_{d['id_dir']}")])
    buttons.append([InlineKeyboardButton(text="➕ Добавить режиссёра", callback_data="admin_add_director")])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="admin_directors_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)