"""Button platform for Internet Watchdog."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
    """Set up button entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ManualRestartButton(coordinator)])


class ManualRestartButton(ButtonEntity):
    """Button to manually trigger FritzBox restart."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:restart-alert"

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_manual_restart"
        self._attr_device_info = DEVICE_INFO

    @property
    def name(self) -> str:
        return "FritzBox Neustart"

    async def async_press(self) -> None:
        """Trigger restart."""
        log.warning("Manual FritzBox restart triggered")
        await self._coordinator.async_trigger_restart()
