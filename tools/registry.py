import json
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger('groot.tools')

_clients: dict = {}


def _tesla(config):
    if 'tesla' not in _clients:
        from integrations.tesla import TeslaClient
        _clients['tesla'] = TeslaClient(config)
    return _clients['tesla']


def _google(config):
    if 'google_cal' not in _clients:
        from integrations.google_cal import GoogleCalendar
        _clients['google_cal'] = GoogleCalendar(config)
    return _clients['google_cal']


def _apple(config):
    if 'apple_cal' not in _clients:
        from integrations.apple_cal import AppleCalendar
        _clients['apple_cal'] = AppleCalendar(config)
    return _clients['apple_cal']


def get_tools(config: dict) -> list:
    return [
        {
            'name': 'get_current_datetime',
            'description': 'Returns the current date and time.',
            'input_schema': {'type': 'object', 'properties': {}, 'required': []},
        },
        {
            'name': 'get_calendar_events',
            'description': 'Fetch upcoming events from Google and/or Apple Calendar.',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'days_ahead': {'type': 'integer', 'description': 'Days ahead to look (default 7)', 'default': 7},
                    'source': {'type': 'string', 'enum': ['google', 'apple', 'all'], 'default': 'all'},
                },
                'required': [],
            },
        },
        {
            'name': 'create_calendar_event',
            'description': 'Create a new event on Google or Apple Calendar.',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'start_iso': {'type': 'string', 'description': 'ISO 8601 start datetime'},
                    'end_iso': {'type': 'string', 'description': 'ISO 8601 end datetime'},
                    'description': {'type': 'string', 'default': ''},
                    'location': {'type': 'string', 'default': ''},
                    'calendar': {'type': 'string', 'enum': ['google', 'apple'], 'default': 'google'},
                },
                'required': ['title', 'start_iso', 'end_iso'],
            },
        },
        {
            'name': 'tesla_get_status',
            'description': 'Get Tesla Model 3 status: battery level, range, lock state, climate, temperature.',
            'input_schema': {'type': 'object', 'properties': {}, 'required': []},
        },
        {
            'name': 'tesla_climate',
            'description': 'Turn Tesla climate on or off, optionally with a target temperature.',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'action': {'type': 'string', 'enum': ['on', 'off']},
                    'temperature_f': {'type': 'number', 'description': 'Target temp in Fahrenheit (when on)', 'default': 70},
                },
                'required': ['action'],
            },
        },
        {
            'name': 'tesla_lock',
            'description': 'Lock or unlock the Tesla.',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'action': {'type': 'string', 'enum': ['lock', 'unlock']},
                },
                'required': ['action'],
            },
        },
        {
            'name': 'tesla_honk',
            'description': 'Honk the Tesla horn or flash lights.',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'action': {'type': 'string', 'enum': ['honk', 'flash_lights']},
                },
                'required': ['action'],
            },
        },
        {
            'name': 'tesla_charging',
            'description': 'Control Tesla charging: start, stop, open charge port, or set charge limit.',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'action': {'type': 'string', 'enum': ['start', 'stop', 'open_port', 'set_limit']},
                    'charge_limit_percent': {
                        'type': 'integer',
                        'description': 'Charge limit % (for set_limit)',
                        'minimum': 50,
                        'maximum': 100,
                    },
                },
                'required': ['action'],
            },
        },
    ]


async def execute_tool(name: str, inputs: dict, config: dict) -> str:
    try:
        if name == 'get_current_datetime':
            return datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')

        if name == 'get_calendar_events':
            days = inputs.get('days_ahead', 7)
            source = inputs.get('source', 'all')
            now = datetime.now(timezone.utc)
            end = now + timedelta(days=days)
            events = []
            if source in ('google', 'all'):
                try:
                    events.extend(_google(config).get_events(now, end))
                except Exception as e:
                    logger.warning(f'Google Calendar error: {e}')
            if source in ('apple', 'all'):
                try:
                    events.extend(_apple(config).get_events(now, end))
                except Exception as e:
                    logger.warning(f'Apple Calendar error: {e}')
            return json.dumps(events, default=str) if events else 'No events found.'

        if name == 'create_calendar_event':
            start = datetime.fromisoformat(inputs['start_iso'])
            end = datetime.fromisoformat(inputs['end_iso'])
            cal = inputs.get('calendar', 'google')
            title = inputs['title']
            kw = {'description': inputs.get('description', ''), 'location': inputs.get('location', '')}
            if cal == 'google':
                _google(config).create_event(title, start, end, **kw)
            else:
                _apple(config).create_event(title, start, end, **kw)
            return f"Event '{title}' created in {cal} calendar."

        if name == 'tesla_get_status':
            return json.dumps(_tesla(config).get_status())

        if name == 'tesla_climate':
            if inputs['action'] == 'on':
                return _tesla(config).climate_on(inputs.get('temperature_f', 70.0))
            return _tesla(config).climate_off()

        if name == 'tesla_lock':
            return _tesla(config).lock() if inputs['action'] == 'lock' else _tesla(config).unlock()

        if name == 'tesla_honk':
            return _tesla(config).honk() if inputs['action'] == 'honk' else _tesla(config).flash_lights()

        if name == 'tesla_charging':
            action = inputs['action']
            t = _tesla(config)
            if action == 'start':
                return t.start_charging()
            if action == 'stop':
                return t.stop_charging()
            if action == 'open_port':
                return t.open_charge_port()
            if action == 'set_limit':
                return t.set_charge_limit(inputs.get('charge_limit_percent', 80))

        return f'Unknown tool: {name}'

    except Exception as e:
        logger.error(f'Tool {name} failed: {e}', exc_info=True)
        return f'Error: {e}'
