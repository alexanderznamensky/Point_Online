from __future__ import annotations

from datetime import date, datetime
import aiohttp


class PointOnlineApiError(Exception):
    """Base API error."""


class PointOnlineAuthError(PointOnlineApiError):
    """Auth error."""


class PointOnlineApi:
    def __init__(self, session: aiohttp.ClientSession, base_url: str, login: str, password: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._login = login
        self._password = password
        self._is_logged_in = False

        self._login_settings_url = f"{self._base_url}/customer_api/login_settings"
        self._login_url = f"{self._base_url}/customer_api/login"
        self._profile_url = f"{self._base_url}/customer_api/auth/profile"
        self._statistics_url = f"{self._base_url}/customer_api/auth/statistics"

        self._headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0",
            "Referer": f"{self._base_url}/",
            "Origin": self._base_url,
        }

    async def _request_json(self, method: str, url: str, **kwargs):
        async with self._session.request(method, url, headers=self._headers, **kwargs) as resp:
            if resp.status == 401:
                raise PointOnlineAuthError("Unauthorized")
            if resp.status >= 400:
                raise PointOnlineApiError(f"HTTP {resp.status} for {url}")

            content_type = resp.headers.get("Content-Type", "")
            if "application/json" not in content_type and "text/plain" not in content_type:
                text = await resp.text()
                raise PointOnlineApiError(
                    f"Unexpected content type: {content_type}, body={text[:300]}"
                )

            return await resp.json(content_type=None)

    async def login(self, force: bool = False) -> None:
        if self._is_logged_in and not force:
            return

        await self._request_json("GET", self._login_settings_url)

        data = await self._request_json(
            "POST",
            self._login_url,
            json={
                "login": self._login,
                "password": self._password,
            },
        )

        sid_customer = self._session.cookie_jar.filter_cookies(self._base_url).get("sid_customer")
        if not sid_customer and not data.get("sid_customer"):
            raise PointOnlineAuthError("sid_customer not received after login")

        self._is_logged_in = True

    async def fetch_profile(self) -> dict:
        return await self._request_json("GET", self._profile_url)

    async def fetch_statistics(self) -> list:
        return await self._request_json("GET", self._statistics_url)

    async def async_test_auth(self) -> dict:
        await self.login()
        return await self.fetch_profile()

    async def async_get_data(self) -> dict:
        await self.login()

        try:
            profile = await self.fetch_profile()
            statistics = await self.fetch_statistics()
        except PointOnlineAuthError:
            await self.login(force=True)
            profile = await self.fetch_profile()
            statistics = await self.fetch_statistics()

        return self._build_result(profile, statistics)

    @staticmethod
    def _ts_to_datetime_str(ts: int | None) -> str | None:
        if not ts:
            return None
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _ts_to_date(ts: int | None) -> date | None:
        if not ts:
            return None
        return datetime.fromtimestamp(ts).date()

    @staticmethod
    def _parse_amount(value) -> float | None:
        try:
            return float(str(value).replace(",", "."))
        except Exception:
            return None

    def _build_payment_diagnostics(self, statistics: list) -> dict:
        normalized = []

        for item in statistics:
            amount = self._parse_amount(item.get("payment_incurrency"))
            actual_date = item.get("actual_date")
            event_name = item.get("event_name")
            date_obj = self._ts_to_date(actual_date)

            if amount is None:
                continue

            normalized.append(
                {
                    "account_id": item.get("account_id"),
                    "event_name": event_name,
                    "actual_date": actual_date,
                    "date": self._ts_to_datetime_str(actual_date),
                    "date_only": date_obj.isoformat() if date_obj else None,
                    "amount": amount,
                    "type": "payment" if amount > 0 else "charge" if amount < 0 else "zero",
                }
            )

        normalized.sort(key=lambda x: x["actual_date"] or 0, reverse=True)

        payments = [x for x in normalized if x["amount"] > 0]
        charges = [x for x in normalized if x["amount"] < 0]

        last_payment = payments[0] if payments else None
        previous_payment = payments[1] if len(payments) > 1 else None
        last_charge = charges[0] if charges else None
        previous_charge = charges[1] if len(charges) > 1 else None

        avg_payment_amount = round(sum(x["amount"] for x in payments) / len(payments), 2) if payments else None
        avg_charge_amount = round(sum(abs(x["amount"]) for x in charges) / len(charges), 2) if charges else None

        return {
            "payments_total_count": len(normalized),
            "positive_payments_count": len(payments),
            "negative_charges_count": len(charges),
            "last_payment_date": last_payment["date"] if last_payment else None,
            "last_payment_amount": round(last_payment["amount"], 2) if last_payment else None,
            "last_payment_event": last_payment["event_name"] if last_payment else None,
            "previous_payment_date": previous_payment["date"] if previous_payment else None,
            "previous_payment_amount": round(previous_payment["amount"], 2) if previous_payment else None,
            "previous_payment_event": previous_payment["event_name"] if previous_payment else None,
            "last_charge_date": last_charge["date"] if last_charge else None,
            "last_charge_amount": round(abs(last_charge["amount"]), 2) if last_charge else None,
            "last_charge_event": last_charge["event_name"] if last_charge else None,
            "previous_charge_date": previous_charge["date"] if previous_charge else None,
            "previous_charge_amount": round(abs(previous_charge["amount"]), 2) if previous_charge else None,
            "previous_charge_event": previous_charge["event_name"] if previous_charge else None,
            "avg_payment_amount": avg_payment_amount,
            "avg_charge_amount": avg_charge_amount,
        }

    def _build_result(self, profile: dict, statistics: list) -> dict:
        balance = profile.get("balance")
        status = "active" if profile.get("is_active") else "inactive"
        monthly_payment = profile.get("payment_in_month")
        login_value = profile.get("login")
        full_name = profile.get("full_name")
        actual_address = profile.get("actual_address")
        mobile_telephone = profile.get("mobile_telephone")
        email = profile.get("email")

        tariff = None
        if profile.get("tariffs"):
            tariff = profile["tariffs"][0].get("name")

        account_id = None
        due_date = None
        service_name = None
        current_tariff_comment = None
        next_tariff_comment = None
        int_status = None
        external_id = None

        accounts = profile.get("accounts") or []
        if accounts:
            account_id = accounts[0].get("id")
            int_status = accounts[0].get("int_status")
            external_id = accounts[0].get("external_id")

            services = accounts[0].get("services") or []
            if services:
                service_name = services[0].get("name")
                due_ts = services[0].get("discount_period_end")
                due_date = self._ts_to_date(due_ts)

            account_tariffs = accounts[0].get("tariffs") or []
            if account_tariffs:
                current_tariff_comment = account_tariffs[0].get("current_tariff_comment")
                next_tariff_comment = account_tariffs[0].get("next_tariff_comment")

        result = {
            "balance": balance,
            "status": status,
            "tariff": tariff,
            "monthly_payment": monthly_payment,
            "due_date": due_date,
            "login": login_value,
            "full_name": full_name,
            "actual_address": actual_address,
            "mobile_telephone": mobile_telephone,
            "email": email,
            "account_id": account_id,
            "service_name": service_name,
            "current_tariff_comment": current_tariff_comment,
            "next_tariff_comment": next_tariff_comment,
            "int_status": int_status,
            "external_id": external_id,
        }

        result.update(self._build_payment_diagnostics(statistics))
        return result