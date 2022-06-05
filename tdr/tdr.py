import requests

TDR_API = "https://api.tdr.org/"


class TDR:
    def get_collateralization_ratio(self) -> float:
        data = requests.get(f"{TDR_API}/tdr/mortgage/get").json()
        return round(data["data"]["mortgage_rate"], 4)
