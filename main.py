from notion_client import Client
from notion_client import errors
from tqdm import tqdm
from datetime import datetime, timedelta
import time
import logging
import argparse
import os
import sys
import pyqrcode
import pathlib
import requests
import logging

from prorev import rev_model
from prorev.Notion import *
from prorev import data
from prorev import notification
from prorev import log_config

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true',
                    help='Enable debug logging')
parser.add_argument('--info', action='store_true',
                    help='Enable info logging [DEFAULT]')
parser.add_argument('--error', action='store_true',
                    help='Enable error logging')
parser.add_argument('--warning', action='store_true',
                    help='Enable warning logging')
parser.add_argument('--new_connection', action='store_true',
                    help='Erases Existing Connection For Creating a New Connection')
args = parser.parse_args()

log_level = logging.INFO

if args.debug:
    log_level = logging.DEBUG
elif args.info:
    log_level = logging.INFO
elif args.error:
    log_level = logging.ERROR
elif args.warning:
    log_level = logging.WARNING

log_config.setup_logging(log_level=log_level)
logger = logging.getLogger(__name__)

if args.new_connection:
    data.erase_connection()


class operations:

    notify = True
    notify_curr = datetime.now().strftime('%H:%M')

    def __init__(self, main_db: database, pending_db: database) -> None:
        self.main_db = main_db
        self.pending_db = pending_db

    def operate_new(self):

        all_task_ids = self.main_db.get_round1_ids()
        existing_task_ids = data.get_all('main_id')

        new_task_ids = list(set(all_task_ids).difference(existing_task_ids))
        logger.info(f"{len(new_task_ids)} New Tasks Found")
        for id in new_task_ids:
            data.store_main_id(id)

            obj = self.main_db.get_task_obj(id)
            plan = rev_model.get_plan(obj)

            for each in plan:
                added_id = self.main_db.add_task(each)
                data.store_main_id(added_id)

    def operate_pending(self):

        pending_task_ids = self.main_db.get_pending_task_id()

        for id in pending_task_ids:
            if id not in data.get_all('main_id'):
                # means not yet operated as new
                self.operate_new()
            if data.get_pending_for_main(id) == None:
                # means not added to pending db
                task_obj = self.main_db.get_task_obj(id)
                added_id = self.pending_db.add_task(task_obj)
                data.store_pending_id(added_id, id)

    def sync(self):

        done = self.pending_db.get_all()

        for t_id in done:
            if self.pending_db.get_task_obj(t_id)['done'] == True:
                try:
                    m_id = data.get_main_for_pending(t_id)
                except:
                    self.pending_db.delete_task(t_id)
                else:
                    self.pending_db.delete_task(t_id)
                    self.main_db.mark_done(m_id)
                    data.delete_pending_id(m_id)

        to_do = self.pending_db.get_pending_task_id()

        for t_id in to_do:
            try:
                m_id = data.get_main_for_pending(t_id)
            except:
                self.pending_db.delete_task(t_id)
            else:
                task_obj = self.main_db.get_task_obj(m_id)
                if task_obj:
                    if task_obj['done'] == True:
                        self.pending_db.delete_task(t_id)
                        data.delete_pending_id(m_id)

    def notif(self):

        notification_timings = ['06:00',
                                '09:00',
                                '12:00',
                                '15:00',
                                '18:00',
                                '21:00']

        current_time = datetime.now().strftime('%H:%M')
        if current_time in notification_timings and operations.notify == True:

            operations.notify_curr = current_time
            pending_tasks = self.pending_db.get_all()

            connection_info = data.get_connection()
            ep = connection_info[0][3]

            for id in pending_tasks:
                task_obj = self.pending_db.get_task_obj(id)
                notif = notification.Notifications(endpoint=ep)
                notif.send_notification(task_obj)

            operations.notify = False

        if datetime.strptime(
            current_time, '%H:%M'
        ) == datetime.strptime(
            operations.notify_curr, '%H:%M'
        ) + timedelta(minutes=1):
            operations.notify = True


def set_page(notion_instance, page_name):

    if not page_name or page_name == "None":
        page_name = input("Enter the name of your page: ")

    try:
        rev_page = page(notion_instance, page_name=page_name)
        page_id = rev_page.pid
    except errors.APIResponseError as e:
        logger.error(str(e) + ": Try Again : Help at : (url of README)")
        exit()
    except IndexError as i:
        logger.error("PAGE NOT FOUND : Try Again : Help at : (url of README)")
        exit()

    database_info = rev_page.get_databases()
    if not database_info:
        rev_page.initialize()
        with tqdm(total=100,
                  desc='Fethcing Database Details...',
                  unit='%',
                  bar_format='''  {desc}: {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt}'''
                  ) as progress_bar:
            # logger.info('Fethcing Database Details...')
            while not database_info:
                database_info = rev_page.get_databases(mode='v')
                progress_bar.update(2)
            progress_bar.update(100 - progress_bar.n)
        progress_bar.close()
        print(
            f'''\nInitalized on:\n  Page ID   : {page_id}\n  Page Name : {page_name}'''
        )
    else:
        print(
            f'''\nConnected on:\n  Page ID   : {page_id}\n  Page Name : {page_name}'''
        )
    return {
        "rev_page": rev_page,
        "page_id": page_id,
        "page_name": page_name,
        "database_ids": database_info
    }


def verify_internet_connection():
    try:
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def notif_config():
    notif_endpoint, channel = notification.Notifications().get_endpoint()
    qr_id = str(notif_endpoint).replace(
        "https://notify.run/", "") + '.png'

    if hasattr(sys, "_MEIPASS"):
        # Running as executable
        # base_path = sys._MEIPASS
        base_path = os.path.dirname(sys.executable)
        path = os.path.join(base_path, "img")
        qr_path = pathlib.Path(path)
    else:
        # Running as script
        qr_path = pathlib.Path(__file__).parent/f"img/"

    QR_code = pyqrcode.create(channel)
    QR_code.png(qr_path/qr_id, scale=6)
    return notif_endpoint

    # try:
    #     qr_path = pathlib.Path(__file__).parent/"../img/"
    #     QR_code = pyqrcode.create(channel)
    #     QR_code.png(qr_path/qr_id, scale=6)
    #     return notif_endpoint
    # except:
    #     # path for the build
    #     qr_path = pathlib.Path(__file__).parent/"img/"


def main(integration_token=None, page_name=None, notif_endpoint=None):

    if not verify_internet_connection():
        logger.error('No Intenet Connection')
        return

    data.create_connection_table()
    db_conn = data.get_connection()

    # if some connection info already exists
    if len(db_conn) != 0:
        integration_token = db_conn[0][0]
        page_name = db_conn[0][1]
        notif_endpoint = db_conn[0][3]

    if not integration_token:
        integration_token = input("Enter you integration token: ")

    notion_instance = Client(auth=integration_token)

    try:
        page_info = set_page(notion_instance, page_name)
    except errors.APIResponseError as api_error:
        logger.error(api_error, ' Notion API Not Working. Try Again')
        exit()
    except errors.HTTPResponseError as httpresponse_error:
        logger.error(httpresponse_error)
        exit()
    except Exception as e:
        logger.exception(e, exc_info=True, stack_info=True)
        logger.error(e, 'error')
        exit()
    else:

        database_ids = page_info['database_ids']
        pending_database_id = database_ids['pending_database_id']
        allTasks_database_id = database_ids['allTasks_database_id']
        print(
            f'''Databases Found:\n  Pending   : {pending_database_id}\n  All Tasks : {allTasks_database_id}\n'''
        )

        if notif_endpoint == '' or notif_endpoint == None:
            notif_endpoint = notif_config()

        # can improve code quality here
        # can improvise on the db flow for the connection
        data.erase_connection()
        data.add_connection(integration_token, page_info['page_name'], '', '')
        data.update_pid(os.getpid(), integration_token)
        data.update_notif_channel(notif_endpoint, integration_token)

        print('\nYour Notification Endpoint : {}\n'. format(notif_endpoint))

        data.create_table()

        pending = database(notion_instance, pending_database_id)
        main = database(notion_instance, allTasks_database_id)

        ops = operations(main, pending)

    while True:

        # add better error handling
        try:
            ops.operate_new()
            ops.operate_pending()
            ops.sync()
            ops.notif()
            logger.info('SLEEP MODE : 10s')
            time.sleep(10)
        except errors.APIResponseError as api_error:
            logger.warning(api_error)
        except errors.HTTPResponseError as httpresponse_error:
            logger.warning(httpresponse_error)
        except errors.RequestTimeoutError as timeout_err:
            logger.warning(timeout_err)
        except PermissionError:
            # needa figure this out
            print('Having Issues swapping log files')
        except Exception as e:
            if isinstance(e, PermissionError):
                print('Having Issues swapping log files')
            else:
                logger.error(e)
        except KeyboardInterrupt:
            # have to add soemething here
            exit()


if __name__ == "__main__":
    main()
    # print(data.get_all('main_id'))
