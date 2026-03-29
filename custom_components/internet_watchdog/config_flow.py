"""Config flow for Internet Watchdog."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_FRITZBOX_IP,
    CONF_SWITCH_ENTITY,
    CONF_CHECK_INTERVAL,
    CONF_FAILURE_THRESHOLD,
    CONF_COOLDOWN,
    CONF_MAX_RESTARTS,
    CONF_RETRY_PAUSE,
    DEFAULT_FRITZBOX_IP,
    DEFAULT_CHECK_INTERVAL,
    DEFAULT_FAILURE_THRESHOLD,
    DEFAULT_COOLDOWN,
    DEFAULT_MAX_RESTARTS,
    DEFAULT_RETRY_PAUSE,
)


class InternetWatchdogConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Internet Watchdog."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Internet Watchdog",
                data={},
                options={
                    CONF_FRITZBOX_IP: user_input[CONF_FRITZBOX_IP],
                    CONF_SWITCH_ENTITY: user_input[CONF_SWITCH_ENTITY],
                    CONF_CHECK_INTERVAL: user_input.get(CONF_CHECK_INTERVAL, DEFAULT_CHECK_INTERVAL),
                    CONF_FAILURE_THRESHOLD: user_input.get(CONF_FAILURE_THRESHOLD, DEFAULT_FAILURE_THRESHOLD),
                    CONF_COOLDOWN: user_input.get(CONF_COOLDOWN, DEFAULT_COOLDOWN),
                    CONF_MAX_RESTARTS: user_input.get(CONF_MAX_RESTARTS, DEFAULT_MAX_RESTARTS),
                    CONF_RETRY_PAUSE: user_input.get(CONF_RETRY_PAUSE, DEFAULT_RETRY_PAUSE),
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_FRITZBOX_IP, default=DEFAULT_FRITZBOX_IP): str,
                vol.Required(CONF_SWITCH_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="switch"),
                ),
                vol.Optional(CONF_CHECK_INTERVAL, default=DEFAULT_CHECK_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=600),
                ),
                vol.Optional(CONF_FAILURE_THRESHOLD, default=DEFAULT_FAILURE_THRESHOLD): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=20),
                ),
                vol.Optional(CONF_COOLDOWN, default=DEFAULT_COOLDOWN): vol.All(
                    vol.Coerce(int), vol.Range(min=60, max=1800),
                ),
                vol.Optional(CONF_MAX_RESTARTS, default=DEFAULT_MAX_RESTARTS): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=10),
                ),
                vol.Optional(CONF_RETRY_PAUSE, default=DEFAULT_RETRY_PAUSE): vol.All(
                    vol.Coerce(int), vol.Range(min=300, max=86400),
                ),
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return InternetWatchdogOptionsFlow(config_entry)


class InternetWatchdogOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry):
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self._entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_FRITZBOX_IP,
                    default=opts.get(CONF_FRITZBOX_IP, DEFAULT_FRITZBOX_IP),
                ): str,
                vol.Required(
                    CONF_SWITCH_ENTITY,
                    default=opts.get(CONF_SWITCH_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="switch"),
                ),
                vol.Optional(
                    CONF_CHECK_INTERVAL,
                    default=opts.get(CONF_CHECK_INTERVAL, DEFAULT_CHECK_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=600)),
                vol.Optional(
                    CONF_FAILURE_THRESHOLD,
                    default=opts.get(CONF_FAILURE_THRESHOLD, DEFAULT_FAILURE_THRESHOLD),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
                vol.Optional(
                    CONF_COOLDOWN,
                    default=opts.get(CONF_COOLDOWN, DEFAULT_COOLDOWN),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=1800)),
                vol.Optional(
                    CONF_MAX_RESTARTS,
                    default=opts.get(CONF_MAX_RESTARTS, DEFAULT_MAX_RESTARTS),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
                vol.Optional(
                    CONF_RETRY_PAUSE,
                    default=opts.get(CONF_RETRY_PAUSE, DEFAULT_RETRY_PAUSE),
                ): vol.All(vol.Coerce(int), vol.Range(min=300, max=86400)),
            }),
        )
