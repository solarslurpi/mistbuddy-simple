'''Very basic MQTT client class for publishing Mistbuddy messages to the power switches.'''
from contextlib import contextmanager
import logging
import random
import string
from typing import Generator, Optional
import paho.mqtt.client as mqtt
import ssl
import src.logging_config
from src.service.exceptions_code import MQTTConnectionError, MQTTPublishError, MQTTSetupError

logger = logging.getLogger(__name__)

class MQTTClient:

    def __init__(self, host:str, port: int=1883, use_ssl: bool = False):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.logger = logger
        self.client_id = self._generate_client_id()
        try:
            self.client = self._setup_client()
        except Exception as e:
            logger.error(f"Error setting up MQTT client", exc_info=True)
            raise MQTTSetupError("Error setting up MQTT client") from e

    def _generate_client_id(self) -> str:
        return "".join(random.choice(string.ascii_lowercase) for _ in range(10))

    def _setup_client(self) -> mqtt.Client:
        try:
            client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv5)
            client.will_set("/lwt", "offline", qos=1, retain=False)
            client.on_connect = self.on_connect
            return client
        except Exception:
            logger.error(f"Error setting up MQTT client.", exc_info=True)
            raise

    def on_connect(self, client, userdata, flags, rc) -> int:
        if rc == 0:
            logger.info(
                f"Connected to broker {self.host}.  The ClientID is {self.client_id}"
            )
        else:
            logger.error(
                f"Connection to broker failed.", exc_info=True
            )

    def _connect(self) -> None:
        try:
            if self.use_ssl:
                self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
            self.client.connect(self.host, self.port)
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker",exc_info=True)
            raise MQTTConnectionError("Failed to connect to MQTT broker") from e

    @contextmanager
    def connection(self) -> Generator[None, None, None]:
        self._connect()
        try:
            yield
        finally:
            pass # No need to disconnect. The client will be disconnected when the context manager exits.

    def publish(self, topic: str, message: str, qos: int = 1, retain: bool = False) -> Optional[mqtt.MQTTMessageInfo]:
        try:
            with self.connection():
                self.client.publish(topic, message, qos, retain)
                logger.info(f"Message published. Topic: {topic}")
        except Exception as e:
            logger.error(f"Failed to publish message to topic {topic}", exc_info=True)
            raise MQTTPublishError("Error setting up MQTT client") from e

# Usage example:
# with MQTTClient("broker.example.com").connection():
#     client.publish("topic", "message")
