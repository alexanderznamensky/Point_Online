from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PointOnlineApi, PointOnlineAuthError, PointOnlineApiError
from .const import CONF_BASE_URL, CONF_LOGIN, CONF_PASSWORD, CONF_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PointOnlineCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.api = PointOnlineApi(
            session=async_get_clientsession(hass),
            base_url=entry.data[CONF_BASE_URL],
            login=entry.data[CONF_LOGIN],
            password=entry.data[CONF_PASSWORD],
        )

        update_minutes = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data[CONF_SCAN_INTERVAL],
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_minutes),
        )

    async def _async_update_data(self) -> dict:
        try:
            return await self.api.async_get_data()
        except PointOnlineAuthError as err:
            raise UpdateFailed(f"Ошибка авторизации: {err}") from err
        except PointOnlineApiError as err:
            raise UpdateFailed(f"Ошибка API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Непредвиденная ошибка: {err}") from err