import requests

TDR_API = "https://api.tdr.org/"


class TDR:
    def get_collateralization_ratio(self) -> float:
        resp = requests.get(f"{TDR_API}/tdr/mortgage/get").json()
        return round(resp["data"]["mortgage_rate"], 4)

    def get_reserve(self):
        resp = requests.get(f"{TDR_API}/tdr/reserve/get").json()
        return resp["data"]

    def get_reserves_amount(self):
        resp = requests.get(f"{TDR_API}/tdr/reserves/amount/get").json()
        return resp["data"]

    def get_actual_cr(self):
        reserves = round(float(self.get_reserve()["usd"]))
        total_usdd_supply = round(
            float(self.get_reserves_amount()["total_value_usd"])
        )
        return (total_usdd_supply / reserves)
