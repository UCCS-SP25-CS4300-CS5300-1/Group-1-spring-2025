"""Module providing an HTMLTaskCalendar that displays tasks and holidays."""

import calendar
from datetime import datetime

class TaskCalendar(calendar.HTMLCalendar):
    """An HTMLCalendar subclass that shows tasks (and marks shared/archived)
    plus holidays in each day cell.
    """

    def __init__(self, tasks, **kwargs):
        super().__init__()
        self.tasks    = self.group_by_day(tasks)
        self.year     = kwargs.get('year')
        self.month    = kwargs.get('month')
        self.holidays = kwargs.get('holidays') or {}
        self.user     = kwargs.get('user')

    def group_by_day(self, tasks):
        """Organize tasks by their due day for quick lookup."""
        task_dict = {}
        for task in tasks:
            day = task.due_date.day
            task_dict.setdefault(day, []).append(task)
        return task_dict

    def formatday(self, day, weekday):
        """Return the <td> HTML for one day, with up to 2 tasks and any holiday."""
        if day == 0:
            return '<td class="noday">&nbsp;</td>'

        cssclass = self.cssclasses[weekday]
        now = datetime.today()
        if day == now.day and self.month == now.month and self.year == now.year:
            cssclass += ' today'

        # build task snippets (max 2, then “more…")
        snippets = []
        day_tasks = self.tasks.get(day, [])
        for t in day_tasks[:2]:
            flags = []
            if getattr(t, 'is_archived', False):
                flags.append('archived')
            elif t.creator != self.user:
                flags.append('shared')
            cls = f' {" ".join(flags)}' if flags else ''
            snippets.append(f'<div class="task{cls}">{t.name[:7]}</div>')
        if len(day_tasks) > 2:
            snippets.append('<div class="task more">…</div>')

        hol_html = ''
        hol_name = self.holidays.get(day)
        if hol_name:
            hol_html = f'<div class="holiday">{hol_name}</div>'

        return (
            f'<td class="{cssclass}">'  # type: ignore
            f'<span class="date">{day}</span><br>'
            f'{"".join(snippets)}{hol_html}'
            f'</td>'
        )

    def formatmonth(self, theyear, themonth, withyear=True):
        """Render the full month calendar, updating self.year/self.month first."""
        self.year, self.month = theyear, themonth
        return super().formatmonth(theyear, themonth, withyear=withyear)
