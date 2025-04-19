import calendar
from datetime import datetime

class TaskCalendar(calendar.HTMLCalendar):
    def __init__(self, tasks, year, month, holidays=None):
        super().__init__()
        self.year     = year
        self.month    = month
        self.tasks    = self.group_by_day(tasks)
        self.holidays = holidays or {}

    def group_by_day(self, tasks):
        """Organize tasks by their due day for quick lookup."""
        task_dict = {}
        for task in tasks:
            task_day = task.due_date.day
            task_dict.setdefault(task_day, []).append(task)
        return task_dict

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'

        cssclass = self.cssclasses[weekday]
        today = datetime.today()
        if day == today.day and self.month == today.month and self.year == today.year:
            cssclass += ' today'

        # 1) tasks
        day_tasks = self.tasks.get(day, [])
        task_html = ''.join(
            f'<div class="task">{t.name[:7]}</div>'
            for t in day_tasks[:2]
        ) + ('<div class="task">…</div>' if len(day_tasks) > 2 else '')

        # 2) holiday (if any)
        hol_name = self.holidays.get(day)
        hol_html = f'<div class="holiday">{hol_name}</div>' if hol_name else ''

        return (f'<td class="{cssclass}">'
                f'<span class="date">{day}</span><br>'
                f'{task_html}{hol_html}'
                f'</td>')

                
    def formatmonth(self, year, month, withyear=True):
        self.year, self.month = year, month
        return super().formatmonth(year, month, withyear=withyear)
