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


const port = 9090;


app.post('/login', async (req, res) => {
    const username = req.body.username;
    const password = req.body.password;

    const client = new Client(connParams);

    const password_hash =
        crypto.createHash('sha256').update(password).digest('hex');

    await client.connect();

    const result = await client.query(
        'SELECT username, password_hash FROM "user" WHERE username=$1::text',
        [username]);

    await client.end();

    if (result.rowCount != 0) {
        if (password_hash == result.rows[0].password_hash) {
            req.session.user = username;
            res.redirect(`/users/${username}`);
        } else {
            res.redirect('/login.html');
        }
    } else {
        res.redirect('/login.html');
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

    const desc_result = await client.query(
        'SELECT content FROM user_description WHERE user_id=$1', [user_data.id]);

    description = ''
    if (desc_result.rowCount != 0) {
        description = desc_result.rows[0].content;
    }

    const logged_res = await client.query(
        'SELECT id FROM "user" WHERE username=$1::text', [logged_username]);

    const logged_id = logged_res.rows[0].id;

    if (!user_data.profile_photo_path) {
        user_data.profile_photo_path = '/static/images/anonim.jpg';
    }

    const friendRequests = await getUserFriendRequests(client, logged_id);

    const groups = await getUserGroups(client, logged_id);

    const friends = await getUserFriends(client, logged_id);

    const groupInvitations = await getUserGroupInvitations(client, logged_id);

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

    let posts = []
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

        let comments = []
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
                user_profile_photo: comm_user.profile_photo_path || '/static/images/anonim.jpg'
            });
        }

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

    await client.end();

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

    const res2 = await client.query('SELECT id FROM "user" WHERE username=$1', [username]);

    const user_id = res2.rows[0].id;

    const friend_res = await client.query(`SELECT * FROM user_friend WHERE 
                                          (user1_id=$1 AND user2_id=$2) OR 
                                          (user1_id=$2 AND user2_id=$1)`,
                                          [user_id, logged_id]);
    if (friend_res.rowCount != 0) {
        await client.end();
        res.redirect(`/users/${logged_username}`);
        return;
    }

    const request_res = await client.query(`SELECT * FROM user_friend_request WHERE
                                            (user_id=$1 AND friend_id=$2) OR
                                            (user_id=$2 AND friend_id=$1)`,
                                            [user_id, logged_id]);
    if (request_res.rowCount != 0) {
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


app.post('/create_comment', async (req, res) => {
    if (!req.session.user) {
        res.redirect('/login.html');
        return;
    }

    let content = req.body.content;
    const post_id = req.body.post_id;
    const loc = req.body.location || '';

    const backURL = req.header('Referer') || '/';

    if (!content) {
        res.redirect(backURL);

        return;
    }

    content = content.trim();

    const client = new Client(connParams);

    await client.connect();

    const id_res = await client.query('SELECT id FROM "user" WHERE username=$1',
                                      [req.session.user]);
    const user_id = id_res.rows[0].id;

    if (loc == 'group') {
        await client.query(`INSERT INTO 
                              group_post_comment (post_id, user_id, content) 
                            VALUES ($1, $2, $3)`,
                           [post_id, user_id, content]);
    } else {
        await client.query(`INSERT INTO 
                              user_post_comment (post_id, user_id, content) 
                            VALUES ($1, $2, $3)`,
                           [post_id, user_id, content]);
    }

    await client.end();

    res.redirect(backURL);
});


app.get('/search', async (req, res) => {
    if (!req.session.user) {
        res.redirect('/login.html');
        return;
    }

    const value = req.query.query;
    const attribute = req.query.attribute;

    const backURL = req.header('Referer') || '/';
    if (!['username', 'first_name', 'last_name', 'email'].includes(attribute)) {
        res.redirect(backURL);
        return;
    }

    let client = new Client(connParams);

    await client.connect();

    const entries = await client.query(
        `SELECT 
          username, 
          first_name, 
          last_name, 
          email, 
          profile_photo_path 
        FROM 
          "user" 
        WHERE 
        LOWER(${attribute}) LIKE $1`,
        ['%' + value.toLowerCase() + '%']);

    if (entries.rowCount == 0) {
        res.redirect(backURL);
        return;
    }

    for (let result of entries.rows) {
        if (!result.profile_photo_path) {
            result.profile_photo_path = '/statis/images/anonim.jpg';
        }
    }

    res.render('search', {logged_username: req.session.user, results: entries.rows});
});


app.get('/groups/:group_name', async (req, res) => {
    const logged_username = req.session.user;
    if (!logged_username) {
        res.redirect('/login.html');
        return;
    }

    const group_name = req.params.group_name;

    let client = new Client(connParams);

    await client.connect();

    let result = await client.query('SELECT * FROM "group" WHERE name=$1', [group_name]);
    if (result.rowCount == 0) {
        res.redirect(`/users/${req.session.user}`);
        return;
    }

    const group = result.rows[0];

    result = await client.query('SELECT id FROM "user" WHERE username=$1', [logged_username]);
    const user_id = result.rows[0].id;

    let user_role = 'ADMIN';
    if (logged_username != 'admin') {
        result = await client.query('SELECT role FROM user_group WHERE user_id = $1 AND group_id = $2',
                                    [user_id, group.id]);
        if (result.rowCount == 0) {
            res.redirect(`/users/${logged_username}`);
            return;
        }

        user_role = result.rows[0].role
    }

    result = await client.query(
      `SELECT 
         p.id, 
         content, 
         user_id, 
         p.date_added, 
         p.time_added, 
         username, 
         first_name, 
         last_name, 
         profile_photo_path 
       FROM 
         group_post p, 
         "user" u 
       WHERE 
         group_id=$1 
         AND u.id = p.user_id`,
       [group.id]);

    let posts = [];
    for (const entry of result.rows) {
        const post = {
            id: entry.id,
            content: entry.content,
            user_id: entry.user_id,
            user_first_name: entry.first_name,
            user_last_name: entry.last_name,
            user_profile_photo: entry.profile_photo_path || '/static/images/anonim.jpg',
            date_added: formatDate(entry.date_added),
            time_added: formatTime(entry.time_added)
        };

        const res = await client.query(
            `SELECT 
              first_name, 
              last_name, 
              profile_photo_path, 
              content, 
              date_added, 
              time_added 
            FROM 
              group_post_comment c, 
              "user" u 
            WHERE 
              post_id=$1 
              AND c.user_id = u.id`,
            [entry.id]);

        let comments = [];
        for (const comment of res.rows) {
            comments.push({
                'content': comment.content,
                'date_added': formatDate(comment.date_added),
                'time_added': formatTime(comment.time_added),
                'user': comment.first_name + ' ' + comment.last_name,
                'user_profile_photo': comment.profile_photo_path || '/static/images/anonim.jpg'
            });
        }

        post.comments = comments;

        posts.push(post);
    }

    result = await client.query(
        `SELECT 
          username, 
          first_name, 
          last_name, 
          profile_photo_path, 
          role 
        FROM 
          "user" u, 
          user_group ug 
        WHERE 
          u.id = ug.user_id 
          AND group_id=$1`,
        [group.id]);

    let members = [];
    for (const member of result.rows) {
        members.push({
            username: member.username,
            first_name: member.first_name,
            last_name: member.last_name,
            profile_photo_path: member.profile_photo_path || '/static/images/anonim.jpg',
            role: member.role
        });
    }

    await client.end();

    group.date_added = formatDate(group.date_added);

    res.render('group', {
        logged_username: logged_username,
        group: group,
        posts: posts,
        members: members,
        user_role: user_role
    });
});


app.post('/remove_group_user', async (req, res) => {
    const username = req.body.username;
    const group_id = parseInt(req.body.group_id);

    let client = new Client(connParams);

    await client.connect();

    const backURL = req.header('Referer') || '/';

    let result = await client.query('SELECT id FROM "user" WHERE username=$1', [username]);
    if (result.rowCount == 0) {
        res.redirect(backURL);
        return;
    }

    const user_id = result.rows[0].id;

    await client.query('DELETE FROM "user_group" WHERE user_id=$1 AND group_id=$2', [user_id, group_id]);

    await client.end();

    res.redirect(backURL);
});


app.get('/logout', (req, res) => {
    delete req.session.user;

    res.redirect('/');
});


app.get('/add_group_user', async (req, res) => {
    const logged_username = req.session.user;
    if (!logged_username) {
        res.redirect('/login.html');
        return;
    }

    const group_id = parseInt(req.query.group_id);
    const user_role = req.query.user_role;
    const group_name = req.query.group_name;

    let client = new Client(connParams);

    await client.connect();

    let result = await client.query('SELECT id FROM "user" WHERE username=$1', [logged_username]);
    const user_id = result.rows[0].id;

    result = await client.query(
        `SELECT f.id, 
               f.first_name, 
               f.last_name, 
               f.profile_photo_path 
        FROM "user" u, 
             "user" f, 
             user_friend uf 
        WHERE ((u.id = uf.user1_id 
                AND f.id = uf.user2_id) 
               OR (u.id = uf.user2_id 
                   AND f.id = uf.user1_id)) 
          AND u.id = $1 
          AND f.id NOT IN 
            (SELECT user_id 
             FROM user_group 
             WHERE group_id = $2) 
          AND f.id NOT IN 
            (SELECT guest_id 
             FROM group_invitation 
             WHERE group_id = $2 
               AND host_id = $1)`,
        [user_id, group_id]);

    for (let entry of result.rows) {
        if (!entry.profile_photo_path) {
            entry.profile_photo_path = '/static/images/anonim.jpg';
        }
    }

    await client.end();

    res.render('add_group_user', {
        group_id: group_id,
        user_role: user_role,
        group_name: group_name,
        friends: result.rows
    });
});


app.post('/add_group_user', async (req, res) => {
    const logged_username = req.session.user;
    if (!logged_username) {
        res.redirect('/login.html');
        return;
    }

    const group_id = parseInt(req.body.group_id);
    const guest_id = parseInt(req.body.guest_id);
    const group_name = req.body.group_name;
    const role = req.body.role;

    let client = new Client(connParams);

    await client.connect();

    let result = await client.query('SELECT id FROM "user" WHERE username=$1', [logged_username]);
    user_id = result.rows[0].id;

    await client.query(`INSERT INTO 
                          group_invitation(
                            guest_id, 
                            host_id, 
                            group_id, 
                            role
                         ) VALUES($1, $2, $3, $4)`,
                       [guest_id, user_id, group_id, role]);

    await client.end();

    res.redirect(`/groups/${group_name}`);
});


app.post('/update_user', async (req, res) => {
    if (req.body.new_profile_photo) {
        // TODO: Not supported yet, unfortunately this is a bit difficult to do in node
    }

    const backURL = req.header('Referer') || '/';
    if (req.body.description) {
        const description = req.body.description;

        if (description.length > 100) {
            res.redirect(backURL);
            return;
        }

        let client = new Client(connParams);

        await client.connect();

        let result = await client.query('SELECT id FROM "user" WHERE username=$1', [req.session.user]);
        user_id = result.rows[0].id;

        result = await client.query('SELECT * FROM user_description WHERE user_id=$1', [user_id]);

        if (result.rowCount > 0) {
            await client.query('UPDATE user_description SET content=$1 WHERE user_id=$2',
                               [description, user_id]);
        } else {
            await client.query('INSERT INTO user_description VALUES($1, $2)', [user_id, description]);
        }

        await client.end();
    }

    res.redirect(backURL);
});



app.listen(
    port, '0.0.0.0',
    () => console.log(`Server running on http://0.0.0.0:${port}`));

