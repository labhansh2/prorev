import sqlite3
import pathlib
import logging
import os
import sys

logger = logging.getLogger(__name__)


def connect_db(query, mode='w'):

    if hasattr(sys, "_MEIPASS"):
        # Running as executable
        # base_path = sys._MEIPASS
        base_path = os.path.dirname(sys.executable)
        path = os.path.join(base_path, "data")
        data_path = pathlib.Path(path)
        # print(data_path)
    else:
        # Running as script
        data_path = pathlib.Path(__file__).parent/f"../data/"

    connection = sqlite3.connect(data_path/"data.db")

    cur = connection.cursor()

    try:
        cur.execute(query)
    except Exception as e:
        logger.error('Error Running Qury: {}'.format(e))
    else:
        data = cur.fetchall()
        connection.commit()
        connection.close()

    if mode == 'r':
        return data


def create_table():

    q = f'''CREATE TABLE IF NOT EXISTS 'Main' ( 
                                main_id varchar(255) PRIMARY KEY, 
                                temp_id varchar(255));'''
    logger.info('Creating Table for Task Ids')
    connect_db(q)


def store_main_id(main_id):
    q = f'''INSERT INTO 'Main' (main_id) VALUES ('{main_id}');'''
    logger.debug('Storing Main Id : {}'.format(main_id))
    connect_db(q)


def store_pending_id(pending_id, main_id):
    q = f'''UPDATE 'Main' SET temp_id='{pending_id}'
        WHERE main_id='{main_id}';'''
    logger.debug('Storing Pending Id : {} for Main : {}'.format(
        pending_id, main_id))
    connect_db(q)


def get_all(id_type):
    q = f'''SELECT {id_type} FROM Main;'''
    logger.debug('Fetching All {} from DB'.format(id_type))
    data = connect_db(q, 'r')
    ids = []
    for id in data:
        ids.append(id[0])
    return ids


def get_main_for_pending(pending_id):
    q = f'''SELECT main_id FROM Main WHERE temp_id='{pending_id}';'''
    logger.debug('Fetching Main Id for Pending ID : {}'.format(pending_id))
    id = connect_db(q, 'r')
    return id[0][0]


def get_pending_for_main(main_id):
    q = f'''SELECT temp_id FROM Main WHERE main_id='{main_id}';'''
    logger.debug('Fetching Pending Id for Main ID : {}'.format(main_id))
    data = connect_db(q, 'r')
    if not data:
        return None
    return data[0][0]


def delete_pending_id(main_id):
    q = f'''UPDATE Main SET temp_id= Null WHERE main_id='{main_id}';'''
    logger.debug('Deleting pending ID for Main : {}'.format(main_id))
    connect_db(q)


def create_connection_table():
    q = f'''CREATE TABLE IF NOT EXISTS 'connection' (
                                integration_token varchar(255) PRIMARY KEY, 
                                page_name varchar(255),
                                process_id varchar(255),
                                notif_channel varchar(255));'''
    logger.info('Creating Connection Table If Not Exists')
    connect_db(q)


def get_connection():
    q = f'''SELECT * FROM connection'''
    logger.debug('Getting Connection Details')
    data = connect_db(q, 'r')
    logger.debug('Connection Details : {}'.format(data))
    return data


def add_connection(integration_token, page_name, process_id, notif_channel):
    q = '''INSERT INTO connection (integration_token, page_name, process_id, notif_channel)
    VALUES ('{}', '{}', '{}', '{}')'''.format(integration_token, page_name, process_id, notif_channel)
    logger.debug('Adding Connection Details : {}'. format(
        integration_token, page_name, process_id, notif_channel))
    connect_db(q)


def update_pid(process_id, integration_token):
    q = '''UPDATE connection SET process_id = '{}' where integration_token ='{}';'''.format(
        process_id, integration_token)
    logger.debug('Updating PID : {}'.format(process_id))
    connect_db(q)


def update_notif_channel(notif_channel, integration_token):
    q = '''UPDATE connection SET notif_channel = '{}' where integration_token ='{}';'''.format(
        notif_channel, integration_token)
    logger.debug(
        'Updating Notification Channel Info : {}'.format(notif_channel))
    connect_db(q)


def update_page_name(page_name, integration_token):
    q = '''UPDATE connection SET page_name = '{}' where integration_token ='{}';'''.format(
        page_name, integration_token)
    logger.debug(
        'Updating Page Name : {}'.format(page_name))
    connect_db(q)


def erase_connection():
    q = '''DELETE FROM connection'''
    logger.info('Erasing Existing Connection Info')
    connect_db(q)


if __name__ == "__main__":
    create_connection_table()
    db_conn = get_connection()
    print(db_conn)
    add_connection('e', '', '', '')
    if len(db_conn) != 0:
        integration_token = db_conn[0][0]
        page_name = db_conn[0][1]
    print(integration_token)
    print(page_name)
    erase_connection()
