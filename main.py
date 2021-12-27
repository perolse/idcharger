import signal
import time
from idcharger import IdCharger
from settings import Settings

settings_filename = '/data/options.json'


class Killer:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


if __name__ == '__main__':
    killer = Killer()
    settings = Settings(settings_filename)
    id_charger = IdCharger(settings)
    if not id_charger.mqtt_connect():
        print("Couldn't connect to MQTT broker")
        exit()
    if not id_charger.update_sensor_configs():
        print("Couldn't update sensor configs")
        exit()
    while True:
        if id_charger.fetch_values():
            if id_charger.send_values():
                print("Send values")
            else:
                print("Couldn't send values")
        time.sleep(10)
        if killer.kill_now:
            break
