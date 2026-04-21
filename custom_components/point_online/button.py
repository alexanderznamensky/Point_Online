from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PointOnlineCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PointOnlineCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PointOnlineRefreshButton(coordinator, entry)])


class PointOnlineRefreshButton(CoordinatorEntity[PointOnlineCoordinator], ButtonEntity):
    _attr_icon = "mdi:refresh"
    _attr_name = "Обновить данные"

    def __init__(self, coordinator: PointOnlineCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh"

    @property
    def device_info(self) -> DeviceInfo:
        login = (
            self.coordinator.data.get("login", "unknown")
            if self.coordinator.data
            else "unknown"
        )
        account_id = (
            self.coordinator.data.get("account_id", "unknown")
            if self.coordinator.data
            else "unknown"
        )

        return DeviceInfo(
            identifiers={(DOMAIN, f"{login}_{account_id}")},
            name="Point Online",
            manufacturer="Point Online",
            model="Личный кабинет",
        )

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()