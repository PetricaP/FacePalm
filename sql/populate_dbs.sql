TRUNCATE TABLE group_post_comment RESTART IDENTITY CASCADE;
TRUNCATE TABLE group_post RESTART IDENTITY CASCADE;
TRUNCATE TABLE user_group RESTART IDENTITY CASCADE;
TRUNCATE TABLE "group" RESTART IDENTITY CASCADE;
TRUNCATE TABLE user_friend_request RESTART IDENTITY CASCADE;
TRUNCATE TABLE user_friend RESTART IDENTITY CASCADE;
TRUNCATE TABLE user_post_comment RESTART IDENTITY CASCADE;
TRUNCATE TABLE user_post RESTART IDENTITY CASCADE;
TRUNCATE TABLE user_description RESTART IDENTITY CASCADE;
TRUNCATE TABLE "user" RESTART IDENTITY CASCADE;

INSERT INTO "user"(username, password_hash, email, last_name, first_name, birth_date) VALUES (
    'admin',
    '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
    'admin@admin.com',
    'admin',
    'admin',
    CURRENT_DATE
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
INSERT INTO "user"(username, password_hash, email, last_name, first_name, birth_date, profile_photo_path) VALUES (
    'enachi.vasile',
    '05bd7470c9d713ab43aec7a4dd393d7f81d9c72a77039573e6b95df40ce71c7e',
    'enachi98@gmail.com',
    'Enachi',
    'Vasile',
    DATE('1998-05-13'),
    '/static/images/ricardo.jpg'
);
INSERT INTO "user"(username, password_hash, email, last_name, first_name, birth_date, profile_photo_path) VALUES (
    'mesina.maria',
    'c758a897588ebcb1853ac90e88090d1c127850a7d0e3c4745831754a066dd465',
    'mesina.maria@gmail.com',
    'Mesina',
    'Maria',
    DATE('1998-04-02'),
    '/static/images/maria.jpg'
);

INSERT INTO user_description VALUES ((SELECT id FROM "user" WHERE username='mesina.maria'), '37 de lei si un borcan cu dulceata');
INSERT INTO user_description VALUES ((SELECT id FROM "user" WHERE username='enachi.vasile'), 'Tuuuu te topesti la minus zece shot-uri de Tequila!');
INSERT INTO user_description VALUES ((SELECT id FROM "user" WHERE username='antoci.mihaela'), 'Prima fata de pe raion');
INSERT INTO user_description VALUES ((SELECT id FROM "user" WHERE username='oleg.barna'), 'Nu va jiucati cu focu!');
INSERT INTO user_description VALUES ((SELECT id FROM "user" WHERE username='bivol.eudochia'), 'Nu renunta la visele tale');

INSERT INTO user_friend VALUES ((SELECT id FROM "user" WHERE username='oleg.barna'), (SELECT id FROM "user" WHERE username='sava.valeria'));
INSERT INTO user_friend VALUES ((SELECT id FROM "user" WHERE username='oleg.barna'), (SELECT id FROM "user" WHERE username='bivol.eudochia'));
INSERT INTO user_friend VALUES ((SELECT id FROM "user" WHERE username='oleg.barna'), (SELECT id FROM "user" WHERE username='secrieru.mircea'));
INSERT INTO user_friend VALUES ((SELECT id FROM "user" WHERE username='oleg.barna'), (SELECT id FROM "user" WHERE username='antoci.mihaela'));
INSERT INTO user_friend VALUES ((SELECT id FROM "user" WHERE username='bivol.eudochia'), (SELECT id FROM "user" WHERE username='secrieru.mircea'));
INSERT INTO user_friend VALUES ((SELECT id FROM "user" WHERE username='sava.valeria'), (SELECT id FROM "user" WHERE username='secrieru.mircea'));
INSERT INTO user_friend VALUES ((SELECT id FROM "user" WHERE username='antoci.mihaela'), (SELECT id FROM "user" WHERE username='enachi.vasile'));
INSERT INTO user_friend VALUES ((SELECT id FROM "user" WHERE username='antoci.mihaela'), (SELECT id FROM "user" WHERE username='mesina.maria'));
INSERT INTO user_friend VALUES ((SELECT id FROM "user" WHERE username='enachi.vasile'), (SELECT id FROM "user" WHERE username='mesina.maria'));

INSERT INTO user_friend_request VALUES ((SELECT id FROM "user" WHERE username='antoci.mihaela'), (SELECT id FROM "user" WHERE username='sava.valeria'));
INSERT INTO user_friend_request VALUES ((SELECT id FROM "user" WHERE username='antoci.mihaela'), (SELECT id FROM "user" WHERE username='secrieru.mircea'));
INSERT INTO user_friend_request VALUES ((SELECT id FROM "user" WHERE username='sava.valeria'), (SELECT id FROM "user" WHERE username='bivol.eudochia'));
INSERT INTO user_friend_request VALUES ((SELECT id FROM "user" WHERE username='sava.valeria'), (SELECT id FROM "user" WHERE username='enachi.vasile'));
INSERT INTO user_friend_request VALUES ((SELECT id FROM "user" WHERE username='oleg.barna'), (SELECT id FROM "user" WHERE username='enachi.vasile'));

INSERT INTO user_post (content, user_id) VALUES ('Bine ati venit pe paagina mea oficiala de facebuci', (SELECT id FROM "user" WHERE username='oleg.barna'));
INSERT INTO user_post (content, user_id) VALUES ('Abia astept sa ninga afara, sa facem un om de zapada', (SELECT id FROM "user" WHERE username='bivol.eudochia'));
INSERT INTO user_post (content, user_id) VALUES ('Lucrurile bune se intampla cand te astepti mai putin', (SELECT id FROM "user" WHERE username='bivol.eudochia'));
INSERT INTO user_post (content, user_id) VALUES ('Daruiesc 2 pisici, vaccinati si steriliati', (SELECT id FROM "user" WHERE username='sava.valeria'));
INSERT INTO user_post (content, user_id) VALUES ('Cunoaste cineva cum ajung de la telecentru la botanica?', (SELECT id FROM "user" WHERE username='antoci.mihaela'));

INSERT INTO user_post_comment (post_id, user_id, content) VALUES (3, (SELECT id FROM "user" WHERE username='antoci.mihaela'), 'Deep');
INSERT INTO user_post_comment (post_id, user_id, content) VALUES (5, (SELECT id FROM "user" WHERE username='secrieru.mircea'), 'Troleibus 17');
INSERT INTO user_post_comment (post_id, user_id, content) VALUES (4, (SELECT id FROM "user" WHERE username='antoci.mihaela'), 'Astept poze in privat');
INSERT INTO user_post_comment (post_id, user_id, content) VALUES (4, (SELECT id FROM "user" WHERE username='secrieru.mircea'), 'Vreau si eu unul daca mai sunt disponibii');
INSERT INTO user_post_comment (post_id, user_id, content) VALUES (2, (SELECT id FROM "user" WHERE username='antoci.mihaela'), 'Putem face unul din noroi daca nu mai ai rabdare');

INSERT INTO "group"(creator_id, name) VALUES ((SELECT id FROM "user" WHERE username='sava.valeria'), 'Pisici de pretutindeni');
INSERT INTO "group"(creator_id, name) VALUES ((SELECT id FROM "user" WHERE username='secrieru.mircea'), 'Iasi-Bucuresti Bucuresti-Iasi');
INSERT INTO "group"(creator_id, name) VALUES ((SELECT id FROM "user" WHERE username='secrieru.mircea'), 'Hai la pacanele');
INSERT INTO "group"(creator_id, name) VALUES ((SELECT id FROM "user" WHERE username='antoci.mihaela'), 'Petrecere de anul nou');
INSERT INTO "group"(creator_id, name) VALUES ((SELECT id FROM "user" WHERE username='antoci.mihaela'), 'Meme-uri si din alea');

INSERT INTO user_group(user_id, group_id, role) VALUES((SELECT id FROM "user" WHERE username='sava.valeria'), (SELECT id FROM "group" WHERE name='Pisici de pretutindeni'), 'ADMIN');

INSERT INTO user_group VALUES((SELECT id FROM "user" WHERE username='antoci.mihaela'), (SELECT id FROM "group" WHERE name='Petrecere de anul nou'), 'ADMIN');
INSERT INTO user_group VALUES((SELECT id FROM "user" WHERE username='antoci.mihaela'), (SELECT id FROM "group" WHERE name='Meme-uri si din alea'), 'ADMIN');
INSERT INTO user_group VALUES((SELECT id FROM "user" WHERE username='oleg.barna'), (SELECT id FROM "group" WHERE name='Iasi-Bucuresti Bucuresti-Iasi'), 'ADMIN');
INSERT INTO user_group VALUES((SELECT id FROM "user" WHERE username='secrieru.mircea'), (SELECT id FROM "group" WHERE name='Hai la pacanele'), 'ADMIN');

INSERT INTO user_group VALUES((SELECT id FROM "user" WHERE username='antoci.mihaela'), (SELECT id FROM "group" WHERE name='Pisici de pretutindeni'), 'ADMIN');
INSERT INTO user_group VALUES((SELECT id FROM "user" WHERE username='secrieru.mircea'), (SELECT id FROM "group" WHERE name='Petrecere de anul nou'), 'WRITER');
INSERT INTO user_group VALUES((SELECT id FROM "user" WHERE username='oleg.barna'), (SELECT id FROM "group" WHERE name='Pisici de pretutindeni'), 'WRITER');

INSERT INTO user_group VALUES((SELECT id FROM "user" WHERE username='bivol.eudochia'), (SELECT id FROM "group" WHERE name='Iasi-Bucuresti Bucuresti-Iasi'), 'WRITER');
INSERT INTO user_group VALUES((SELECT id FROM "user" WHERE username='sava.valeria'), (SELECT id FROM "group" WHERE name='Iasi-Bucuresti Bucuresti-Iasi'), 'WRITER');
INSERT INTO user_group VALUES((SELECT id FROM "user" WHERE username='sava.valeria'), (SELECT id FROM "group" WHERE name='Hai la pacanele'), 'WRITER');

INSERT INTO group_post(content, group_id, user_id) VALUES('Am gasit azi o pisica in Copou, neagra ochii verzi, o cauta cineva?', (SELECT id FROM "group" WHERE name='Pisici de pretutindeni'), (SELECT id FROM "user" WHERE username='sava.valeria'));
INSERT INTO group_post(content, group_id, user_id) VALUES('Bine ati venit in "Pisici de pretutindeni', (SELECT id FROM "group" WHERE name='Pisici de pretutindeni'), (SELECT id FROM "user" WHERE username='sava.valeria'));
INSERT INTO group_post(content, group_id, user_id) VALUES('Am nevoie de o masina care pleaca miine spre Ungheni.', (SELECT id FROM "group" WHERE name='Iasi-Bucuresti Bucuresti-Iasi'), (SELECT id FROM "user" WHERE username='oleg.barna'));
INSERT INTO group_post(content, group_id, user_id) VALUES('Petrica are centura neagra la catan', (SELECT id FROM "group" WHERE name='Hai la pacanele'), (SELECT id FROM "user" WHERE username='secrieru.mircea'));
INSERT INTO group_post(content, group_id, user_id) VALUES('Cine are apartamentul liber', (SELECT id FROM "group" WHERE name='Petrecere de anul nou'), (SELECT id FROM "user" WHERE username='antoci.mihaela'));

INSERT INTO group_post_comment(content, post_id, user_id) VALUES('Nu stiu sigur, poti sa-mi trimiti o poza pe email?', 1, (SELECT id FROM "user" WHERE username='secrieru.mircea'));
INSERT INTO group_post_comment(content, post_id, user_id) VALUES('Vreau sa vad si eu o poza', 2, (SELECT id FROM "user" WHERE username='sava.valeria'));
INSERT INTO group_post_comment(content, post_id, user_id) VALUES('La ora 5 e ok?', 3, (SELECT id FROM "user" WHERE username='bivol.eudochia'));
INSERT INTO group_post_comment(content, post_id, user_id) VALUES('niceeee', 4, (SELECT id FROM "user" WHERE username='sava.valeria'));
INSERT INTO group_post_comment(content, post_id, user_id) VALUES('Oleg', 5, (SELECT id FROM "user" WHERE username='secrieru.mircea'));

INSERT INTO group_invitation(guest_id, host_id, group_id, role) VALUES((SELECT id FROM "user" WHERE username='sava.valeria'), (SELECT id FROM "user" WHERE username='bivol.eudochia'), (SELECT id FROM "group" WHERE name='Iasi-Bucuresti Bucuresti-Iasi'), 'READER');
INSERT INTO group_invitation(guest_id, host_id, group_id, role) VALUES((SELECT id FROM "user" WHERE username='antoci.mihaela'), (SELECT id FROM "user" WHERE username='oleg.barna'), (SELECT id FROM "group" WHERE name='Iasi-Bucuresti Bucuresti-Iasi'), 'WRITER');
INSERT INTO group_invitation(guest_id, host_id, group_id, role) VALUES((SELECT id FROM "user" WHERE username='enachi.vasile'), (SELECT id FROM "user" WHERE username='antoci.mihaela'), (SELECT id FROM "group" WHERE name='Petrecere de anul nou'), 'WRITER');
INSERT INTO group_invitation(guest_id, host_id, group_id, role) VALUES((SELECT id FROM "user" WHERE username='mesina.maria'), (SELECT id FROM "user" WHERE username='antoci.mihaela'), (SELECT id FROM "group" WHERE name='Meme-uri si din alea'), 'ADMIN');
INSERT INTO group_invitation(guest_id, host_id, group_id, role) VALUES((SELECT id FROM "user" WHERE username='enachi.vasile'), (SELECT id FROM "user" WHERE username='antoci.mihaela'), (SELECT id FROM "group" WHERE name='Meme-uri si din alea'), 'READER');
