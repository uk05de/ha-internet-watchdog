"""Sensor platform for Internet Watchdog."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

log = logging.getLogger(__name__)

DEVICE_INFO = {
    "identifiers": {(DOMAIN, "internet_watchdog")},
    "name": "Internet Watchdog",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        RestartCountSensor(coordinator),
        LastRestartSensor(coordinator),
    ])


class RestartCountSensor(SensorEntity, RestoreEntity):
    """Sensor tracking total restart count."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_restart_count"
        self._attr_device_info = DEVICE_INFO

    @property
    def name(self) -> str:
        return "Neustarts"

    @property
    def native_value(self) -> int:
        return self._coordinator.restart_count

    async def async_added_to_hass(self) -> None:
        """Restore restart count and register listener."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in ("unknown", "unavailable"):
            self._coordinator.set_restart_count(int(float(last_state.state)))
            log.info("Restored restart count: %d", self._coordinator.restart_count)

        @callback
        def _update():
            self.async_write_ha_state()

        self._coordinator.register_listener(_update)
        self.async_on_remove(lambda: self._coordinator.remove_listener(_update))


class LastRestartSensor(SensorEntity):
    """Sensor showing last restart timestamp."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = "timestamp"

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_last_restart"
        self._attr_device_info = DEVICE_INFO

    @property
    def name(self) -> str:
        return "Letzter Neustart"

    @property
    def native_value(self):
        return self._coordinator.last_restart

    async def async_added_to_hass(self) -> None:
        """Register listener."""
        @callback
        def _update():
            self.async_write_ha_state()

        self._coordinator.register_listener(_update)
        self.async_on_remove(lambda: self._coordinator.remove_listener(_update))
