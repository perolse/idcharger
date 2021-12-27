import requests
import paho.mqtt.client as mqtt
from settings import Settings
import logging
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class IdCharger:
    def __init__(self, settings):
        self.settings = settings
        self.loginUrl = '/api/v1/auth/login'
        self.ctCoilUrl = '/api/v1/evse-settings/ct-coil-measured-current'
        self.ct1 = 0.0
        self.ct2 = 0.0
        self.ct3 = 0.0
        logging.info("Starting MQTT client")
        self.mqttClient = mqtt.Client()
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

    def fetch_values(self):
        try:
            login_response = requests.post(
                url=self.settings.host+self.loginUrl,
                json={"password": self.settings.password},
                verify=False)
            headers = {
                'Authorization': 'Bearer '
                + login_response.json().get('access_token')
            }
            ct_coil_response = requests.get(
                url=self.settings.host+self.ctCoilUrl,
                headers=headers, verify=False)
            self.ct1 = float(ct_coil_response.json().get('CT1'))
            self.ct2 = float(ct_coil_response.json().get('CT2'))
            self.ct3 = float(ct_coil_response.json().get('CT3'))
            return True
        except Exception:
            return False

    def send_values(self):
        value_str = '{{\n' + \
                    '  "CT1":{val1},\n' + \
                    '  "CT2":{val2},\n' + \
                    '  "CT3":{val3}\n' + \
                    '}}'
        result = self.mqttClient.publish('vw/idcharger/ctcoil',
                                         value_str.format(val1=self.ct1,
                                                          val2=self.ct2,
                                                          val3=self.ct3))
        return result[0] == 0
