"""Connection Watchdog integration — monitors internet/FritzBox and triggers restart via Shelly."""

import asyncio
import logging
from datetime import datetime, timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_FRITZBOX_URL,
    CONF_SWITCH_ENTITY,
    CONF_CHECK_INTERVAL,
    CONF_FAILURE_THRESHOLD,
    CONF_COOLDOWN,
    CONF_MAX_RESTARTS,
    DEFAULT_CHECK_INTERVAL,
    DEFAULT_FAILURE_THRESHOLD,
    DEFAULT_COOLDOWN,
    DEFAULT_MAX_RESTARTS,
    INTERNET_CHECK_TARGETS,
)

log = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "sensor", "button", "switch"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Connection Watchdog from a config entry."""
    coordinator = WatchdogCoordinator(hass, entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await coordinator.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: WatchdogCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update — reload the integration."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _check_tcp(host: str, port: int, timeout: float = 5.0) -> bool:
    """Check if a host:port is reachable via TCP connection."""
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (OSError, asyncio.TimeoutError):
        return False


async def _check_url(url: str, timeout: float = 10.0) -> bool:
    """Check if a URL is reachable via HTTP HEAD request."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout),
                ssl=False,
            ) as resp:
                return resp.status < 500
    except Exception:
        return False


class WatchdogCoordinator:
    """Monitors connectivity and triggers restart when needed."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry

        self._internet_connected = True
        self._fritzbox_reachable = True
        self._consecutive_failures = 0
        self._restart_count = 0
        self._last_restart: datetime | None = None
        self._in_cooldown = False
        self._cooldown_until: datetime | None = None
        self._auto_restart_enabled = True
        self._consecutive_restarts = 0
        self._unsub_timer = None
        self._listeners: list[callback] = []

    @property
    def fritzbox_url(self) -> str:
        return self.entry.options.get(CONF_FRITZBOX_URL, "")

    @property
    def switch_entity(self) -> str:
        return self.entry.options.get(CONF_SWITCH_ENTITY, "")

    @property
    def check_interval(self) -> int:
        return self.entry.options.get(CONF_CHECK_INTERVAL, DEFAULT_CHECK_INTERVAL)

    @property
    def failure_threshold(self) -> int:
        return self.entry.options.get(CONF_FAILURE_THRESHOLD, DEFAULT_FAILURE_THRESHOLD)

    @property
    def cooldown(self) -> int:
        return self.entry.options.get(CONF_COOLDOWN, DEFAULT_COOLDOWN)

    @property
    def max_restarts(self) -> int:
        return self.entry.options.get(CONF_MAX_RESTARTS, DEFAULT_MAX_RESTARTS)

    @property
    def internet_connected(self) -> bool:
        return self._internet_connected

    @property
    def fritzbox_reachable(self) -> bool:
        return self._fritzbox_reachable

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    @property
    def restart_count(self) -> int:
        return self._restart_count

    @property
    def last_restart(self) -> datetime | None:
        return self._last_restart

    @property
    def auto_restart_enabled(self) -> bool:
        return self._auto_restart_enabled

    @property
    def in_cooldown(self) -> bool:
        return self._in_cooldown

    def set_auto_restart(self, enabled: bool) -> None:
        """Toggle auto-restart."""
        self._auto_restart_enabled = enabled
        self._notify_listeners()

    def set_restart_count(self, value: int) -> None:
        """Set restart count (used by RestoreEntity)."""
        self._restart_count = value

    def register_listener(self, listener: callback) -> None:
        """Register a listener for state updates."""
        self._listeners.append(listener)

    def remove_listener(self, listener: callback) -> None:
        """Remove a listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        """Notify all registered listeners of state change."""
        for listener in self._listeners:
            listener()

    async def async_start(self) -> None:
        """Start periodic connectivity checks."""
        self._unsub_timer = async_track_time_interval(
            self.hass,
            self._async_check,
            timedelta(seconds=self.check_interval),
        )
        # Run first check immediately
        self.hass.async_create_task(self._async_check())
        log.info(
            "Connection Watchdog started (interval=%ds, threshold=%d, cooldown=%ds)",
            self.check_interval, self.failure_threshold, self.cooldown,
        )

    async def async_stop(self) -> None:
        """Stop periodic checks."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        log.info("Connection Watchdog stopped")

    async def _async_check(self, now=None) -> None:
        """Check connectivity and trigger restart if needed."""
        # Skip checks during cooldown
        if self._in_cooldown:
            if self._cooldown_until and dt_util.utcnow() < self._cooldown_until:
                log.debug("In cooldown until %s, skipping check", self._cooldown_until)
                return
            self._in_cooldown = False
            self._cooldown_until = None
            log.info("Cooldown ended, resuming checks")

        # Check internet via TCP to DNS servers
        results = await asyncio.gather(
            *[_check_tcp(host, port) for host, port in INTERNET_CHECK_TARGETS]
        )
        internet_ok = any(results)

        # Check FritzBox URL
        fritzbox_ok = True
        if self.fritzbox_url:
            fritzbox_ok = await _check_url(self.fritzbox_url)

        self._internet_connected = internet_ok
        self._fritzbox_reachable = fritzbox_ok

        if internet_ok:
            if self._consecutive_failures > 0:
                log.info("Internet connection restored after %d failures", self._consecutive_failures)
            self._consecutive_failures = 0
            self._consecutive_restarts = 0
        else:
            self._consecutive_failures += 1
            log.warning(
                "Connectivity check failed (%d/%d) — Internet: %s, FritzBox: %s",
                self._consecutive_failures, self.failure_threshold,
                "OK" if internet_ok else "FAIL",
                "OK" if fritzbox_ok else "FAIL",
            )

            # Trigger restart if threshold reached
            if (
                self._auto_restart_enabled
                and self._consecutive_failures >= self.failure_threshold
                and self._consecutive_restarts < self.max_restarts
            ):
                await self.async_trigger_restart()

            elif self._consecutive_restarts >= self.max_restarts:
                if self._consecutive_failures == self.failure_threshold:
                    log.warning(
                        "Max restarts (%d) reached — stopping auto-restart until connection recovers",
                        self.max_restarts,
                    )

        self._notify_listeners()

    async def async_trigger_restart(self) -> None:
        """Trigger FritzBox restart by turning off the Shelly switch."""
        if not self.switch_entity:
            log.error("No switch entity configured — cannot trigger restart")
            return

        log.warning("Triggering FritzBox restart via %s", self.switch_entity)

        try:
            await self.hass.services.async_call(
                "switch", "turn_off",
                {"entity_id": self.switch_entity},
                blocking=True,
            )
        except Exception:
            log.exception("Failed to turn off switch %s", self.switch_entity)
            return

        self._restart_count += 1
        self._consecutive_restarts += 1
        self._last_restart = dt_util.now()
        self._consecutive_failures = 0

        # Enter cooldown
        self._in_cooldown = True
        self._cooldown_until = dt_util.utcnow() + timedelta(seconds=self.cooldown)

        log.warning(
            "FritzBox restart #%d triggered — cooldown %ds",
            self._restart_count, self.cooldown,
        )
        self._notify_listeners()
