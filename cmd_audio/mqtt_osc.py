"""MQTT/OSC integration (Phase 4.2)."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from cmd_audio.logging_config import get_logger

logger = get_logger(__name__)

try:
    import paho.mqtt.publish as mqtt_publish  # type: ignore[import-untyped]
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False
    mqtt_publish = None  # type: ignore[assignment]


class MQTTClient:
    """MQTT client for publishing audio features."""

    def __init__(self, broker: str = "localhost", port: int = 1883, topic: str = "cmd-audio/"):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.running = False
        self._client = None

    def start(self) -> None:
        if not HAS_MQTT:
            logger.warning("paho-mqtt not installed")
            return
        self.running = True

    def stop(self) -> None:
        self.running = False

    def publish_audio_features(self, level: float, beat: bool, flux: float) -> None:
        if not self.running or not HAS_MQTT:
            return
        data = json.dumps({"level": level, "beat": beat, "flux": flux})
        try:
            mqtt_publish.single(f"{self.topic}audio", data, hostname=self.broker, port=self.port)  # type: ignore[union-attr]
        except Exception as exc:
            logger.error("MQTT publish error: %s", exc)


class OSCClient:
    """OSC client for publishing audio features to live performance tools."""

    def __init__(self, host: str = "localhost", port: int = 9000):
        self.host = host
        self.port = port
        self.running = False

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def send_osc(self, address: str, value: Any) -> None:
        if not self.running:
            return
        logger.info("OSC send: %s %s", address, value)


def create_mqtt_client(broker: str = "localhost") -> MQTTClient:
    return MQTTClient(broker)


def create_osc_client(host: str = "localhost", port: int = 9000) -> OSCClient:
    return OSCClient(host, port)