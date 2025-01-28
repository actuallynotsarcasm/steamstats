import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine

from schemas import Base


def create_db():
    try:
        connection = psycopg2.connect(user='postgres',
                                    password='admin',
                                    host='localhost',
                                    port='5432')
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        cursor.execute('select exists (select from pg_database where datname = \'steamstats\');')
        db_exists = cursor.fetchone()[0]
        if not db_exists:
            sql_create_database = 'CREATE DATABASE steamstats'
            cursor.execute(sql_create_database)
            connection.commit()
    except (Exception, Error) as error:
        print('Error creating db:', error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print('Connection closed')

    try:
        print('Creating engine and tables')
        engine = create_engine('postgresql+psycopg2://postgres:admin@localhost/steamstats')
        Base.metadata.create_all(engine)
    except (Exception, Error) as error:
        print('Error creating engine or tables:', error)