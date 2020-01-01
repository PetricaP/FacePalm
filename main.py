import datetime
import functools
import hashlib
import os

import flask
import flask_login
import psycopg2
from PIL import Image
from flask_login import UserMixin as User


def format_date(date):
    return f'{date.day:02d}.{date.month:02d}.{date.year}'


def format_time(time):
    return f'{time.hour:02d}:{time.minute:02d}:{time.second:02d}'


def create_tables(connection):
    with open('sql/create_tables.sql', 'r') as script:
        with connection.cursor() as cursor:
            cursor.execute(script.read())
        connection.commit()


def admin_login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if flask_login.current_user.is_authenticated and flask_login.current_user.id == 'admin':
            return func(*args, **kwargs)
        else:
            flask.abort(404)

    return wrapper


def create_app(db_connection):
    app = flask.Flask('Server')

    app.secret_key = b'(`R\x1e\x0bN\xdb9\xab1\x84\x97\xa4\xc8M\x07'

    @app.route('/users/<username>', methods=['GET', 'POST'])
    @flask_login.login_required
    def user_page(username):
        cursor = db_connection.cursor()
        cursor.execute(
            'SELECT id, first_name, last_name, birth_date, profile_photo_path FROM "user" WHERE username=%s',
            (username,))

        entry = cursor.fetchone()
        if not entry:
            flask.abort(404)

        user_id, first_name, last_name, birth_date, profile_photo_path = entry

        formatted_date = format_date(birth_date)
        if profile_photo_path is None:
            profile_photo_path = '/static/images/anonim.jpg'

        cursor.execute('SELECT id, content, date_added, time_added FROM user_post WHERE user_id=%s', (user_id,))
        post_entries = cursor.fetchall()

        posts = []
        for post_id, post_content, post_date_added, post_time_added in post_entries:
            cursor.execute(
                'SELECT user_id, content, date_added, time_added FROM user_post_comment WHERE post_id=%s ORDER BY '
                'date_added ASC, time_added ASC', (post_id,))
            comment_entries = cursor.fetchall()

            comments = []
            for user_id, comment_content, comment_date_added, comment_time_added in comment_entries:
                cursor.execute('SELECT first_name, last_name FROM "user" WHERE id=%s', (user_id,))
                user_first_name, user_last_name = cursor.fetchone()

                formatted_comment_date = format_date(comment_date_added)
                formatted_comment_time = format_time(comment_time_added)

                comments.append({'content': comment_content,
                                 'date_added': formatted_comment_date,
                                 'time_added': formatted_comment_time,
                                 'user': f'{user_first_name} {user_last_name}'})

            formatted_post_date = format_date(post_date_added)
            formatted_post_time = format_time(post_time_added)

            posts.append({'id': post_id,
                          'content': post_content,
                          'date_added': formatted_post_date,
                          'time_added': formatted_post_time,
                          'comments': comments})

        return flask.render_template('user_profile.html',
                                     username=username,
                                     first_name=first_name,
                                     last_name=last_name,
                                     profile_photo_path=profile_photo_path,
                                     birth_date=formatted_date,
                                     posts=posts)

    @app.route('/')
    def hello_world():
        return flask.send_from_directory('UI', 'index.html')

    @app.route('/signup', methods=['POST', 'GET'])
    def signup():
        if flask.request.method == 'GET':
            return flask.send_from_directory('UI', 'signup.html')
        else:
            username = flask.request.form['username']
            password = flask.request.form['password']
            re_password = flask.request.form['re_password']
            first_name = flask.request.form['first_name']
            last_name = flask.request.form['last_name']
            email = flask.request.form['email']
            bday = flask.request.form['bday']
            bmonth = flask.request.form['bmonth']
            byear = flask.request.form['byear']

            if not all([username, password, re_password, first_name, last_name, email]):
                return '<h1>All fields are required</h1>'

            cursor = db_connection.cursor()
            cursor.execute('SELECT username FROM "user" WHERE username=%s', (username,))
            if cursor.fetchone():
                return '<h1>Username already in use</h1>'

            if password != re_password:
                return '<h1>Passwords don\'t match</h1>'

            # TODO: Check email, better error handling
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            birth_date = datetime.date(int(byear), int(bmonth), int(bday))

            cursor.execute('INSERT INTO "user" (username, password_hash, first_name, last_name, email, birth_date)'
                           ' VALUES(%s, %s, %s, %s, %s, %s)',
                           (username, password_hash, first_name, last_name, email, birth_date))
            db_connection.commit()

            user = User()
            user.id = username

            flask_login.login_user(user)

            return flask.redirect(f'/users/{username}')

    @app.route('/login', methods=['POST', 'GET'])
    def login():
        if flask.request.method == 'GET':
            return flask.send_from_directory('UI', 'login.html')
        else:
            username = flask.request.form['username']
            password = flask.request.form['password']

            cursor = db_connection.cursor()
            cursor.execute('SELECT username, password_hash FROM "user" WHERE username=%s', (username,))
            entry = cursor.fetchone()

            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if entry and password_hash == entry[1]:
                user = User()
                user.id = username

                flask_login.login_user(user)

                return flask.redirect(f'/users/{username}')

            return f'<h1>User {username} does not exist</h1>'

    @app.route('/search', methods=['GET'])
    @flask_login.login_required
    def search():
        query = flask.request.args['query']
        if not query:
            flask.abort(404)
        first_name, last_name = query.split(maxsplit=1)

        cursor = db_connection.cursor()
        cursor.execute('SELECT username FROM "user" WHERE last_name=%s AND first_name=%s', (last_name, first_name))

        result = cursor.fetchone()
        if not result:
            flask.abort(404)

        username = result[0]
        return flask.redirect(f'/users/{username}')

    @app.route("/logout")
    @flask_login.login_required
    def logout():
        flask_login.logout_user()
        return flask.redirect('/')

    @app.route('/create_post', methods=['POST'])
    @flask_login.login_required
    def create_post():
        username = flask.request.form['username']
        content = flask.request.form['content']

        if not content:
            return flask.redirect(f'/users/{username}')

        cursor = db_connection.cursor()
        cursor.execute('SELECT id FROM "user" WHERE username=%s', (username,))
        id_entry = cursor.fetchone()

        if not id_entry:
            return flask.redirect(f'/users/{username}')

        user_id = id_entry[0]
        cursor.execute('INSERT INTO user_post (user_id, content) VALUES (%s, %s)', (user_id, content))
        db_connection.commit()

        return flask.redirect(f'/users/{username}')

    @app.route('/create_comment', methods=['POST'])
    @flask_login.login_required
    def create_comment():
        username = flask.request.form['username']
        content = flask.request.form['content']
        post_id = flask.request.form['post_id']

        if not content:
            return flask.redirect(f'/users/{username}')

        cursor = db_connection.cursor()
        cursor.execute('SELECT id FROM "user" WHERE username=%s', (flask_login.current_user.id,))
        id_entry = cursor.fetchone()

        if not id_entry:
            return flask.redirect(f'/users/{username}')

        user_id = id_entry[0]

        cursor.execute('INSERT INTO user_post_comment (post_id, user_id, content) VALUES (%s, %s, %s)',
                       (post_id, user_id, content))
        db_connection.commit()

        return flask.redirect(f'/users/{username}')

    @flask_login.login_required
    @app.route('/update_user', methods=['POST'])
    def update_user():
        if 'new_profile_photo' in flask.request.files:
            photo = flask.request.files['new_profile_photo']

            _, ext = os.path.splitext(photo.filename)
            if ext[1:] not in ['jpg', 'png', 'jpeg', 'bmp']:
                return flask.redirect(f'/users/{flask_login.current_user.id}')

            local_path = f'static/images/{os.path.basename(photo.filename)}'

            photo.save(local_path)

            image = Image.open(local_path)
            width, height = image.size

            if width != 300 or height != 300:
                if width != height:
                    side = min((width, height))
                    center_x, center_y = width // 2, height // 2

                    crop_left = 0 if width <= side else center_x - side // 2
                    crop_right = crop_left + side

                    crop_top = 0 if height <= side else center_y - side // 2
                    crop_bottom = crop_top + side

                    image = image.crop((crop_left, crop_top, crop_right, crop_bottom))

                image = image.resize((300, 300))

                image.save(local_path)

            cursor = db_connection.cursor()
            server_path = '/' + local_path
            cursor.execute('UPDATE "user" SET profile_photo_path=%s WHERE username=%s',
                           (server_path, flask_login.current_user.id))
            db_connection.commit()

        return flask.redirect(f'/users/{flask_login.current_user.id}')

    @app.route('/admin')
    def admin_main_page():
        return flask.send_from_directory('UI/admin', 'index.html')

    @app.route('/admin/<table_name>')
    @admin_login_required
    def admin_table_view(table_name):
        cursor = db_connection.cursor()

        cursor.execute('SELECT column_name FROM information_schema.COLUMNS WHERE table_name=%s', (table_name,))
        column_entries = cursor.fetchall()
        if not column_entries:
            flask.abort(404)

        cursor.execute(
            'SELECT a.attname FROM  pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY('
            f'i.indkey) WHERE  i.indrelid = \'"{table_name}"\'::regclass AND i.indisprimary;')
        primary_keys_entries = cursor.fetchall()
        primary_keys = [p[0] for p in primary_keys_entries]

        cursor.execute(f'SELECT * FROM "{table_name}"')
        entries = cursor.fetchall()

        info = {
            'title': table_name.upper(),
            'keys': [c[0] for c in column_entries],
            'primary_keys': primary_keys,
            'entries': entries
        }

        return flask.render_template('admin/table_template.html', table_name=table_name, info=info)

    @app.route('/delete/<table_name>', methods=['POST'])
    def delete(table_name):
        cursor = db_connection.cursor()
        cursor.execute(f'SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)', (table_name, ))
        entry = cursor.fetchone()
        if not entry:
            flask.abort(404)

        cursor.execute(
            'SELECT a.attname FROM  pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY('
            'i.indkey) WHERE  i.indrelid =%s::regclass AND i.indisprimary;', (table_name, ))
        primary_keys_entries = cursor.fetchall()
        primary_keys = [p[0] for p in primary_keys_entries]

        if primary_keys:
            query = f'DELETE FROM "{table_name}" WHERE '
            added = 0
            for primary_key in primary_keys:
                if primary_key in flask.request.form:
                    query += f'{" AND " if added != 0 else ""}{primary_key}={flask.request.form[primary_key]}'
                    added += 1
            if added == 0:
                flask.abort(400)
        else:
            query = f'DELETE FROM "{table_name}" WHERE '
            added = 0
            for key, value in flask.request.form.values():
                query += f'{" AND " if added != 0 else ""}{key}={value}'
                added += 1

        try:
            cursor.execute(query)
        except Exception as e:
            print(e)
            flask.flash(str(e))
            flask.abort(400)

        db_connection.commit()

        return flask.redirect(flask.request.referrer)

    @app.route('/update/<table_name>', methods=['POST'])
    def update(table_name):
        cursor = db_connection.cursor()
        cursor.execute(f'SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)', (table_name, ))
        entry = cursor.fetchone()
        if not entry:
            flask.abort(404)

        cursor.execute(
            'SELECT a.attname FROM  pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY('
            'i.indkey) WHERE  i.indrelid =%s::regclass AND i.indisprimary;', (table_name, ))
        primary_keys_entries = cursor.fetchall()
        primary_keys = [p[0] for p in primary_keys_entries]

        form_data = dict(flask.request.form)
        query = f'UPDATE "{table_name}" SET '

        added = 0
        keys_to_remove = []
        for key in form_data:
            if key.startswith('__'):
                query += f'{", " if added != 0 else ""}{key[2:]}=\'{form_data[key]}\''
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del form_data[key]

        if not keys_to_remove:
            flask.abort(400)

        query += ' WHERE '
        if primary_keys:
            added = 0
            for primary_key in primary_keys:
                if primary_key in form_data:
                    query += f'{" AND " if added != 0 else ""}{primary_key}={form_data[primary_key]}'
                    added += 1
            if added == 0:
                flask.abort(400)
        else:
            added = 0
            for key, value in flask.request.form.values():
                query += f'{" AND " if added != 0 else ""}{key}={value}'
                added += 1

        try:
            cursor.execute(query)
        except Exception as e:
            print(e)
            flask.flash(str(e))
            flask.abort(400)

        db_connection.commit()

        return flask.redirect(flask.request.referrer)

    return app


def main():
    db_connection = psycopg2.connect(host='localhost', database='bdp', user='postgres', password='password')
    create_tables(db_connection)

    app = create_app(db_connection)

    login_manager = flask_login.LoginManager()

    @login_manager.user_loader
    def load_user(user_id):
        cursor = db_connection.cursor()
        cursor.execute('SELECT username FROM "user" WHERE username=%s', (user_id,))
        entry = cursor.fetchone()
        if not entry:
            return None
        user = User()
        user.id = entry[0]
        return user

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        return flask.redirect('/login')

    login_manager.init_app(app)

    app.run(host='localhost', port=9090)

    db_connection.close()


if __name__ == '__main__':
    main()
