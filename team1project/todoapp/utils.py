import calendar
from datetime import datetime

class TaskCalendar(calendar.HTMLCalendar):
    def __init__(self, tasks, year, month, holidays=None, user=None):
        super().__init__()
        self.year     = year
        self.month    = month
        self.tasks    = self.group_by_day(tasks)
        self.holidays = holidays or {}
        self.user     = user

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

        # 1) tasks (mark shared ones)
        day_tasks = self.tasks.get(day, [])
        snippets = []
        for t in day_tasks[:2]:
            # if archived, flag “archived”; else if shared, flag “shared”
            cls = []
            if getattr(t, 'is_archived', False):
                cls.append('archived')
            elif t.creator != self.user:
                cls.append('shared')
            cls_str = ' ' + ' '.join(cls) if cls else ''
            snippets.append(
                f'<div class="task{cls_str}">{t.name[:7]}</div>'
        )
        if len(day_tasks) > 2:
            snippets.append('<div class="task more">…</div>')
        task_html = ''.join(snippets)
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
