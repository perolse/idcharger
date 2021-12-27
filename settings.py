import json


class Settings:
    def __init__(self, settings_filename):
        settings_file = open(settings_filename)
        self.settings = json.load(settings_file)
        settings_file.close()

    @property
    def host(self):
        return self.settings['host']

    @property
    def password(self):
        return self.settings['password']

    @property
    def mqtt_broker(self):
        return self.settings['mqttBroker']

    @property
    def mqtt_port(self):
        return self.settings['mqttPort']

    @property
    def mqtt_user(self):
        return self.settings['mqttUser']

    @property
    def mqtt_password(self):
        return self.settings['mqttPassword']
