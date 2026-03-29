"""Switch platform for Connection Watchdog — toggle auto-restart."""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

log = logging.getLogger(__name__)

DEVICE_INFO = {
    "identifiers": {(DOMAIN, "connection_watchdog")},
    "name": "Connection Watchdog",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AutoRestartSwitch(coordinator)])


class AutoRestartSwitch(SwitchEntity, RestoreEntity):
    """Switch to enable/disable automatic restart."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:shield-refresh"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_auto_restart"
        self._attr_device_info = DEVICE_INFO

    @property
    def name(self) -> str:
        return "Automatischer Neustart"

    @property
    def is_on(self) -> bool:
        return self._coordinator.auto_restart_enabled

    async def async_turn_on(self, **kwargs) -> None:
        """Enable auto-restart."""
        self._coordinator.set_auto_restart(True)
        log.info("Auto-restart enabled")

    async def async_turn_off(self, **kwargs) -> None:
        """Disable auto-restart."""
        self._coordinator.set_auto_restart(False)
        log.info("Auto-restart disabled")

    async def async_added_to_hass(self) -> None:
        """Restore previous state."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state == "off":
            self._coordinator.set_auto_restart(False)
