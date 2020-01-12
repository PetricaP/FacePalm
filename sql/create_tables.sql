CREATE TABLE IF NOT EXISTS "user"(
    id SERIAL,
    username VARCHAR(30) NOT NULL,
    password_hash CHAR(64) NOT NULL,
    email VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    profile_photo_path VARCHAR(150),
    birth_date DATE NOT NULL,
    date_joined DATE NOT NULL DEFAULT(CURRENT_DATE),
    PRIMARY KEY(id),
    UNIQUE (username),
    UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS user_description(
    user_id INTEGER NOT NULL,
    content VARCHAR(100),
    UNIQUE(user_id),
    FOREIGN KEY(user_id) REFERENCES "user"(id)
);

CREATE TABLE IF NOT EXISTS user_friend(
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    PRIMARY KEY(user1_id, user2_id),
    FOREIGN KEY(user1_id) REFERENCES "user"(id),
    FOREIGN KEY(user2_id) REFERENCES "user"(id),
    CHECK (user1_id != user2_id)
);

CREATE TABLE IF NOT EXISTS user_friend_request(
    friend_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    PRIMARY KEY(friend_id, user_id),
    FOREIGN KEY(friend_id) REFERENCES "user"(id),
    FOREIGN KEY(user_id) REFERENCES "user"(id),
    CHECK (friend_id != user_id)
);

CREATE TABLE IF NOT EXISTS user_post(
    id SERIAL,
    content VARCHAR(500) NOT NULL,
    user_id INTEGER NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    time_added TIME NOT NULL DEFAULT(LOCALTIME),
    PRIMARY KEY(id),
    FOREIGN KEY(user_id) REFERENCES "user"(id)
);

CREATE TABLE IF NOT EXISTS user_post_comment(
    id SERIAL,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content VARCHAR(500) NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    time_added TIME NOT NULL DEFAULT(LOCALTIME),
    PRIMARY KEY(id),
    FOREIGN KEY(user_id) REFERENCES "user"(id),
    FOREIGN KEY(post_id) REFERENCES user_post(id)
);

CREATE TABLE IF NOT EXISTS "group"(
    id SERIAL,
    creator_id INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    PRIMARY KEY(id),
    FOREIGN KEY(creator_id) REFERENCES "user"(id),
    UNIQUE(name)
);

DO $$
BEGIN
    IF (SELECT 1 FROM pg_type WHERE typname = 'role') IS null THEN
        CREATE TYPE role AS ENUM ('ADMIN', 'READER', 'WRITER');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS user_group(
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    role ROLE NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    time_added TIME NOT NULL DEFAULT(LOCALTIME),
    PRIMARY KEY(user_id, group_id),
    FOREIGN KEY(user_id) REFERENCES "user"(id),
    FOREIGN KEY(group_id) REFERENCES "group"(id)
);

CREATE TABLE IF NOT EXISTS group_post(
    id SERIAL,
    content VARCHAR(500) NOT NULL,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    time_added TIME NOT NULL DEFAULT(LOCALTIME),
    PRIMARY KEY(id),
    FOREIGN KEY(group_id) REFERENCES "group"(id),
    FOREIGN KEY(user_id) REFERENCES "user"(id)
);

CREATE TABLE IF NOT EXISTS group_post_comment(
    id SERIAL,
    content VARCHAR(500) NOT NULL,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    time_added TIME NOT NULL DEFAULT(LOCALTIME),
    PRIMARY KEY(id),
    FOREIGN KEY(post_id) REFERENCES group_post(id),
    FOREIGN KEY(user_id) REFERENCES "user"(id)
);

CREATE TABLE IF NOT EXISTS group_invitation(
    guest_id INTEGER NOT NULL,
    host_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    role ROLE NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    time_added TIME NOT NULL DEFAULT(LOCALTIME),
    FOREIGN KEY(guest_id) REFERENCES "user"(id),
    FOREIGN KEY(host_id) REFERENCES "user"(id),
    FOREIGN KEY(group_id) REFERENCES "group"(id),
    UNIQUE(host_id, guest_id, group_id),
    CHECK (host_id != guest_id)
);