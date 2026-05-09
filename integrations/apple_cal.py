import logging
import uuid
from datetime import datetime
import caldav
from icalendar import Calendar, Event

logger = logging.getLogger('groot.apple_cal')

ICLOUD_URL = 'https://caldav.icloud.com'


class AppleCalendar:
    def __init__(self, config: dict):
        self._user = config['apple']['username']
        self._pass = config['apple']['password']
        self._principal = None

    def _connect(self):
        if self._principal:
            return
        client = caldav.DAVClient(url=ICLOUD_URL, username=self._user, password=self._pass)
        self._principal = client.principal()

    def get_events(self, start: datetime, end: datetime) -> list:
        self._connect()
        events = []
        for cal in self._principal.calendars():
            try:
                for ev in cal.date_search(start=start, end=end, expand=True):
                    cal_obj = Calendar.from_ical(ev.data)
                    for comp in cal_obj.walk('VEVENT'):
                        dtstart = comp.get('DTSTART')
                        dtend = comp.get('DTEND')
                        events.append({
                            'title': str(comp.get('SUMMARY', 'Untitled')),
                            'start': str(dtstart.dt) if dtstart else '',
                            'end': str(dtend.dt) if dtend else '',
                            'location': str(comp.get('LOCATION', '')),
                            'source': 'apple',
                        })
            except Exception as e:
                logger.warning(f'Error reading Apple calendar {cal.name}: {e}')
        return sorted(events, key=lambda x: x['start'])

    def create_event(self, title: str, start: datetime, end: datetime,
                     description: str = '', location: str = '') -> dict:
        self._connect()
        calendars = self._principal.calendars()
        if not calendars:
            raise RuntimeError('No Apple calendars found')
        cal = Calendar()
        cal.add('prodid', '-//Groot//EN')
        cal.add('version', '2.0')
        event = Event()
        event.add('uid', str(uuid.uuid4()))
        event.add('summary', title)
        event.add('dtstart', start)
        event.add('dtend', end)
        if description:
            event.add('description', description)
        if location:
            event.add('location', location)
        cal.add_component(event)
        calendars[0].add_event(cal.to_ical().decode())
        return {'title': title, 'start': str(start)}
