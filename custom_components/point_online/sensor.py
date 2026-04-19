from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="balance",
        name="Баланс",
        icon="mdi:cash",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="RUB",
    ),
    SensorEntityDescription(
        key="status",
        name="Статус",
        icon="mdi:lan-connect",
    ),
    SensorEntityDescription(
        key="tariff",
        name="Тариф",
        icon="mdi:wan",
    ),
    SensorEntityDescription(
        key="monthly_payment",
        name="Ежемесячный платёж",
        icon="mdi:credit-card",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="RUB",
    ),
    SensorEntityDescription(
        key="due_date",
        name="Дата оплаты",
        icon="mdi:calendar",
        device_class=SensorDeviceClass.DATE,
    ),
    SensorEntityDescription(
        key="last_payment_amount",
        name="Последняя оплата",
        icon="mdi:bank-check",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="RUB",
    ),
    SensorEntityDescription(
        key="last_charge_amount",
        name="Последнее списание",
        icon="mdi:cash-minus",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="RUB",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PointOnlineSensor(coordinator, entry, description)
        for description in SENSORS
    )


class PointOnlineSensor(CoordinatorEntity, SensorEntity):
    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_has_entity_name = True

    @property
    def unique_id(self) -> str:
        login = self.coordinator.data.get("login", self._entry.unique_id or "unknown")
        return f"point_online_{login}_{self.entity_description.key}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def device_info(self) -> DeviceInfo:
        login = self.coordinator.data.get("login", "unknown")
        account_id = self.coordinator.data.get("account_id", "unknown")

        return DeviceInfo(
            identifiers={(DOMAIN, f"{login}_{account_id}")},
            name="Point Online",
            manufacturer="Point Online",
            model="Личный кабинет",
        )

    @property
    def extra_state_attributes(self):
        return {
            "login": self.coordinator.data.get("login"),
            "full_name": self.coordinator.data.get("full_name"),
            "actual_address": self.coordinator.data.get("actual_address"),
            "mobile_telephone": self.coordinator.data.get("mobile_telephone"),
            "email": self.coordinator.data.get("email"),
            "account_id": self.coordinator.data.get("account_id"),
            "service_name": self.coordinator.data.get("service_name"),
            "current_tariff_comment": self.coordinator.data.get("current_tariff_comment"),
            "next_tariff_comment": self.coordinator.data.get("next_tariff_comment"),
            "int_status": self.coordinator.data.get("int_status"),
            "external_id": self.coordinator.data.get("external_id"),
            "payments_total_count": self.coordinator.data.get("payments_total_count"),
            "positive_payments_count": self.coordinator.data.get("positive_payments_count"),
            "negative_charges_count": self.coordinator.data.get("negative_charges_count"),
            "last_payment_date": self.coordinator.data.get("last_payment_date"),
            "last_payment_amount": self.coordinator.data.get("last_payment_amount"),
            "last_payment_event": self.coordinator.data.get("last_payment_event"),
            "previous_payment_date": self.coordinator.data.get("previous_payment_date"),
            "previous_payment_amount": self.coordinator.data.get("previous_payment_amount"),
            "previous_payment_event": self.coordinator.data.get("previous_payment_event"),
            "last_charge_date": self.coordinator.data.get("last_charge_date"),
            "last_charge_amount": self.coordinator.data.get("last_charge_amount"),
            "last_charge_event": self.coordinator.data.get("last_charge_event"),
            "previous_charge_date": self.coordinator.data.get("previous_charge_date"),
            "previous_charge_amount": self.coordinator.data.get("previous_charge_amount"),
            "previous_charge_event": self.coordinator.data.get("previous_charge_event"),
            "avg_payment_amount": self.coordinator.data.get("avg_payment_amount"),
            "avg_charge_amount": self.coordinator.data.get("avg_charge_amount"),
        }