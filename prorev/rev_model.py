from datetime import datetime, timedelta
from pprint import pprint
import logging

logger = logging.getLogger(__name__)


def get_plan(task_obj: dict):

    logger.info('Generating Plan of {} for Task : {}'.format(
        task_obj['duration']['name'], task_obj['task']))
    initial_round = 1
    initial_date = datetime.strptime(task_obj['date'], "%Y-%m-%d").date()

    rev_plan = {
        '3 Months': [3, 7, 16, 35, 68, 90],
        '1 Month': [3, 7, 16, 31],
        '1 Week': [2, 4, 7]
    }

    plan = []

    for n in enumerate(rev_plan[task_obj['duration']['name']]):
        round_no = initial_round + n[0] + 1
        date = str(initial_date + timedelta(days=n[1]))

        new_task_obj = task_obj.copy()

        new_task_obj['round_no'] = round_no
        new_task_obj['date'] = date
        new_task_obj['done'] = False

        plan.append(new_task_obj)

    return plan


if __name__ == "__main__":
    eg_task_obj = {
        "task": 'something',
        "duration": {'name': '3 Months'},
        "done": False,
        "round_no": 1,
        "date": "2023-06-16"
    }

    pprint(get_plan(eg_task_obj))
