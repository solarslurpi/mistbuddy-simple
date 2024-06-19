"""The focus is on publishing mqtt messages to the Tasmotized power switches.  Receiving readings comes over telegraf.

"""
from dotenv import load_dotenv
load_dotenv()


import logging
import os
import random
import string
import paho.mqtt.client as mqtt


from logger_code import LoggerBase

logger = LoggerBase.setup_logger("mqtt_code", logging.DEBUG)
#

# MQTT Error values from https://github.dev/eclipse/paho.mqtt.python/tree/master/src/paho/mqtt/client.py
rc_codes = {
    "MQTT_ERR_AGAIN": -1,
    "MQTT_ERR_SUCCESS": 0,
    "MQTT_ERR_NOMEM": 1,
    "MQTT_ERR_PROTOCOL": 2,
    "MQTT_ERR_INVAL": 3,
    "MQTT_ERR_NO_CONN": 4,
    "MQTT_ERR_CONN_REFUSED": 5,
    "MQTT_ERR_NOT_FOUND": 6,
    "MQTT_ERR_CONN_LOST": 7,
    "MQTT_ERR_TLS": 8,
    "MQTT_ERR_PAYLOAD_SIZE": 9,
    "MQTT_ERR_NOT_SUPPORTED": 10,
    "MQTT_ERR_AUTH": 11,
    "MQTT_ERR_ACL_DENIED": 12,
    "MQTT_ERR_UNKNOWN": 13,
    "MQTT_ERR_ERRNO": 14,
    "MQTT_ERR_QUEUE_SIZE": 15,
    "MQTT_ERR_KEEPALIVE": 16,
}


class MQTTClient:

    def __init__(self, host):
        # The client ID is a unique identifier that is used by the broker to identify this
        # client. If a client ID is not provided, a unique ID is generated and used instead.
        self.host = host
        self.client_id = "".join(
            random.choice(string.ascii_lowercase) for i in range(10)
        )

        try:
            self.client = mqtt.Client(client_id=self.client_id, clean_session=False)
        except Exception as e:
            logger.debug(f"mqtt_code.init: Error creating MQTT client.  The error is {e}.")
            raise e
        # This will be sent to subscribers who asked to receive the LWT for this mqtt client.
        self.client.will_set("/lwt", "offline", qos=1, retain=False)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc) -> int:
        """mqtt_code.publish: Callback function that is called when the client connects to the MQTT broker."""
        logger.debug(
            f"mqtt_code.publish: Connected to broker **{self.host}**.  The ClientID is {self.client_id}.  The result code is {str(rc)}"
        )
        if rc != 0:
            logger.error(
                f"mqtt_code.publish: Received an unexpected error in on_connect.  The error is {rc_codes[rc]}"
            )
            return rc

    def on_disconnect(self, client, userdata, rc) -> int:
        if rc != 0:
            logger.error(
                f"mqtt_code.publish: Received an unexpected disconnect.  The error is {rc_codes[rc]}"
            )
        return rc

    def on_message(self, client, userdata, msg) -> None:
        logger.debug(f"mqtt_code.publish: Received MQTT message: {msg.payload.decode('utf-8')}")


    def publish(self, topic, message, qos=1):
        logger.debug(f"mqtt_code.publish: Publishing message {message} to topic {topic}.")
        rc = self.client.publish(topic, message, qos)
        return rc

    def disconnect(self):
        self.client.disconnect()

    def start(self):

        self.client.connect(self.host)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
