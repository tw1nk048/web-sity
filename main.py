import hashlib
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, session, redirect, url_for, flash
import psycopg2

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = {
    'dbname': 'Diplom',
    'user': 'postgres',
    'password': '0000',
    'host': 'localhost'
}


def connect_db():
    return psycopg2.connect(**DATABASE)


@app.route('/')
def home():
    username = session.get('username')
    role = session.get('role')
    return render_template('home.html', username=username, role=role)


@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = connect_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        # Получение данных из формы
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            # Проверка пользователя в базе данных
            cursor.execute("""
                SELECT * FROM "user" WHERE login = %s AND password = %s
            """, (username, password))
            user = cursor.fetchone()

            if user:
                # Сохранение информации о пользователе в сессии
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                flash("Вы успешно вошли!", "success")
                return redirect(url_for('profile'))  # Переход на страницу профиля
            else:
                flash("Неверный логин или пароль.", "error")
        except psycopg2.Error as e:
            flash(f"Ошибка базы данных: {e.pgerror}", "error")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    conn = connect_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        # Получение данных из формы
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        role = request.form.get('role')  # "patient" или "doctor"
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        middle_name = request.form.get('middleName')

        # Проверка совпадения паролей
        if password != confirm_password:
            flash("Пароли не совпадают!", "error")
            return render_template('register.html')

        # Запись в таблицу user
        cursor.execute("""
            INSERT INTO "user" (login, password, role)
            VALUES (%s, %s, %s) RETURNING id_user
        """, (username, password, role))
        id_user = cursor.fetchone()[0]  # Получаем ID только что созданного пользователя

        # Вставка в таблицы patient или doctor
        if role == 'patient':
            policy = request.form.get('policy')
            birth_date = request.form.get('birthDate')
            cursor.execute("""
                INSERT INTO patient (surname, name, middlename, policy, dataofbirth, id_user)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (last_name, first_name, middle_name, policy, birth_date, id_user))
        elif role == 'doctor':
            specialization = request.form.get('specialization')
            experience = request.form.get('experience')
            cursor.execute("""
                INSERT INTO doctor (surname, name, middlename, specialization, experience, id_user)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (last_name, first_name, middle_name, specialization, experience, id_user))

        # Сохранение изменений в базе данных
        conn.commit()
        flash("Регистрация прошла успешно!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Вы вышли из системы.")
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    # Проверяем, авторизован ли пользователь
    if 'user_id' not in session:
        flash("Вы должны войти, чтобы увидеть профиль.", "error")
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()

    user_id = session['user_id']

    # Получаем данные пользователя
    cursor.execute("""
        SELECT id_user, login, role FROM "user" WHERE id_user = %s
    """, (user_id,))
    user = cursor.fetchone()

    if not user:
        flash("Пользователь не найден.", "error")
        return redirect(url_for('home'))

    # Инициализируем дополнительные данные
    details = None

    # В зависимости от роли пользователя, получаем доп. информацию
    if user[2] == 'patient':  # Если пользователь пациент
        cursor.execute("""
            SELECT surname, name, middlename, policy, dataofbirth 
            FROM "patient" WHERE id_user = %s
        """, (user_id,))
        details = cursor.fetchone()
    elif user[2] == 'doctor':  # Если пользователь врач
        cursor.execute("""
            SELECT surname, name, middlename, specialization, experience 
            FROM "doctor" WHERE id_user = %s
        """, (user_id,))
        details = cursor.fetchone()

    # Закрываем соединение
    conn.close()

    # Передаем данные в шаблон
    return render_template('profile.html', user=user, details=details)


@app.route('/chat')
def chat():
    # Проверка, что пользователь авторизован
    if 'user_id' not in session:
        flash("Пожалуйста, войдите для доступа к чату.", "error")
        return redirect(url_for('login'))  # Перенаправление на страницу входа
    return render_template('chat.html')


if __name__ == '__main__':
    app.run(debug=True)