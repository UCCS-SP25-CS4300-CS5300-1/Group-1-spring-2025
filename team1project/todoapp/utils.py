import calendar
from datetime import datetime

class TaskCalendar(calendar.HTMLCalendar):
    def __init__(self, tasks, year, month):
        super().__init__()
        self.year = year
        self.month = month
        self.tasks = self.group_by_day(tasks)

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
        
        day_tasks = self.tasks.get(day, [])
        display_tasks = []
        # If more than 3 tasks, display first 2 (truncated) and then ellipsis.
        if len(day_tasks) > 3:
            for task in day_tasks[:2]:
                display_tasks.append(f'<div class="task">{task.name[:7]}</div>')
            display_tasks.append('<div class="task">...</div>')
        else:
            for task in day_tasks:
                display_tasks.append(f'<div class="task">{task.name[:7]}</div>')
        
        task_html = ''.join(display_tasks)
        return f'<td class="{cssclass}"><span class="date">{day}</span><br>{task_html}</td>'

    def formatmonth(self, year, month, withyear=True):
        self.year, self.month = year, month
        return super().formatmonth(year, month, withyear=withyear)
