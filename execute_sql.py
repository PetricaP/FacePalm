import argparse

import psycopg2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('script_path', help='Path to sql file to execute')
    args = parser.parse_args()

    db_connection = psycopg2.connect(host='localhost', database='bdp', user='postgres', password='password')

    with open(args.script_path, 'r') as script:
        with db_connection.cursor() as cursor:
            cursor.execute(script.read())
        db_connection.commit()


if __name__ == '__main__':
    main()
