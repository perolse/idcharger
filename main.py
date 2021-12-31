import signal
import time
import logging
import uuid
import paho.mqtt.client as mqtt
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


class Mqtt_manager:
    def __init__(self, settings):
        self.settings = settings
        logging.info("Starting MQTT client")
        client_id = 'VWIdCharger_' + uuid.uuid4().hex
        self.mqttClient = mqtt.Client(client_id=client_id)
        self.mqttClient.on_connect = self.on_connect
        if len(self.settings.mqtt_user + self.settings.mqtt_password) > 0:
            self.mqttClient.username_pw_set(
                username=self.settings.mqtt_user,
                password=self.settings.mqtt_password)

    def on_connect(self, client, userdata, flags, rc):
        logging.info("Connected with result code "+str(rc))
        self.connected_result = rc

    def mqtt_connect(self):
        logging.info("Connecting to MQTT client")
        self.mqttClient.connect(self.settings.mqtt_broker,
                                self.settings.mqtt_port)
        self.mqttClient.loop(20)
        return self.connected_result == 0

    def update_sensor_configs(self):
        config_address = 'homeassistant/sensor/vwidcharger/ct{id}/config'
        config_template = '{{\n' + \
            '  "device_class": "current",\n' + \
            '  "name": "VW ID Charger Ct-Coil-{id}",\n' + \
            '  "unique_id": "ct{id}",\n' + \
            '  "state_topic": "vw/idcharger/ctcoil",\n' + \
            '  "unit_of_measurement": "A",\n' + \
            '  "value_template": "{{{{ value_json.CT{id} }}}}"\n' + \
            '}}'
        result = self.mqttClient.publish(config_address.format(id='1'),
                                         config_template.format(id='1'))
        retval = result[0]
        result = self.mqttClient.publish(config_address.format(id='2'),
                                         config_template.format(id='2'))
        retval = retval + result[0]
        result = self.mqttClient.publish(config_address.format(id='3'),
                                         config_template.format(id='3'))
        retval = retval + result[0]
        return retval == 0

    def send_values(self, ct1, ct2, ct3):
        value_str = '{{\n' + \
                    '  "CT1":{val1},\n' + \
                    '  "CT2":{val2},\n' + \
                    '  "CT3":{val3}\n' + \
                    '}}'
        result = self.mqttClient.publish('vw/idcharger/ctcoil',
                                         value_str.format(val1=ct1,
                                                          val2=ct2,
                                                          val3=ct3))
        return result[0] == 0

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    killer = Killer()
    settings = Settings(settings_filename)
    id_charger = IdCharger(settings)
    mqtt_manager = Mqtt_manager(settings)
    if not mqtt_manager.mqtt_connect():
        logging.error("Couldn't connect to MQTT broker")
        exit()
    if not mqtt_manager.update_sensor_configs():
        logging.error("Couldn't update sensor configs")
        exit()
    while True:
        if id_charger.fetch_values():
            if mqtt_manager.send_values(id_charger.ct1, id_charger.ct2, id_charger.ct3):
                logging.info("Send values")
            else:
                logging.warning("Couldn't send values")
                mqtt_manager.mqtt_connect()
        time.sleep(10)
        if killer.kill_now:
            id_charger.stop()
            break
