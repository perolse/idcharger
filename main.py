import signal
import time
import logging
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
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    killer = Killer()
    settings = Settings(settings_filename)
    id_charger = IdCharger(settings)
    if not id_charger.mqtt_connect():
        logging.error("Couldn't connect to MQTT broker")
        exit()
    if not id_charger.update_sensor_configs():
        logging.error("Couldn't update sensor configs")
        exit()
    while True:
        if id_charger.fetch_values():
            if id_charger.send_values():
                logging.info("Send values")
            else:
                logging.warn("Couldn't send values")
        time.sleep(10)
        if killer.kill_now:
            break
