"""Binary sensor platform for Connection Watchdog."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

DEVICE_INFO = {
    "identifiers": {(DOMAIN, "connection_watchdog")},
    "name": "Connection Watchdog",
    "manufacturer": "Connection Watchdog",
    "model": "Verbindungsüberwachung",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [InternetConnectivitySensor(coordinator)]
    if coordinator.fritzbox_url:
        entities.append(FritzBoxReachabilitySensor(coordinator))

    async_add_entities(entities)


class InternetConnectivitySensor(BinarySensorEntity):
    """Binary sensor for internet connectivity."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_icon = "mdi:web"

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_internet"
        self._attr_device_info = DEVICE_INFO

    @property
    def name(self) -> str:
        return "Internetverbindung"

    @property
    def is_on(self) -> bool:
        return self._coordinator.internet_connected

    async def async_added_to_hass(self) -> None:
        """Register update listener."""
        @callback
        def _update():
            self.async_write_ha_state()

        self._coordinator.register_listener(_update)
        self.async_on_remove(lambda: self._coordinator.remove_listener(_update))

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "consecutive_failures": self._coordinator.consecutive_failures,
            "in_cooldown": self._coordinator.in_cooldown,
        }


class FritzBoxReachabilitySensor(BinarySensorEntity):
    """Binary sensor for FritzBox reachability."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_icon = "mdi:router-wireless"

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_fritzbox"
        self._attr_device_info = DEVICE_INFO

    @property
    def name(self) -> str:
        return "FritzBox"

    @property
    def is_on(self) -> bool:
        return self._coordinator.fritzbox_reachable

    async def async_added_to_hass(self) -> None:
        """Register update listener."""
        @callback
        def _update():
            self.async_write_ha_state()

        self._coordinator.register_listener(_update)
        self.async_on_remove(lambda: self._coordinator.remove_listener(_update))

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "fritzbox_url": self._coordinator.fritzbox_url,
        }
