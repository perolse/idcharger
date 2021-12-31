import requests
from settings import Settings
import logging
import threading
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class IdCharger:
    def __init__(self, settings):
        self.settings = settings
        self.loginUrl = '/api/v1/auth/login'
        self.refreshUrl = '/api/v1/auth/refresh'
        self.ctCoilUrl = '/api/v1/evse-settings/ct-coil-measured-current'
        self.access_token = None
        self.refresh_token = None
        self.ct1 = 0.0
        self.ct2 = 0.0
        self.ct3 = 0.0
        self.update_access_token()

    def login(self):
        try:
            logging.info("Try to login on Id Charger")
            login_response = requests.post(
                url=self.settings.host+self.loginUrl,
                json={"password": self.settings.password},
                verify=False, timeout=30)
            if login_response.status_code != requests.codes.ok:
                logging.error("Login failed, status: %s", login_response.status_code)
                self.access_token = None
                self.refresh_token = None
                return
            self.access_token = login_response.json().get('access_token')
            self.refresh_token = login_response.json().get('refresh')
        except Exception as e:
            logging.error("Login Id Charger failed: %s", str(e))
            self.access_token = None

    def refresh(self):
        try:
            logging.info("Try to refresh token on Id Charger")
            refresh_response = requests.post(
                url=self.settings.host+self.refreshUrl,
                json={"refresh_token": self.refresh_token},
                verify=False, timeout=30)
            if refresh_response.status_code != requests.codes.ok:
                logging.error("Refresh failed, status: %s", refresh_response.status_code)
                self.access_token = None
                return False
            self.access_token = refresh_response.json().get('access_token')
        except Exception as e:
            logging.error("Refresh access token for Id Charger failed: %s", str(e))
            self.access_token = None

    def update_access_token(self):
        try:
            if self.refresh_token == None:
                if self.login():
                    raise Exception("Login failed")
            else:
                if not refresh():
                    if self.login():
                        raise Exception("Login failed")
            self.token_refresh_timer = threading.Timer(120, self.update_access_token)
            self.token_refresh_timer.start()

        except Exception as e:
            logging.error("Update access token for Id Charger failed: %s", str(e))
            self.access_token = None
            self.refresh_token = None

    def stop(self):
        self.token_refresh_timer.cancel()

    def fetch_values(self):
        try:
            headers = {
                'Authorization': 'Bearer ' + self.access_token
            }
            logging.info("Try to fetch values")
            ct_coil_response = requests.get(
                url=self.settings.host+self.ctCoilUrl,
                headers=headers, verify=False, timeout=10)
            if ct_coil_response.status_code != requests.codes.ok:
                logging.error("Fetch failed, status: %s", ct_coil_response.status_code)
                return False
            logging.info("Values fetched")
            self.ct1 = float(ct_coil_response.json().get('CT1'))
            self.ct2 = float(ct_coil_response.json().get('CT2'))
            self.ct3 = float(ct_coil_response.json().get('CT3'))
            return True
        except Exception as e:
            logging.info("Fetch values failed: %s", str(e))
            return False

