import jdatetime
from datetime import date, datetime

def to_jalali(value):
    """
    تبدیل تاریخ میلادی به جلالی
    :param value: datetime یا date object
    :return: string "YYYY/MM/DD"
    """
    if isinstance(value, datetime):
        value = value.date()
    return jdatetime.date.fromgregorian(date=value).strftime("%Y/%m/%d")