import base64
import time
import os
import requests
import urllib.parse
import hashlib
import hmac
import configparser

config = configparser.ConfigParser()
config.read("conf.ini")

api_url = config["K_ACC"]["url"]
api_key = config["K_ACC"]["key"]
api_sec = config["K_ACC"]["secret"]
investment_amount = config["K_ACC"]["amount"]


class Kraken_api:

    # Attaches auth headers and returns results of a POST request
    def kraken_order(self, asset_data, order, new_asset_price, logger):

        vol = int(investment_amount) / float(new_asset_price)

        if "buy" == order:
            uri_path = "/0/private/AddOrder"
            data = {
                "nonce": str(int(1000 * time.time())),
                "ordertype": "market",
                "type": order,
                "volume": vol,
                "pair": asset_data["name"],
            }

        if "sell" == order:
            uri_path = "/0/private/AddOrder"
            data = {
                "nonce": str(int(1000 * time.time())),
                "ordertype": "market",
                "type": order,
                "volume": vol,
                "pair": asset_data["name"],
            }

        if "short sell" == order:
            uri_path = "/0/private/AddOrder"
            data = {
                "nonce": str(int(1000 * time.time())),
                "ordertype": "market",
                "type": "sell",
                "volume": vol,
                "pair": asset_data["name"],
                "leverage": 5,
            }
        if "close short sell" == order:
            uri_path = "/0/private/AddOrder"
            data = {
                "nonce": str(int(1000 * time.time())),
                "ordertype": "market",
                "type": "buy",
                "volume": vol,
                "pair": asset_data["name"],
                "leverage": 5,
            }

        headers = {}
        headers["API-Key"] = api_key
        headers["API-Sign"] = self._get_kraken_signature(uri_path, data, api_sec)
        req = requests.post((api_url + uri_path), headers=headers, data=data)

        if not req.status_code == 200:
            logger.exception(
                "Status " + str(req.status_code) + ", " + order + " order failed"
            )
            raise Exception("Status " + str(req.status_code))
        else:
            logger.info(self.get_date() + order + " status: " + str(req.status_code))

    # @staticmethod
    def get_date(self):
        return "[" + time.strftime("%d-%m-%Y,%H:%M:%S") + "]: "

    def _get_kraken_signature(self, urlpath, data, secret):

        postdata = urllib.parse.urlencode(data)
        encoded = (str(data["nonce"]) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()
