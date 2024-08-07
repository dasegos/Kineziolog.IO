# Other imports
import os
import calendar
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import pandas as pd
from dotenv import load_dotenv

async def process_data(year: int, month: int, day: int, hour: int, minute: int, rollback: int) -> int:
    '''The function returns the `int` instance which 
       represents the unique timestamp of the time when task
       has to be executed
    '''
    if (rollback == 3 and day <= 3) or (rollback == 1 and day <= 1):
        prev_month_days = calendar.monthrange(year, month-1)
        prev_month_day = prev_month_days[1] - abs(day - rollback)
        return int(datetime.timestamp(datetime(year, month-1, prev_month_day, hour, minute)) / 60)
    return int(datetime.timestamp(datetime(year, month, day-rollback, hour, minute)) / 60)

async def process_time(now: datetime, event: datetime) -> int:
    '''The function returns difference between two events in seconds'''
    difference = event - now 
    return difference.total_seconds()

async def to_excel(values: dict[str, list], path: str) -> str:
    '''The function converts dataframes into excel file'''
    dataframe = pd.DataFrame(values)
    dataframe.to_excel(path, sheet_name='Статистика', index=False)
    return path

async def send_mail(to: str, text: str):
    '''The function sends an email'''
    load_dotenv()
    login = os.getenv('GMAIL_LOGIN')
    password = os.getenv('GMAIL_PASSWORD')

    email = MIMEText(text, 'plain', 'utf-8')
    email['Subject'] = Header('Поступил запрос на обратную связь!', 'utf-8')
    email['From'] = login
    email['To'] = to

    con = smtplib.SMTP(host='smtp.gmail.com', port=587)
    con.ehlo() # Not necessary
    con.starttls()
    con.ehlo() # Not necessary
    con.login(login, password)
    con.sendmail(email['From'], to, email.as_string())
    con.quit()

        
        