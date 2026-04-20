from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PointOnlineApi, PointOnlineAuthError, PointOnlineApiError
from .const import (
    CONF_BASE_URL,
    CONF_LOGIN,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class PointOnlineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_LOGIN])
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = PointOnlineApi(
                session=session,
                base_url=user_input[CONF_BASE_URL],
                login=user_input[CONF_LOGIN],
                password=user_input[CONF_PASSWORD],
            )

            try:
                data = await api.async_test_auth()
            except PointOnlineAuthError as err:
                _LOGGER.warning("Point Online auth error during config flow: %s", err)
                errors["base"] = "invalid_auth"
            except PointOnlineApiError as err:
                _LOGGER.warning("Point Online API error during config flow: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Point Online unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                title = f"Point Online ({data.get('login')})"
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_LOGIN): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=DEFAULT_SCAN_INTERVAL,
                ): vol.All(int, vol.Range(min=5, max=1440)),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PointOnlineOptionsFlow()


class PointOnlineOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL,
                        self.config_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ),
                ): vol.All(int, vol.Range(min=5, max=1440)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)