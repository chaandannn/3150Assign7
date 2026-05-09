import logging
import teslapy

logger = logging.getLogger('groot.tesla')


class TeslaClient:
    def __init__(self, config: dict):
        self.email = config['tesla']['email']

    def _wake_vehicle(self, tesla: teslapy.Tesla):
        vehicles = tesla.vehicle_list()
        if not vehicles:
            raise RuntimeError('No Tesla vehicles found on this account')
        v = vehicles[0]
        v.sync_wake_up()
        return v

    def get_status(self) -> dict:
        with teslapy.Tesla(self.email) as tesla:
            v = self._wake_vehicle(tesla)
            data = v.get_vehicle_data()
        charge = data['charge_state']
        climate = data['climate_state']
        vehicle = data['vehicle_state']
        drive = data['drive_state']
        return {
            'battery_level': charge['battery_level'],
            'battery_range_miles': round(charge['battery_range'], 1),
            'charging_state': charge['charging_state'],
            'is_locked': vehicle['locked'],
            'odometer_miles': round(vehicle['odometer']),
            'climate_on': climate['is_climate_on'],
            'inside_temp_f': _c_to_f(climate.get('inside_temp')),
            'outside_temp_f': _c_to_f(climate.get('outside_temp')),
            'speed_mph': drive.get('speed') or 0,
        }

    def climate_on(self, temp_f: float = 70.0) -> str:
        temp_c = (temp_f - 32) * 5 / 9
        with teslapy.Tesla(self.email) as tesla:
            v = self._wake_vehicle(tesla)
            v.command('CLIMATE_ON')
            v.command('CHANGE_CLIMATE_TEMPERATURE_SETTING', driver_temp=temp_c, passenger_temp=temp_c)
        return f'Climate on, set to {temp_f:.0f}°F'

    def climate_off(self) -> str:
        with teslapy.Tesla(self.email) as tesla:
            v = self._wake_vehicle(tesla)
            v.command('CLIMATE_OFF')
        return 'Climate turned off'

    def lock(self) -> str:
        with teslapy.Tesla(self.email) as tesla:
            v = self._wake_vehicle(tesla)
            v.command('LOCK')
        return 'Car locked'

    def unlock(self) -> str:
        with teslapy.Tesla(self.email) as tesla:
            v = self._wake_vehicle(tesla)
            v.command('UNLOCK')
        return 'Car unlocked'

    def honk(self) -> str:
        with teslapy.Tesla(self.email) as tesla:
            v = self._wake_vehicle(tesla)
            v.command('HONK_HORN')
        return 'Horn honked'

    def flash_lights(self) -> str:
        with teslapy.Tesla(self.email) as tesla:
            v = self._wake_vehicle(tesla)
            v.command('FLASH_LIGHTS')
        return 'Lights flashed'

    def start_charging(self) -> str:
        with teslapy.Tesla(self.email) as tesla:
            v = self._wake_vehicle(tesla)
            v.command('START_CHARGE')
        return 'Charging started'

    def stop_charging(self) -> str:
        with teslapy.Tesla(self.email) as tesla:
            v = self._wake_vehicle(tesla)
            v.command('STOP_CHARGE')
        return 'Charging stopped'

    def open_charge_port(self) -> str:
        with teslapy.Tesla(self.email) as tesla:
            v = self._wake_vehicle(tesla)
            v.command('CHARGE_PORT_DOOR_OPEN')
        return 'Charge port opened'

    def set_charge_limit(self, percent: int) -> str:
        with teslapy.Tesla(self.email) as tesla:
            v = self._wake_vehicle(tesla)
            v.command('CHANGE_CHARGE_LIMIT', percent=percent)
        return f'Charge limit set to {percent}%'


def _c_to_f(celsius):
    if celsius is None:
        return None
    return round(celsius * 9 / 5 + 32, 1)
