from __future__ import annotations

from datetime import date, datetime

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
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
        native_unit_of_measurement="RUB",
        state_class=SensorStateClass.MEASUREMENT,
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
        native_unit_of_measurement="RUB",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="due_date",
        name="Дата оплаты",
        icon="mdi:calendar",
    ),
    SensorEntityDescription(
        key="last_payment_amount",
        name="Последняя оплата",
        icon="mdi:bank-check",
        native_unit_of_measurement="RUB",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="last_charge_amount",
        name="Последнее списание",
        icon="mdi:cash-minus",
        native_unit_of_measurement="RUB",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


def day(num_days: int) -> str:
    num_days = abs(num_days)
    last_two = num_days % 100
    last_one = num_days % 10

    if 11 <= last_two <= 14:
        return "дней"
    if last_one == 1:
        return "день"
    if last_one in (2, 3, 4):
        return "дня"
    return "дней"


def time_to_pay(due_date: str) -> tuple[str | None, int | None]:
    if not due_date:
        return None, None

    parsed_date = None

    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            parsed_date = datetime.strptime(due_date, fmt)
            break
        except ValueError:
            continue

    if parsed_date is None:
        try:
            parsed_date = datetime.fromisoformat(due_date)
        except ValueError:
            return None, None

    today = datetime.now().date()
    num_days = (parsed_date.date() - today).days
    days = day(num_days)

    if num_days == 0:
        msg = "Сегодня срок оплаты Point Online!"
    elif 0 < num_days <= 5:
        msg = f"Через {num_days} {days} нужно оплатить Point Online!"
    elif num_days < 0:
        msg = "Просрочена оплата Point Online!!!"
    else:
        msg = f"Все в порядке!\nОплачивать Point Online нужно через {num_days} {days}."

    return msg, num_days


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
        login = None
        if self.coordinator.data:
            login = self.coordinator.data.get("login")
        login = login or self._entry.unique_id or "unknown"
        return f"point_online_{login}_{self.entity_description.key}"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self.entity_description.key)

        if value is None:
            return None

        if self.entity_description.key in (
            "balance",
            "monthly_payment",
            "last_payment_amount",
            "last_charge_amount",
        ):
            return float(f"{float(value):.2f}")

        return value

    @property
    def state(self):
        if self.entity_description.key != "due_date":
            return super().state

        value = self.native_value

        if value is None:
            return None

        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y")

        if isinstance(value, date):
            return value.strftime("%d.%m.%Y")

        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").strftime("%d.%m.%Y")
            except ValueError:
                try:
                    return datetime.fromisoformat(value).strftime("%d.%m.%Y")
                except ValueError:
                    return value

        return str(value)

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

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}

        attrs = {
            "last_update": data.get("last_update"),
            "execution_seconds": data.get("execution_seconds"),
            "login": data.get("login"),
            "full_name": data.get("full_name"),
            "actual_address": data.get("actual_address"),
            "mobile_telephone": data.get("mobile_telephone"),
            "email": data.get("email"),
            "account_id": data.get("account_id"),
            "service_name": data.get("service_name"),
            "current_tariff_comment": data.get("current_tariff_comment"),
            "next_tariff_comment": data.get("next_tariff_comment"),
            "int_status": data.get("int_status"),
            "external_id": data.get("external_id"),
            "payments_total_count": data.get("payments_total_count"),
            "positive_payments_count": data.get("positive_payments_count"),
            "negative_charges_count": data.get("negative_charges_count"),
            "due_date_raw": data.get("due_date"),
            "last_payment_date": data.get("last_payment_date"),
            "last_payment_amount": data.get("last_payment_amount"),
            "last_payment_event": data.get("last_payment_event"),
            "previous_payment_date": data.get("previous_payment_date"),
            "previous_payment_amount": data.get("previous_payment_amount"),
            "previous_payment_event": data.get("previous_payment_event"),
            "last_charge_date": data.get("last_charge_date"),
            "last_charge_amount": data.get("last_charge_amount"),
            "last_charge_event": data.get("last_charge_event"),
            "previous_charge_date": data.get("previous_charge_date"),
            "previous_charge_amount": data.get("previous_charge_amount"),
            "previous_charge_event": data.get("previous_charge_event"),
            "avg_payment_amount": data.get("avg_payment_amount"),
            "avg_charge_amount": data.get("avg_charge_amount"),
        }

        if self.entity_description.key == "balance":
            due_date = data.get("due_date")
            message, days_left = time_to_pay(str(due_date) if due_date else "")
            attrs["days_left"] = days_left
            attrs["message"] = message

        return attrs