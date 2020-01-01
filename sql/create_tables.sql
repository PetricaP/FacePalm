CREATE TABLE IF NOT EXISTS "user"(
    id SERIAL,
    username VARCHAR(30) NOT NULL,
    password_hash CHAR(64) NOT NULL,
    email VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    profile_photo_path VARCHAR(150),
    last_online DATE,
    birth_date DATE NOT NULL,
    date_joined DATE NOT NULL DEFAULT(CURRENT_DATE),
    PRIMARY KEY(id),
    UNIQUE (username)
);

CREATE TABLE IF NOT EXISTS user_friend(
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    FOREIGN KEY(user1_id) REFERENCES "user"(id),
    FOREIGN KEY(user2_id) REFERENCES "user"(id),
    CHECK (user1_id != user2_id)
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
    creator INTEGER NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    PRIMARY KEY(id),
    FOREIGN KEY(creator) REFERENCES "user"(id)
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
    time_added TIME NOT NULL DEFAULT(LOCALTIME)
);

CREATE TABLE IF NOT EXISTS group_post(
    id SERIAL,
    content VARCHAR(500) NOT NULL,
    group_id INTEGER NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    time_added TIME NOT NULL DEFAULT(LOCALTIME),
    PRIMARY KEY(id),
    FOREIGN KEY(group_id) REFERENCES "group"(id)
);

CREATE TABLE IF NOT EXISTS group_request(
    id SERIAL,
    group_id INTEGER NOT NULL,
    date_added DATE NOT NULL DEFAULT(CURRENT_DATE),
    time_added TIME NOT NULL DEFAULT(LOCALTIME),
    FOREIGN KEY(group_id) REFERENCES "group"(id)
);