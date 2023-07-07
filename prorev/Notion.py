from notion_client import Client
from pprint import pprint
from tqdm import tqdm
from datetime import date
import logging

import data

logger = logging.getLogger(__name__)


class page:

    def __init__(
            self,
            notion_instance: Client,
            page_id: str = None,
            page_name: str = None
    ) -> None:
        self.notion = notion_instance
        if page_id:
            self.pid = page_id
        if page_name:
            self.name = page_name
            self.pid = self.get_page(page_name)

    def get_page(self, page_name):

        logger.info('Searching for Page : {}'.format(page_name))
        target_page = self.notion.search(
            query=page_name, **{
                "object": "page"
            }
        )

        # sloppy
        try:
            target_page['results'][0]['id']
        except IndexError:
            logger.error('Page Not Found')
        else:
            logger.info('Page Found')

        if target_page:
            return target_page['results'][0]['id']

    def get_databases(self, mode=None):

        if mode == 'v':
            # logger.info('Searching For Databases')
            result = self.notion.search(filter={
                "property": "object", "value": "database"
            })
        else:
            # this is important coz, there is a delay in Notion API and this can show the old data if recently deleted
            # with progress bar:
            try:
                with tqdm(
                    total=100,
                    desc='Fetching the Page...        ',
                    unit='%',
                    bar_format='''  {desc}: {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt}'''
                ) as progress_bar:
                    for _ in range(10):
                        result = self.notion.search(filter={
                            "property": "object",
                            "value": "database"
                        }
                        )
                        progress_bar.update(10)
            except:
                logger.info(
                    'Fethcing the page...')
                for _ in range(10):
                    result = self.notion.search(filter={
                        "property": "object",
                        "value": "database"
                    }
                    )

        count = 0
        for res in result['results']:
            if res['parent'] == {
                'page_id': self.pid,
                'type': 'page_id'
            }:
                if res['title'][0]['text']['content'] == 'Pending':
                    pending_database_id = res['id']
                elif res['title'][0]['text']['content'] == 'All Tasks':
                    allTasks_database_id = res['id']
                count += 1

        if mode != 'v':
            logger.debug(f"{count} databases found for user's page")
        if count == 2:
            return {
                "pending_database_id": pending_database_id,
                "allTasks_database_id": allTasks_database_id
            }
        else:
            return False

    def initialize(self):

        database_properties = {
            'Task Name': {
                'name': 'Task Name',
                'title': {},
                'type': 'title'
            },
            'Select Duration': {
                'name': 'Select Duration',
                'select': {
                    'options': [
                        {
                            'color': 'orange',
                            'name': '1 '
                            'Week'
                        },
                        {
                            'color': 'blue',
                            'name': '1 '
                            'Month'
                        },
                        {
                            'color': 'green',
                            'name': '3 '
                            'Months'
                        }
                    ]
                },
                'type': 'select'
            },
            'Done': {
                'checkbox': {},
                'name': 'Done',
                'type': 'checkbox'
            },
            'Round': {
                'name': 'Round',
                'number': {'format': 'number'},
                'type': 'number'
            },
            'Date': {
                'date': {},
                'name': 'Date',
                'type': 'date'
            }}

        with tqdm(total=100,
                  desc='Creating Databases...       ',
                  unit='%',
                  bar_format='''  {desc}: {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt}'''
                  ) as progress_bar:
            # logger.info('Creating Databases...')
            self.notion.databases.create(
                title=[
                    {
                        'annotations': {
                            'bold': False,
                            'code': False,
                            'color': 'default',
                            'italic': False,
                            'strikethrough': False,
                            'underline': False
                        },
                        'href': None,
                        'plain_text': 'Pending',
                        'text': {
                            'content': 'Pending',
                            'link': None
                        },
                        'type': 'text'
                    }
                ],
                parent={"type": "page_id", "page_id": self.pid},
                properties=database_properties,
                is_inline=True
            )
            progress_bar.update(50)

            self.notion.databases.create(
                title=[
                    {
                        'annotations': {
                            'bold': False,
                            'code': False,
                            'color': 'default',
                            'italic': False,
                            'strikethrough': False,
                            'underline': False
                        },
                        'href': None,
                        'plain_text': 'Today',
                        'text': {
                            'content': 'All Tasks', 'link': None
                        },
                        'type': 'text'
                    }
                ],
                parent={
                    "type": "page_id",
                    "page_id": self.pid
                },
                properties=database_properties,
                is_inline=True
            )
            progress_bar.update(50)
        progress_bar.close()


class database:
    def __init__(self, notion_instance, database_id: str) -> None:
        self.db_Id = database_id
        self.notion: Client = notion_instance

    def get_round1_ids(self, task_type=True):

        logger.debug('Getting Round 1 Tasks from All Tasks')
        result = self.notion.databases.query(database_id=self.db_Id, filter={
            "and": [
                {
                    "property": 'Date',
                    "date": {
                        "is_not_empty": True
                    }
                },
                {
                    "property": "Round",
                    "number": {
                        "equals": 1
                    }
                },
                {
                    "property": "Task Name",
                    "title": {
                        "is_not_empty": True
                    }
                },
                {
                    "property": "Select Duration",
                    "select": {
                        "is_not_empty": True
                    }
                }
            ]
        })

        round1_ids = []

        logger.debug('Classifying New Tasks')
        for res in result['results']:
            round1_ids.append(res['id'])
        logger.debug(f"{len(round1_ids)} Round 1 Tasks Found")
        return round1_ids

    def get_pending_task_id(self, task_type=False):

        current_date = date.today().strftime("%Y-%m-%d")

        logger.debug(
            'Querying Database For Pending Tasks [Tasks On or Before {}]'.format(current_date))
        result = self.notion.databases.query(database_id=self.db_Id, filter={
            "and": [
                {
                    'property': "Date",
                    'date': {
                        'on_or_before':  current_date
                    }
                },
                {
                    "property": 'Done',
                    "checkbox": {
                        "equals": task_type
                    }
                },
                {
                    "property": "Round",
                    "number": {
                        "is_not_empty": True
                    }
                },
                {
                    "property": "Task Name",
                    "title": {
                        "is_not_empty": True
                    }
                },
                {
                    "property": "Select Duration",
                    "select": {
                        "is_not_empty": True
                    }
                }
            ]
        })

        pending_task_ids = [res['id'] for res in result['results']]

        logger.info(f"{len(pending_task_ids)} Pending Tasks Found")
        return pending_task_ids

    def add_task(self, task_obj):

        task_properties = {
            'Date': {
                'date': {
                    'end': None,
                    'start': task_obj['date'],
                    'time_zone': None
                },
                'type': 'date'
            },
            'Done': {
                'checkbox': task_obj['done'],
                'type': 'checkbox'
            },
            'Task Name': {
                'title': [
                    {
                        'plain_text': 'newly added '
                        'task',
                        'text': {
                            'content': task_obj['task'],
                            'link': None
                        },
                        'type': 'text'
                    }
                ],
                'type': 'title'
            },
            'Round': {
                'number': task_obj['round_no'],
                'type': 'number'
            },
            'Select Duration': {
                'select': task_obj['duration'],
                'type': 'select'
            }
        }

        logger.info(
            f"Adding Task: {task_obj['task']} [Round: {task_obj['round_no']}]")
        new_page = self.notion.pages.create(
            parent={'database_id': self.db_Id,
                    'type': 'database_id'},
            properties=task_properties
        )
        logger.debug(f"{new_page['id']} Added")
        return new_page['id']

    def get_task_obj(self, task_id):

        task = None
        duration = None
        done = None
        round_no = None
        date = None

        logger.debug('Getting Task Info for Task ID : {}'.format(task_id))
        while any(
            var is None for var in (
                task, duration, done, round_no, date
            )
        ) and type(duration) != dict:

            logger.debug('Querying Database for Task Info')
            result = self.notion.databases.query(database_id=self.db_Id)

            for res in result['results']:
                if res['id'] == task_id:
                    task = res['properties']['Task Name']['title'][0]['plain_text']
                    duration = res['properties']['Select Duration']['select']
                    done = res['properties']['Done']['checkbox']
                    round_no = res['properties']['Round']['number']
                    date = res['properties']['Date']['date']['start']

        duration.pop('id')
        logger.debug(f"{task} - Found")
        return {
            "task": task,
            "duration": duration,
            "done": done,
            "round_no": round_no,
            "date": date
        }

    def mark_done(self, task_id):

        properties = {
            "Done": {
                "type": "checkbox",
                'checkbox': True
            }
        }
        logger.debug("Marking Task Done : {}".format(task_id))
        self.notion.pages.update(page_id=task_id,
                                 properties=properties)

    def delete_task(self, task_id):
        logger.debug('Deleting Task : {}'.format(task_id))
        self.notion.pages.update(page_id=task_id,
                                 archived=True)

    def get_all(self):

        logger.debug('Quering Database For All Tasks')
        result = self.notion.databases.query(
            database_id=self.db_Id,
            filter={
                "and": [
                    {
                        'property': "Date",
                        'date': {
                            'is_not_empty':  True
                        }
                    },
                    {
                        "property": "Round",
                        "number": {
                            "is_not_empty": True
                        }
                    },
                    {
                        "property": "Task Name",
                        "title": {
                            "is_not_empty": True
                        }
                    },
                    {
                        "property": "Select Duration",
                        "select": {
                            "is_not_empty": True
                        }
                    }
                ]
            }
        )
        all_tasks = [res['id'] for res in result['results']]
        logger.debug(f"{len(all_tasks)} Tasks Found in the DB")
        return all_tasks


if __name__ == "__main__":
    """testing"""
    # p = page(notion, '3bdaa6af-241a-44b3-b01c-51de394943ab')
    # p.get_databases('v')

    # d = database(notion, 'dce1e09a-6da1-4c0e-8c7d-351c437aa84c')
    # while True:
    #     print('getting...')
    #     ids = d.get_new_task_ids()
    #     pprint(ids)
    # pprint(p)

    # today = []
    # while True:
    #     ids = database.get_today_task_id(
    #         '5036e964-0f4c-4d48-a42d-82145e7bd103')
    #     for id in ids:

    #         if id not in today:
    #             obj = database.get_task_obj(
    #                 '5036e964-0f4c-4d48-a42d-82145e7bd103', id)
    #             database.add_task('5047042d-61a6-49f5-aefd-7f5bb1445d16', obj)
    #             today.append(id)
    ...
