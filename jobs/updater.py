from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from .jobs import schedule_api


def start():
    """
Schedule a recurring job to call `schedule_api()` function every week, starting from March 15th, 2023.

:return: None
"""
    start_date = datetime.strptime('2023-03-15', '%Y-%m-%d')
    scheduler = BackgroundScheduler()
    scheduler.add_job(schedule_api, 'interval', start_date=start_date, weeks=1)
    scheduler.start()
