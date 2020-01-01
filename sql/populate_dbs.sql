TRUNCATE TABLE user_friend RESTART IDENTITY CASCADE;
TRUNCATE TABLE user_post_comment RESTART IDENTITY CASCADE;
TRUNCATE TABLE user_post RESTART IDENTITY CASCADE;
TRUNCATE TABLE "user" RESTART IDENTITY CASCADE;

INSERT INTO "user"(username, password_hash, email, last_name, first_name, birth_date) VALUES (
    'admin',
    '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
    'admin@admin.com',
    'admin',
    'admin',
    DATE(CURRENT_DATE)
);

INSERT INTO "user"(username, password_hash, email, last_name, first_name, birth_date, profile_photo_path) VALUES (
    'sava.valeria',
    'aa0dcafe4109e988919cd527a080558ce611d781952ffd5049fa3ca6439b56d9',
    'sava.valeria@gmail.com',
    'Sava',
    'Valeria',
    DATE('1983-07-17'),
    '/static/images/girl1.jpg'
);
INSERT INTO "user"(username, password_hash, email, last_name, first_name, birth_date, profile_photo_path) VALUES (
    'oleg.barna',
    '685dc42816021874d549879124b023c4b8bfd4c9952ee45612349f9f810eade5',
    'oleg.barna@gmail.com',
    'Barna',
    'Oleg',
    DATE('1985-02-03'),
    '/static/images/dodon.jpg'
);
INSERT INTO "user"(username, password_hash, email, last_name, first_name, birth_date) VALUES (
    'secrieru.mircea',
    '82598c4e98460783d84acb865ae33da8724c6c11f1d7b8764239e3ab6fb57be1',
    'secrieru.mircea@mail.ru',
    'Secrieru',
    'Mircea',
    DATE('1987-05-11')
);
INSERT INTO "user"(username, password_hash, email, last_name, first_name, birth_date, profile_photo_path) VALUES (
    'antoci.mihaela',
    '25bd4c93b0916f3672cd3971860d2ce15e76191f61d9c8a05a35bc776481e08c',
    'antoci.mihaela@yahoo.com',
    'Antoci',
    'Mihaela',
    DATE('2000-11-13'),
    '/static/images/girl2.jpg'
);
INSERT INTO "user"(username, password_hash, email, last_name, first_name, birth_date, profile_photo_path) VALUES (
    'bivol.eudochia',
    '8ea5b8f92665eda157ea387f849b400ab2c179c7ff3601e4f48f36ebc944abaf',
    'bivol.eudochia@hotmail.com',
    'Bivol',
    'Eudochia',
    DATE('1954-02-01'),
    '/static/images/girl4.jpg'
);

INSERT INTO user_friend VALUES (3, 2);
INSERT INTO user_friend VALUES (3, 6);
INSERT INTO user_friend VALUES (3, 4);
INSERT INTO user_friend VALUES (3, 6);
INSERT INTO user_friend VALUES (6, 4);
INSERT INTO user_friend VALUES (2, 4);

INSERT INTO user_post (content, user_id) VALUES ('Bine ati venit pe paagina mea oficiala de facebuci', 3);
INSERT INTO user_post (content, user_id) VALUES ('Abia astept sa ninga afara, sa facem un om de zapada', 6);
INSERT INTO user_post (content, user_id) VALUES ('Lucrurile bune se intampla cand te astepti mai putin', 6);
INSERT INTO user_post (content, user_id) VALUES ('Daruiesc 2 pisici, vaccinati si steriliati', 2);
INSERT INTO user_post (content, user_id) VALUES ('Cunoaste cineva cum ajung de la telecentru la botanica?', 5);

INSERT INTO user_post_comment (post_id, user_id, content) VALUES (3, 5, 'Deep');
INSERT INTO user_post_comment (post_id, user_id, content)VALUES (5, 4, 'Troleibus 17');
INSERT INTO user_post_comment (post_id, user_id, content)VALUES (4, 5, 'Astept poze in privat');
INSERT INTO user_post_comment (post_id, user_id, content)VALUES (4, 4, 'Vreau si eu unul daca mai sunt disponibii');
INSERT INTO user_post_comment (post_id, user_id, content)VALUES (2, 5, 'Putem face unul din noroi daca nu mai ai rabdare');
