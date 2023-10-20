"""Support for Tuya Locks"""
from __future__ import annotations

from dataclasses import dataclass

import logging

from homeassistant.components.lock import LockEntity, LockEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from tuya_iot import TuyaDevice, TuyaDeviceManager

from . import HomeAssistantTuyaData
from .base import TuyaEntity
from .const import DOMAIN, TUYA_DISCOVERY_NEW

@dataclass
class TuyaLockEntityDescription(LockEntityDescription):
    open_value: str = "True"
    closed_value: str = "False"
    unknown_value: str = "unknown"


LOCKS: dict[str, TuyaLockEntityDescription] = {
    "jtmsbh":
        TuyaLockEntityDescription(
            key="lock_motor_state",
            icon="mdi:lock",
        ),
}

_LOGGER = logging.getLogger(__name__)

l
async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up tuya lock dynamically through tuya discovery."""
    hass_data: HomeAssistantTuyaData = hass.data[DOMAIN][entry.entry_id]

    @callback
    def async_discover_device(device_ids: list[str]) -> None:
        """Discover and add a discovered tuya lock."""
        entities: list[TuyaLockEntity] = []
        for device_id in device_ids:
            device = hass_data.device_manager.device_map[device_id]
            if description := LOCKS.get(device.category):
                entities.append(TuyaLockEntity(device, hass_data.device_manager, description))

        async_add_entities(entities)

    async_discover_device([*hass_data.device_manager.device_map])

    entry.async_on_unload(
        async_dispatcher_connect(hass, TUYA_DISCOVERY_NEW, async_discover_device)
    )


class TuyaLockEntity(TuyaEntity, LockEntity):
    entity_description: TuyaLockEntityDescription | None = None

    def __init__(
            self,
            device: TuyaDevice,
            device_manager: TuyaDeviceManager,
            description: TuyaLockEntityDescription
    ) -> None:
        """Init TuyaHaLock."""
        super().__init__(device, device_manager)
        self.entity_description = description
        self._attr_unique_id = f"{super().unique_id}{description.key}"

    @property
    def is_locked(self) -> bool:
      # If the status is None, return None
      _LOGGER.debug(self.device.status)
      status = self.device.status.get("lock_motor_state")
      if status is None:
        return None

      # Return True if the status is True, False otherwise.
      return not status

    def lock(self, **kwargs):
        """Lock the lock."""
        self._send_command([{"code": self.entity_description.key, "value": False}])

    def unlock(self, **kwargs):
        """Unlock the lock."""
        self._send_command([{"code": self.entity_description.key, "value": True}])