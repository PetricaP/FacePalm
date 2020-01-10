import datetime
import functools
import hashlib
import os
import re

import flask
import flask_login
import psycopg2
from PIL import Image
from flask_login import UserMixin as User

EMAIL_REGEX = r'''^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$'''


def format_date(date):
    return f'{date.day:02d}.{date.month:02d}.{date.year}'


def format_time(time):
    return f'{time.hour:02d}:{time.minute:02d}:{time.second:02d}'


def transform_data(data, data_type):
    if data_type == 'integer':
        data = int(data)
    elif data_type == 'date':
        data = datetime.datetime.strptime(data, '%Y-%m-%d') if data != 'None' else None
    return data


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


def validate_form_data():
    error_flag = False
    username = flask.request.form['username']
    if not username:
        flask.flash('You must supply a username')
        error_flag = True
    else:
        if len(username) > 30:
            flask.flash('The username must have 30 characters or less')
            error_flag = True

        if not username[0].isalpha():
            flask.flash('The username must start with a letter')
            error_flag = True

        if any([not (c.isalnum() or c in {'_', '.'}) for c in username]):
            flask.flash('The username can only contain letters, numbers, "." and "_"')
            error_flag = True
    password = flask.request.form['password']
    if not password:
        flask.flash('You must supply a password')
        error_flag = True
    else:
        # Normally I would make more password checks, but for testing purposes this is better
        if len(password) < 8:
            flask.flash('Password needs to be 8 characters or longer')
            error_flag = True
        if any([c not in '@!#$%^&*()_.' for c in password]):
            flask.flash('Password can only contain alphanumeric characters and any of @!#$%^&*()_.')
            error_flag = True

    re_password = flask.request.form['re_password']
    first_name = flask.request.form['first_name']
    if not first_name:
        flask.flash('You must supply a First Name')
        error_flag = True
    elif not first_name.isalpha():
        flask.flash('Your name can only contain letters')
        error_flag = True

    last_name = flask.request.form['last_name']
    if not last_name:
        flask.flash('You must supply a Last Name')
        error_flag = True
    elif not last_name.isalpha():
        flask.flash('Your name can only contain letters')
        error_flag = True

    email = flask.request.form['email']
    if not re.match(EMAIL_REGEX, email):
        flask.flash('Invalid email')
        error_flag = True

    bday = flask.request.form['bday']
    if not bday or not bday.isnum() or int(bday) < 1 or int(bday) > 31:
        flask.flash('Invalid birth date')
        error_flag = True

    bmonth = flask.request.form['bmonth']
    if not bmonth or not bmonth.isnum() or int(bmonth) < 1 or int(bmonth) > 12:
        flask.flash('Invalid birth date')
        error_flag = True

    byear = flask.request.form['byear']
    if not byear or not byear.isnum() or int(byear) < 1900 or int(byear) > 2015:
        flask.flash('Invalid birth date')
        error_flag = True

    return error_flag, bday, bmonth, byear, email, first_name, last_name, password, re_password, username


def create_app(db_connection):
    app = flask.Flask('Server')

    app.secret_key = b'(`R\x1e\x0bN\xdb9\xab1\x84\x97\xa4\xc8M\x07'

    @app.route('/users/<username>', methods=['GET', 'POST'])
    @flask_login.login_required
    def user_page(username):
        with db_connection.cursor() as cursor:
            try:
                cursor.execute(
                    'SELECT'
                    '  id,'
                    '  first_name,'
                    '  last_name,'
                    '  birth_date,'
                    '  profile_photo_path '
                    'FROM'
                    '  "user" '
                    'WHERE '
                    '  username=%s',
                    (username,))
            except psycopg2.DatabaseError:
                flask.abort(400)

            entry = cursor.fetchone()
            if not entry:
                flask.abort(404)

            user_id, first_name, last_name, birth_date, profile_photo_path = entry

            formatted_date = format_date(birth_date)
            if profile_photo_path is None:
                profile_photo_path = '/static/images/anonim.jpg'

            current_username = flask_login.current_user.id

            cursor.execute('SELECT id FROM "user" WHERE username=%s', (current_username,))
            current_id = cursor.fetchone()[0]

            friend_requests = get_user_friend_requests(cursor, current_id)

            my_groups = get_user_groups(cursor, current_id)

            my_friends = get_user_friends(cursor, current_id)

            group_invitations = get_user_group_invitations(cursor, current_id)

            is_friend = None
            if current_username != username:
                cursor.execute(
                    'SELECT * FROM user_friend WHERE (user1_id=%s AND user2_id=%s) OR (user1_id=%s AND user2_id=%s)',
                    (user_id, current_id, current_id, user_id))
                if cursor.fetchone():
                    is_friend = 1
                else:
                    cursor.execute('SELECT * FROM user_friend_request WHERE friend_id=%s AND user_id=%s',
                                   (user_id, current_id))
                    if cursor.fetchone():
                        is_friend = 2
                    else:
                        cursor.execute('SELECT * FROM user_friend_request WHERE friend_id=%s AND user_id=%s',
                                       (current_id, user_id))
                        if cursor.fetchone():
                            is_friend = 3
                        else:
                            is_friend = 0

            cursor.execute('SELECT id, content, date_added, time_added FROM user_post WHERE user_id=%s', (user_id,))
            post_entries = cursor.fetchall()

            posts = []
            for post_id, post_content, post_date_added, post_time_added in post_entries:
                cursor.execute(
                    'SELECT user_id, content, date_added, time_added FROM user_post_comment WHERE post_id=%s ORDER BY '
                    'date_added ASC, time_added ASC', (post_id,))
                comment_entries = cursor.fetchall()

                comments = []
                for comment_user_id, comment_content, comment_date_added, comment_time_added in comment_entries:
                    cursor.execute('SELECT username, first_name, last_name, profile_photo_path FROM "user" WHERE id=%s',
                                   (comment_user_id,))
                    comment_username, user_first_name, user_last_name, user_profile_photo = cursor.fetchone()

                    formatted_comment_date = format_date(comment_date_added)
                    formatted_comment_time = format_time(comment_time_added)

                    comments.append({'content': comment_content,
                                     'date_added': formatted_comment_date,
                                     'time_added': formatted_comment_time,
                                     'username': comment_username,
                                     'user': f'{user_first_name} {user_last_name}',
                                     'user_profile_photo': user_profile_photo or '/static/images/anonim.jpg'})

                formatted_post_date = format_date(post_date_added)
                formatted_post_time = format_time(post_time_added)

                posts.append({'id': post_id,
                              'content': post_content,
                              'date_added': formatted_post_date,
                              'time_added': formatted_post_time,
                              'comments': comments})

        return flask.render_template('user_profile.html',
                                     user_id=user_id,
                                     username=username,
                                     first_name=first_name,
                                     last_name=last_name,
                                     profile_photo_path=profile_photo_path,
                                     birth_date=formatted_date,
                                     posts=posts,
                                     friend_requests=friend_requests,
                                     my_groups=my_groups,
                                     my_friends=my_friends,
                                     is_friend=is_friend,
                                     group_invitations=group_invitations)

    def get_user_groups(cursor, current_id):
        cursor.execute(
            'SELECT '
            '  g.id, '
            '  g.name '
            'FROM '
            '  "group" g, '
            '  "user" u, '
            '  "user_group" ug '
            'WHERE '
            '  g.id = ug.group_id '
            '  AND ug.user_id = u.id '
            '  AND u.id = %s',
            (current_id,))
        entries = cursor.fetchall()
        my_groups = [{
            'id': e[0],
            'name': e[1]
        } for e in entries]
        return my_groups

    def get_user_friend_requests(cursor, current_id):
        cursor.execute(
            'SELECT '
            '  first_name, '
            '  last_name, '
            '  profile_photo_path, '
            '  id, '
            '  username '
            'FROM'
            '  user_friend_request r,'
            '  "user" u '
            'WHERE '
            'friend_id=%s '
            'AND user_id=id',
            (current_id,)
        )
        entries = cursor.fetchall()
        friend_requests = [{
            'first_name': e[0],
            'last_name': e[1],
            'profile_photo_path': e[2] or '/static/images/anonim.jpg',
            'id': e[3],
            'username': e[4]
        } for e in entries]
        return friend_requests

    def get_user_friends(cursor, current_id):
        cursor.execute(
            'SELECT '
            '  f.id, '
            '  f.username, '
            '  f.first_name, '
            '  f.last_name, '
            '  f.profile_photo_path '
            'FROM '
            '  "user" u, '
            '  "user" f, '
            '  user_friend uf '
            'WHERE '
            '  ((u.id = uf.user1_id '
            '    AND f.id = uf.user2_id) '
            '   OR '
            '   (u.id = uf.user2_id '
            '   AND f.id = uf.user1_id)) '
            '  AND u.id = %s',
            (current_id,)
        )
        entries = cursor.fetchall()

        friends = [{
            'id': e[0],
            'username': e[1],
            'first_name': e[2],
            'last_name': e[3],
            'profile_photo_path': e[4] or '/static/images/anonim.jpg',
        } for e in entries]

        return friends

    def get_user_group_invitations(cursor, user_id):
        cursor.execute(
            'SELECT'
            '  i.host_id, '
            '  i.group_id, '
            '  g.name, '
            '  u.username, '
            '  u.first_name, '
            '  u.last_name, '
            '  u.profile_photo_path '
            'FROM '
            '  "group" g, '
            '  group_invitation i, '
            '  "user" u '
            'WHERE '
            '  g.id = i.group_id '
            '  AND i.host_id=u.id'
            '  AND i.guest_id=%s', (user_id, ))
        entries = cursor.fetchall()

        return [{
            'host_id': e[0],
            'group_id': e[1],
            'group_name': e[2],
            'username': e[3],
            'first_name': e[4],
            'last_name': e[5],
            'profile_photo_path': e[6] or '/static/images/anonim.jpg'
        } for e in entries]

    @app.route('/add_friend', methods=['POST'])
    @flask_login.login_required
    def add_friend():
        current_username = flask_login.current_user.id
        username = flask.request.form['username']

        with db_connection as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT id FROM "user" WHERE username=%s', (current_username,))
                current_id = cursor.fetchone()[0]

                try:
                    cursor.execute('SELECT id FROM "user" WHERE username=%s', (username,))
                except psycopg2.DatabaseError:
                    flask.abort(400)

                user_id = cursor.fetchone()
                if not user_id:
                    flask.abort(400)
                user_id = user_id[0]

                cursor.execute('SELECT * FROM user_friend WHERE (user1_id=%s AND user2_id = %s) OR'
                               ' (user1_id=%s AND user2_id=%s)', (user_id, current_id, current_id, user_id))
                if cursor.fetchone():
                    flask.flash(f'User {username} is already your friend.')
                    return flask.redirect(flask.request.referrer)

                try:
                    cursor.execute('INSERT INTO user_friend_request VALUES(%s, %s)', (user_id, current_id))
                except psycopg2.IntegrityError:
                    flask.flash(f'You have already send a request to the user {username}.')
                    return flask.redirect(flask.request.referrer)

        return flask.redirect(flask.request.referrer)

    @app.route('/resolve_friend_request', methods=['POST'])
    @flask_login.login_required
    def resolve_friend_request():
        current_username = flask_login.current_user.id
        user_id = flask.request.form['user_id']

        with db_connection as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT id FROM "user" WHERE username=%s', (current_username,))
                curr_id = cursor.fetchone()[0]

                try:
                    cursor.execute('SELECT id FROM "user" WHERE id=%s', (int(user_id),))
                except psycopg2.DatabaseError:
                    flask.flash(f'Malformed user id: {user_id}')
                    return flask.redirect(flask.request.referrer)

                if not cursor.fetchone():
                    flask.flash(f'User with id {user_id} does not exist')
                    return flask.redirect(flask.request.referrer)

                cursor.execute('DELETE FROM user_friend_request WHERE friend_id=%s AND user_id=%s',
                               (curr_id, int(user_id)))

                if 'accept' in flask.request.form:
                    try:
                        cursor.execute('INSERT INTO user_friend VALUES(%s, %s)', (curr_id, int(user_id)))
                    except psycopg2.IntegrityError:
                        flask.flash(f'User with id {user_id} is already your friend')
                        return flask.redirect(flask.request.referrer)

        return flask.redirect(flask.request.referrer)

    @app.route('/resolve_group_invitation', methods=['POST'])
    def resolve_group_invitations():
        host_id = flask.request.form['host_id']
        group_id = flask.request.form['group_id']

        try:
            host_id = int(host_id)
        except ValueError:
            flask.flash('Invalid host id')
            return flask.redirect(flask.request.referrer)

        try:
            group_id = int(group_id)
        except ValueError:
            flask.flash('Invalid group id')
            return flask.redirect(flask.request.referrer)

        with db_connection:
            with db_connection.cursor() as cursor:
                cursor.execute('SELECT id FROM "user" WHERE username=%s', (flask_login.current_user.id, ))
                guest_id = cursor.fetchone()[0]

                cursor.execute('SELECT role FROM group_invitation WHERE host_id=%s AND guest_id=%s AND group_id=%s',
                               (host_id, guest_id, group_id))
                entry = cursor.fetchone()
                if not entry:
                    flask.flash('You haven\'t received an invitation')
                    return flask.redirect(flask.request.referrer)

                role = entry[0]

                try:
                    cursor.execute('DELETE FROM group_invitation WHERE host_id=%s AND guest_id=%s AND group_id=%s',
                                   (host_id, guest_id, group_id))
                except psycopg2.DatabaseError:
                    flask.flash('Invalid form parameters')
                    return flask.redirect(flask.request.referrer)

                if 'accept' in flask.request.form:
                    try:
                        cursor.execute('INSERT INTO user_group VALUES(%s, %s, %s)', (guest_id, group_id, role))
                    except psycopg2.DatabaseError:
                        flask.flash('Invalid form parameters')
                        return flask.redirect(flask.request.referrer)

        return flask.redirect(flask.request.referrer)

    @app.route('/')
    def hello_world():
        return flask.send_from_directory('UI', 'index.html')

    @app.route('/signup', methods=['POST', 'GET'])
    def signup():
        if flask.request.method == 'GET':
            if flask_login.current_user.is_authenticated:
                return flask.redirect(f'/users/{flask_login.current_user.id}')

            return flask.render_template('signup.html')
        else:
            error_flag, bday, bmonth, byear, email, first_name, last_name, password, re_password, username = \
                validate_form_data()

            if error_flag:
                return flask.redirect(flask.request.referrer)

            with db_connection:
                with db_connection.cursor() as cursor:
                    cursor.execute('SELECT username FROM "user" WHERE username=%s', (username,))
                    if cursor.fetchone():
                        flask.flash('Username already in use')
                        return flask.redirect(flask.request.referrer)

                    if password != re_password:
                        flask.flash('Passwords don\'t match')
                        return flask.redirect(flask.request.referrer)

                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    birth_date = datetime.date(int(byear), int(bmonth), int(bday))

                    # If this fails, it's a programming error and should be detected, the user will get an internal
                    # server error
                    cursor.execute('INSERT INTO'
                                   '  "user" ('
                                   '    username, '
                                   '    password_hash, '
                                   '    first_name, '
                                   '    last_name, '
                                   '    email, '
                                   '    birth_date)'
                                   'VALUES(%s, %s, %s, %s, %s, %s)',
                                   (username, password_hash, first_name, last_name, email, birth_date))

            user = User()
            user.id = username

            flask_login.login_user(user)

            return flask.redirect(f'/users/{username}')

    @app.route('/login', methods=['POST', 'GET'])
    def login():
        if flask.request.method == 'GET':
            if flask_login.current_user.is_authenticated:
                return flask.redirect(f'/users/{flask_login.current_user.id}')

            return flask.render_template('login.html')
        else:
            username = flask.request.form['username']
            password = flask.request.form['password']

            with db_connection.cursor() as cursor:
                try:
                    cursor.execute('SELECT username, password_hash FROM "user" WHERE username=%s', (username,))
                except psycopg2.DatabaseError:
                    flask.flash('Invalid credentials supplied')
                    return flask.redirect(flask.request.referrer)

                entry = cursor.fetchone()

            if not entry:
                flask.flash('The specified user does not exist')
                return flask.redirect(flask.request.referrer)

            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash == entry[1]:
                user = User()
                user.id = username

                flask_login.login_user(user)

                if username == 'admin':
                    return flask.redirect('/admin')
                else:
                    return flask.redirect(f'/users/{username}')
            else:
                flask.flash('Wrong password, contact the admin to implement "Forgot your password"')
                return flask.redirect(flask.request.referrer)

    @app.route('/search', methods=['GET'])
    @flask_login.login_required
    def search():
        value = flask.request.args['query']

        attribute = flask.request.args['attribute']
        if attribute not in {'username', 'first_name', 'last_name', 'email'}:
            flask.flash(f'Invalid attribute: {attribute}')
            return flask.redirect(flask.request.referrer)

        with db_connection.cursor() as cursor:
            try:
                cursor.execute(
                    'SELECT '
                    '  username, '
                    '  first_name, '
                    '  last_name, '
                    '  email, '
                    '  profile_photo_path '
                    'FROM '
                    '  "user" '
                    'WHERE '
                    f'LOWER({attribute}) LIKE %s',
                    ('%' + value.lower() + '%',))

            except psycopg2.DatabaseError:
                flask.flash(f'Malformed value: {value}')
                return flask.redirect(flask.request.referrer)

            entries = cursor.fetchall()
            if not entries:
                flask.flash('No users satisfying this criterium were found.')
                return flask.redirect(flask.request.referrer)

        results = [{
            'username': e[0],
            'first_name': e[1],
            'last_name': e[2],
            'email': e[3],
            'profile_photo_path': e[4] or '/static/images/anonim.jpg'
        } for e in entries]

        return flask.render_template('search.html', results=results)

    @app.route('/add_group_user', methods=['GET', 'POST'])
    @flask_login.login_required
    def add_group_user():
        if flask.request.method == 'GET':
            group_id = flask.request.args['group_id']
            user_role = flask.request.args['user_role']
            group_name = flask.request.args['group_name']

            with db_connection.cursor() as cursor:
                cursor.execute('SELECT id FROM "user" WHERE username=%s', (flask_login.current_user.id,))
                user_id = cursor.fetchone()[0]

                try:
                    group_id = int(group_id)
                except ValueError:
                    flask.flash('Invalid group id')
                    return flask.redirect(flask.request.referrer)

                cursor.execute(
                    'SELECT f.id, '
                    '       f.first_name, '
                    '       f.last_name, '
                    '       f.profile_photo_path '
                    'FROM "user" u, '
                    '     "user" f, '
                    '     user_friend uf '
                    'WHERE ((u.id = uf.user1_id '
                    '        AND f.id = uf.user2_id) '
                    '       OR (u.id = uf.user2_id '
                    '           AND f.id = uf.user1_id)) '
                    '  AND u.id = %s '
                    '  AND f.id NOT IN '
                    '    (SELECT user_id '
                    '     FROM user_group '
                    '     WHERE group_id = %s) '
                    '  AND f.id NOT IN '
                    '    (SELECT guest_id '
                    '     FROM group_invitation '
                    '     WHERE group_id = %s '
                    '       AND host_id = %s) ',
                    (user_id, group_id, group_id, user_id))
                entries = cursor.fetchall()

                friends = [{
                    'id': e[0],
                    'first_name': e[1],
                    'last_name': e[2],
                    'profile_photo_path': e[3] or '/static/images/anonim.jpg'
                } for e in entries]

            return flask.render_template('add_group_user.html', group_id=group_id, user_role=user_role,
                                         group_name=group_name, friends=friends)
        else:
            group_id = flask.request.form['group_id']
            guest_id = flask.request.form['guest_id']
            group_name = flask.request.form['group_name']
            role = flask.request.form['role']

            try:
                group_id = int(group_id)
            except ValueError:
                flask.flash('Invalid group id')
                return flask.redirect(flask.request.referrer)

            try:
                guest_id = int(guest_id)
            except ValueError:
                flask.flash('Invalid guest id')
                return flask.redirect(flask.request.referrer)

            with db_connection:
                with db_connection.cursor() as cursor:
                    try:
                        cursor.execute('SELECT id FROM "user" WHERE username=%s', (flask_login.current_user.id,))
                        user_id = cursor.fetchone()[0]

                        cursor.execute('INSERT INTO '
                                       '  group_invitation('
                                       '    guest_id, '
                                       '    host_id, '
                                       '    group_id, '
                                       '    role'
                                       ') VALUES(%s, %s, %s, %s)',
                                       (guest_id, user_id, group_id, role))
                    except (psycopg2.DatabaseError, ValueError) as e:
                        flask.flash('Invalid input')
                        return flask.redirect(flask.request.referrer)

            return flask.redirect(f'/groups/{group_name}')

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
        group_id = flask.request.form['group_id']

        if not content:
            flask.flash('Post cannot contain empty body.')
            return flask.redirect(flask.request.referrer)

        with db_connection:
            with db_connection.cursor() as cursor:
                try:
                    cursor.execute('SELECT id FROM "user" WHERE username=%s', (username,))
                except psycopg2.DatabaseError:
                    flask.flash(f'Malformed username: {username}')
                    return flask.redirect(flask.request.referrer)

                id_entry = cursor.fetchone()

                if not id_entry:
                    flask.flash(f'The specified user does not exist')
                    return flask.redirect(flask.request.referrer)

                user_id = id_entry[0]
                try:
                    if group_id:
                        cursor.execute('INSERT INTO group_post (content, group_id, user_id) VALUES (%s, %s, %s)',
                                       (content, int(group_id), user_id))
                    else:
                        cursor.execute('INSERT INTO user_post (user_id, content) VALUES (%s, %s)', (user_id, content))
                except psycopg2.DatabaseError:
                    flask.flash(f'Malformed content in the post: {content}')
                    return flask.redirect(flask.request.referrer)

        return flask.redirect(flask.request.referrer)

    @app.route('/create_comment', methods=['POST'])
    @flask_login.login_required
    def create_comment():
        content = flask.request.form['content']
        post_id = flask.request.form['post_id']
        location = flask.request.form['location'] if 'location' in flask.request.form else ''

        if not content:
            flask.flash('Content of the comment cannot be empty')
            return flask.redirect(flask.request.referrer)

        with db_connection:
            with db_connection.cursor() as cursor:
                cursor.execute('SELECT id FROM "user" WHERE username=%s', (flask_login.current_user.id,))
                id_entry = cursor.fetchone()

                user_id = id_entry[0]

                try:
                    if location == 'group':
                        cursor.execute('INSERT INTO '
                                       '  group_post_comment (post_id, user_id, content) '
                                       'VALUES (%s, %s, %s)',
                                       (post_id, user_id, content))
                    else:
                        cursor.execute('INSERT INTO '
                                       '  user_post_comment (post_id, user_id, content) '
                                       'VALUES (%s, %s, %s)',
                                       (post_id, user_id, content))
                except psycopg2.DatabaseError:
                    flask.flash(f'Malformed input: {content}')

        return flask.redirect(flask.request.referrer)

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

            with db_connection:
                with db_connection.cursor() as cursor:
                    server_path = '/' + local_path
                    cursor.execute('UPDATE "user" SET profile_photo_path=%s WHERE username=%s',
                                   (server_path, flask_login.current_user.id))

        return flask.redirect(f'/users/{flask_login.current_user.id}')

    @app.route('/groups/<group_name>')
    @flask_login.login_required
    def group_page(group_name):
        with db_connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "group" WHERE name=%s', (group_name,))
            entry = cursor.fetchone()
            if not entry:
                flask.abort(404)

            group_id, creator_id, name, date_added = entry

            cursor.execute('SELECT id FROM "user" WHERE username=%s', (flask_login.current_user.id,))
            user_id = cursor.fetchone()[0]

            if flask_login.current_user.id == 'admin':
                user_role = 'ADMIN'
            else:
                cursor.execute('SELECT role FROM user_group WHERE user_id = %s AND group_id = %s', (user_id, group_id))
                entry = cursor.fetchone()
                if not entry:
                    return flask.render_template('unauthorized_group.html')

                user_role = entry[0]

            cursor.execute('SELECT'
                           '  p.id, '
                           '  content, '
                           '  user_id, '
                           '  p.date_added, '
                           '  p.time_added, '
                           '  username, '
                           '  first_name, '
                           '  last_name, '
                           '  profile_photo_path '
                           'FROM '
                           '  group_post p, '
                           '  "user" u '
                           'WHERE '
                           '  group_id=%s '
                           '  AND u.id = p.user_id',
                           (group_id,))
            entries = cursor.fetchall()

            posts = []
            for post_id, post_content, post_user_id, post_date_added, post_time_added, username, user_first_name, \
                user_last_name, user_profile_photo in entries:
                post = {
                    'id': post_id,
                    'content': post_content,
                    'user_id': post_user_id,
                    'user_first_name': user_first_name,
                    'user_last_name': user_last_name,
                    'user_profile_photo': user_profile_photo,
                    'date_added': format_date(post_date_added),
                    'time_added': format_time(post_time_added)
                }

                cursor.execute(
                    'SELECT '
                    '  first_name, '
                    '  last_name, '
                    '  profile_photo_path, '
                    '  content, '
                    '  date_added, '
                    '  time_added '
                    'FROM '
                    '  group_post_comment c, '
                    '  "user" u '
                    'WHERE '
                    '  post_id=%s '
                    '  AND c.user_id = u.id',
                    (post_id,))
                entries = cursor.fetchall()

                comments = []
                for first_name, last_name, profile_photo_path, \
                    comment_content, comment_date_added, comment_time_added in entries:
                    comments.append({
                        'content': comment_content,
                        'date_added': format_date(comment_date_added),
                        'time_added': format_time(comment_time_added),
                        'user': first_name + ' ' + last_name,
                        'user_profile_photo': profile_photo_path or '/static/images/anonim.jpg'
                    })

                post['comments'] = comments

                posts.append(post)

            cursor.execute(
                'SELECT '
                '  username, '
                '  first_name, '
                '  last_name, '
                '  profile_photo_path '
                'FROM '
                '  "user" u, '
                '  user_group ug '
                'WHERE '
                '  u.id = ug.user_id '
                '  AND group_id=%s',
                (group_id,))
            entries = cursor.fetchall()

        members = []
        for username, first_name, last_name, profile_photo_path in entries:
            members.append({
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'profile_photo_path': profile_photo_path or '/static/images/anonim.jpg'
            })

        group = {
            'id': group_id,
            'creator_id': creator_id,
            'name': name,
            'date_added': date_added
        }

        return flask.render_template('group.html', group=group, posts=posts, members=members, user_role=user_role)

    @app.route('/admin')
    @admin_login_required
    def admin_main_page():
        with db_connection.cursor() as cursor:
            cursor.execute(
                'SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != \'pg_catalog\''
                ' AND schemaname != \'information_schema\'')
            entries = cursor.fetchall()

            table_names = [e[0] for e in entries]

        return flask.render_template('admin/index.html', table_names=table_names)

    @app.route('/admin/<table_name>')
    @admin_login_required
    def admin_table_view(table_name):
        with db_connection.cursor() as cursor:
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

        keys = [c[0] for c in column_entries]

        info = {
            'title': table_name.upper(),
            'keys': keys,
            'primary_keys': primary_keys,
            'entries': entries
        }
        try:
            i = keys.index('id')
        except ValueError:
            i = -1

        return flask.render_template('admin/table_template.html', table_name=table_name, info=info,
                                     new_id=max(map(lambda el: el[i], entries)) + 1 if entries and i != -1 else None)

    @app.route('/delete/<table_name>', methods=['POST'])
    def delete(table_name):
        with db_connection:
            with db_connection.cursor() as cursor:
                cursor.execute(f'SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)',
                               (table_name,))
                entry = cursor.fetchone()
                if not entry:
                    flask.abort(404)

                cursor.execute(
                    'SELECT a.attname FROM  pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = '
                    'ANY('
                    'i.indkey) WHERE  i.indrelid =%s::regclass AND i.indisprimary;', (table_name,))
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
                    for key, value in flask.request.form.items():
                        query += f'{" AND " if added != 0 else ""}{key}={value}'
                        added += 1

                try:
                    cursor.execute(query)
                except Exception as e:
                    print(e)
                    flask.flash(str(e))

        return flask.redirect(flask.request.referrer)

    @app.route('/update/<table_name>', methods=['POST'])
    def update(table_name):
        with db_connection:
            with db_connection.cursor() as cursor:
                cursor.execute(f'SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)',
                               (table_name,))
                entry = cursor.fetchone()
                if not entry:
                    flask.abort(404)

                cursor.execute('SELECT column_name, data_type FROM information_schema.COLUMNS WHERE table_name=%s',
                               (table_name,))
                column_entries = cursor.fetchall()
                data_types = {c[0]: c[1] for c in column_entries}

                cursor.execute(
                    'SELECT a.attname FROM  pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = '
                    'ANY('
                    'i.indkey) WHERE  i.indrelid =%s::regclass AND i.indisprimary;', (table_name,))
                primary_keys_entries = cursor.fetchall()
                primary_keys = [p[0] for p in primary_keys_entries]

                form_data = dict(flask.request.form)
                query = f'UPDATE "{table_name}" SET '

                args = []

                added = 0
                keys_to_remove = []
                for key in form_data:
                    if key.startswith('__'):
                        query += f'{", " if added != 0 else ""}{key[2:]}=%s'
                        added += 1
                        keys_to_remove.append(key)

                        data = form_data[key]
                        data_type = data_types[key[2:]]
                        data = transform_data(data, data_type)

                        args.append(data)

                if not keys_to_remove:
                    flask.abort(400)

                for key in keys_to_remove:
                    del form_data[key]

                query += ' WHERE '
                if primary_keys:
                    added = 0
                    for primary_key in primary_keys:
                        if primary_key in form_data:
                            query += f'{" AND " if added != 0 else ""}{primary_key}=%s'
                            added += 1

                            data = form_data[primary_key]
                            data_type = data_types[primary_key]
                            data = transform_data(data, data_type)

                            args.append(data)
                    if added == 0:
                        flask.abort(400)
                else:
                    added = 0
                    for key, value in flask.request.form.values():
                        query += f'{" AND " if added != 0 else ""}{key}=%s'
                        added += 1

                        data = value
                        data_type = data_types[key]
                        data = transform_data(data, data_type)

                        args.append(data)

                try:
                    cursor.execute(query, tuple(args))
                except Exception as e:
                    print(e)
                    flask.flash(str(e))
                    flask.abort(400)

        return flask.redirect(flask.request.referrer)

    @app.route('/insert/<table_name>', methods=['POST'])
    def insert(table_name):
        with db_connection as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)', (table_name,))
            entry = cursor.fetchone()
            if not entry:
                flask.abort(404)

            cursor.execute('SELECT column_name, data_type FROM information_schema.COLUMNS WHERE table_name=%s',
                           (table_name,))
            column_entries = cursor.fetchall()
            data_types = {c[0]: c[1] for c in column_entries}

            form_data = dict(flask.request.form)
            query = f'INSERT INTO "{table_name}"('

            args = []

            added = 0
            for key, value in form_data.items():
                query += f'{", " if added != 0 else ""}{key}'
                added += 1

                data = value
                data_type = data_types[key]
                data = transform_data(data, data_type)

                args.append(data)

            query += ') VALUES(' + '%s, ' * (added - 1) + '%s)'

            try:
                cursor.execute(query, tuple(args))
            except psycopg2.DatabaseError as e:
                flask.flash(f'Failed to insert new element in database: {e}')
                return flask.redirect(flask.request.referrer)

            conn.commit()

        return flask.redirect(flask.request.referrer)

    return app


def main():
    db_connection = psycopg2.connect(host='localhost', database='bdp', user='postgres', password='p@ssw0rd')
    create_tables(db_connection)

    app = create_app(db_connection)

    login_manager = flask_login.LoginManager()

    @login_manager.user_loader
    def load_user(user_id):
        with db_connection.cursor() as cursor:
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
