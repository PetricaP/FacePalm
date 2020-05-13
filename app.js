const express = require('express');
const expressLayouts = require('express-ejs-layouts');
const bodyParser = require('body-parser');
const session = require('express-session');

const crypto = require('crypto');
const {Client} = require('pg');

const app = express();


app.use(session({
    secret: 'OnceUponATime',
    cookie: {maxAge: 60000},
    resave: false,
    saveUninitialized: true
}))

app.set('view engine', 'ejs');
app.use(expressLayouts);
app.use(express.static('static'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: true}));


const connParams = {
    user: 'postgres',
    host: 'localhost',
    database: 'pwp',
    password: 'p@ssw0rd',
};


const port = 9090


app.post('/login', async (req, res) => {
    const username = req.body.username;
    const password = req.body.password;

    const client = new Client(connParams);

    const password_hash =
        crypto.createHash('sha256').update(password).digest('hex');

    console.log(`${username} ${password} ${password_hash}`);

    await client.connect();

    const result = await client.query(
        'SELECT username, password_hash FROM "user" WHERE username=$1::text',
        [username]);

    await client.end();

    if (result.rowCount == 0) {
        console.log(`User ${username} not found in DB`);
    } else {
        console.log(`User ${username} found in DB`);
        if (password_hash == result.rows[0].password_hash) {
            req.session.user = username;
            res.redirect(`/users/${username}`);
        } else {
            res.redirect('/login.html');
        }
    }
});


function formatDate(date) {
    return `${date.getDay()}.${date.getMonth()}.${date.getFullYear()}`
}


function formatTime(time) {
    let parts = time.split(':');

    return `${parts[0]}:${parts[1]}:${parts[2].substr(0, 2)}`
}


async function getUserGroups(client, current_id) {
    const result = await client.query(
        `SELECT 
          g.id, 
          g.name 
        FROM 
          "group" g, 
          "user" u, 
          "user_group" ug 
        WHERE 
          g.id = ug.group_id 
          AND ug.user_id = u.id 
          AND u.id = $1`,
        [current_id]);

    return result.rows;
}


async function getUserFriendRequests(client, current_id) {
    const result = await client.query(
        `SELECT 
          first_name, 
          last_name, 
          profile_photo_path, 
          id, 
          username 
        FROM
          user_friend_request ,
          "user" 
        WHERE 
        friend_id=$1 
        AND user_id=id`,
        [current_id]
    )

    for (let friend of result.rows) {
        if (!friend.profile_photo_path) {
            friend.profile_photo_path = '/static/images/anonim.jpg';
        }
    }

    return result.rows
}


async function getUserGroups(client, current_id) {
    const result = await client.query(
        `SELECT 
          g.id, 
          g.name 
        FROM 
          "group" g, 
          "user" u, 
          "user_group" ug 
        WHERE 
          g.id = ug.group_id 
          AND ug.user_id = u.id 
          AND u.id = $1`,
        [current_id]
    )

    return result.rows
}


async function getUserFriends(client, current_id) {
    const result = await client.query(
        `SELECT 
          f.id, 
          f.username, 
          f.first_name, 
          f.last_name, 
          f.profile_photo_path 
        FROM 
          "user" u, 
          "user" f, 
          user_friend uf 
        WHERE 
          ((u.id = uf.user1_id 
            AND f.id = uf.user2_id) 
           OR 
           (u.id = uf.user2_id 
           AND f.id = uf.user1_id)) 
          AND u.id = $1`,
        [current_id]
    )

    for (let friend of result.rows) {
        if (!friend.profile_photo_path) {
            friend.profile_photo_path = '/static/images/anonim.jpg';
        }
    }

    console.log('Friends:');
    console.log(result.rows);

    return result.rows
}


async function getUserGroupInvitations(client, current_id) {
    const result = await client.query(
        `SELECT 
          i.host_id, 
          i.group_id, 
          g.name, 
          u.username, 
          u.first_name, 
          u.last_name, 
          u.profile_photo_path 
        FROM 
          "group" g, 
          group_invitation i, 
          "user" u 
        WHERE 
          g.id = i.group_id 
          AND i.host_id=u.id
          AND i.guest_id=$1`,
        [current_id]
    )

    return result.rows
}



app.get('/users/:username', async (req, res) => {
    logged_username = req.session.user
    if (!logged_username) {
        res.redirect('/login.html');
        return;
    }

    const username = req.params.username

    const client = new Client(connParams);

    await client.connect();

    const result = await client.query(
        `SELECT id, first_name, last_name, birth_date, profile_photo_path FROM "user" 
        WHERE username=$1::text`, [username]);

    const user_data = result.rows[0];

    console.log(user_data);
    const desc_result = await client.query(
        'SELECT content FROM user_description WHERE user_id=$1',
        [req.params.id]);

    description = ''
    if (desc_result.rowCount != 0) {
        description = desc_result.rows[0].content;
    }

    const logged_res = await client.query(
        'SELECT id FROM "user" WHERE username=$1::text', [logged_username]);

    console.log(logged_username);
    const logged_id = logged_res.rows[0].id;

    if (!user_data.profile_photo_path) {
        user_data.profile_photo_path = '/static/images/anonim.jpg';
    }

    const friendRequests = await getUserFriendRequests(client, logged_id);

    const groups = await getUserGroups(client, logged_id);

    const friends = await getUserFriends(client, logged_id);

    const groupInvitations = await getUserGroupInvitations(client, logged_id);

    console.log(groups);

    const formattedDate = formatDate(user_data.birth_date);

    let is_friend = undefined;
    if (logged_username != user_data.username) {
        let res = await client.query(
            'SELECT * FROM user_friend WHERE (user1_id=$1 AND user2_id=$2) OR (user1_id=$2 AND user2_id=$1)',
            [user_data.id, logged_id]);
        if (res.rowCount != 0) {
            is_friend = 1;
        } else {
            res = await client.query('SELECT * FROM user_friend_request WHERE friend_id=$1 AND user_id=$2',
                           [user_data.id, logged_id])
            if (res.rowCount != 0) {
                is_friend = 2;
            } else {
                res = await client.query('SELECT * FROM user_friend_request WHERE friend_id=$1 AND user_id=$2',
                               [logged_id, user_data.id])
                if (res.rowCount != 0) {
                    is_friend = 3;
                } else {
                    is_friend = 0;
                }
            }
        }
    }

    const posts_res = await client.query('SELECT id, content, date_added, time_added FROM user_post WHERE user_id=$1', [user_data.id])

    posts = []
    for (let entry of posts_res.rows) {
        const comment_res = await client.query(
            `SELECT 
              user_id, 
              content, 
              date_added, 
              time_added 
            FROM 
              user_post_comment 
            WHERE 
              post_id=$1 
            ORDER BY 
              date_added ASC,
              time_added ASC`,
            [entry.id])

        comments = []
        for (comment_row of comment_res.rows) {
            const user_res = await client.query('SELECT username, first_name, last_name, profile_photo_path FROM "user" WHERE id=$1',
                           [comment_row.user_id]);

            const comm_user = user_res.rows[0];

            formatted_comment_date = formatDate(comment_row.date_added);
            formatted_comment_time = formatTime(comment_row.time_added);

            comments.push({
                content: comment_row.content,
                date_added: formatted_comment_date,
                time_added: formatted_comment_time,
                username: comm_user.username,
                user: `${comm_user.first_name} ${comm_user.last_name}`,
                user_profile_photo: (comm_user.profile_photo) ? comm_user.profile_photo
                                                              : '/static/images/anonim.jpg'
            });

            formatted_post_date = formatDate(entry.date_added);
            formatted_post_time = formatTime(entry.time_added);

            posts.push({
                id: entry.id,
                content: entry.content,
                date_added: formatted_post_date,
                time_added: formatted_post_time,
                comments: comments
            });
        }
    }

    console.log(posts);

    await client.end();

    console.log(is_friend);
    console.log(user_data);

    res.render('user_profile', {
        logged_username: logged_username,
        user_id: user_data.id,
        username: username,
        first_name: user_data.first_name,
        last_name: user_data.last_name,
        profile_photo_path: user_data.profile_photo_path,
        birth_date: formattedDate,
        description: description,
        posts: posts,
        friend_requests: friendRequests,
        my_groups: groups,
        my_friends: friends,
        is_friend: is_friend,
        group_invitations: groupInvitations
    });
});


app.post('/add_friend', async (req, res) => {
    const logged_username = req.session.user
    if (!logged_username) {
        res.redirect('/login.html');
        return;
    }

    const username = req.body.username;

    const client = new Client(connParams);

    await client.connect();

    const res1 = await client.query('SELECT id FROM "user" WHERE username=$1', [logged_username]);
    const logged_id = res1.rows[0].id;

    console.log(username);
    const res2 = await client.query('SELECT id FROM "user" WHERE username=$1', [username]);

    const user_id = res2.rows[0].id;

    const friend_res = await client.query(`SELECT * FROM user_friend WHERE 
                                          (user1_id=$1 AND user2_id=$2) OR 
                                          (user1_id=$2 AND user2_id=$1)`,
                                          [user_id, logged_id]);
    if (!friend_res.rowCount != 0) {
        await client.end();
        res.redirect(`/users/${logged_username}`);
        return;
    }

    const request_res = await client.query(`SELECT * FROM user_friend_request WHERE
                                            (user_id=$1 AND friend_id=$2) OR
                                            (user_id=$2 AND friend_id=$1)`,
                                            [user_id, logged_id]);
    if (request_re.rowCount != 0) {
        await client.end();
        res.redirect(`/users/${logged_username}`);
        return;
    }

    await client.query('INSERT INTO user_friend_request VALUES($1, $2)', [user_id, logged_id])

    await client.end();

    res.redirect(`/users/${username}`);
});


app.post('/resolve_friend_request', async (req, res) => {
    logged_username = req.session.user;
    user_id = parseInt(req.body.user_id);

    const client = new Client(connParams);

    await client.connect();

    let id_res = await client.query('SELECT id FROM "user" WHERE username=$1',
                                    [logged_username]);
    const logged_id = id_res.rows[0].id;

    await client.query('DELETE FROM user_friend_request WHERE friend_id=$1 AND user_id=$2',
                       [logged_id, user_id])

    if (req.body.accept) {
        await client.query('INSERT INTO user_friend VALUES($1, $2)', [logged_id, user_id]);
    }

    await client.end();

    res.redirect(`/users/${logged_username}`);
});


app.post('/resolve_group_invitation', async (req, res) => {
    const logged_username = req.session.user
    if (!logged_username) {
        res.redirect('/login.html');
        return;
    }

    const host_id = parseInt(req.body.host_id);
    const group_id = parseInt(req.body.group_id);

    const client = new Client(connParams);

    await client.connect();

    let id_res = await client.query('SELECT id FROM "user" WHERE username=$1',
                                    [logged_username]);
    const guest_id = id_res.rows[0].id;

    const role_res = await client.query(`SELECT role FROM group_invitation WHERE 
                                         host_id=$1 AND guest_id=$2 AND group_id=$3`,
                                        [host_id, guest_id, group_id]);
    if (role_res.rowCount == 0) {
        await client.end();
        res.redirect(`/users/${logged_username}`);
        return;
    }

    const role = role_res.rows[0].role;

    await client.query(`DELETE FROM group_invitation WHERE 
                        host_id=$1 AND guest_id=$2 AND group_id=$3`,
                       [host_id, guest_id, group_id]);

    if (req.body.accept) {
        await client.query('INSERT INTO user_group VALUES($1, $2, $3)',
                           [guest_id, group_id, role]);
    }

    await client.end();

    res.redirect(`/users/${logged_username}`);
});


app.post('/remove_user_friend', async (req, res) => {
    const logged_username = req.session.user;
    if (!logged_username) {
        res.redirect('/login.html');
        return;
    }

    friend_id = parseInt(req.body.friend_id);

    const client = new Client(connParams);

    await client.connect();

    const id_res = await client.query('SELECT id FROM "user" WHERE username=$1',
                                      [logged_username]);
    const logged_id = id_res.rows[0].id;

    await client.query(`DELETE FROM "user_friend" WHERE 
                        (user1_id=$1 AND user2_id=$2) OR 
                        (user1_id=$2 AND user2_id=$1)`,
                       [logged_id, friend_id]);

    return res.redirect(`/users/${logged_username}`);
});


app.listen(
    port, '0.0.0.0',
    () => console.log(`Server running on http://0.0.0.0:${port}`));

