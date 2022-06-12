import requests
import re

JUSTLEND_API = "https://labc.ablesdxd.link/justlend/"

# TODO : ラッパー / Wrapper


class JustLend:
    def __init__(self, addr):
        self._addr = addr
        self._yieldinfos = requests.get(
            f"{JUSTLEND_API}yieldInfos?addr={self._addr}"
        ).json()

    def update_yieldinfos(self):
        self._yieldinfos = requests.get(
            f"{JUSTLEND_API}yieldInfos?addr={self._addr}"
        ).json()

    # デバッグ用 / For debugging.
    def get_yieldinfos(self) -> list[tuple]:
        return self._yieldinfos

    def get_deposit_and_borrow(self) -> float:
        self.update_yieldinfos()

        al = self._yieldinfos["data"]["assetList"]
        fixed_deposit, fixed_borrow = 0.0, 0.0

        for asset in al:
            if "account_entered" in asset:
                if asset["account_entered"] == 1:
                    # 預入
                    if "account_depositJtoken" in asset:
                        if int(asset["account_depositJtoken"]) > 0:
                            decimal = int(asset["jtokenDecimal"])+2 # ???
                            deposit = int(asset["account_depositJtoken"]) / 10**decimal
                            exchange_rate = asset["exchangeRate"]
                            if "e" in str(exchange_rate):
                                exchange_rate = exchange_rate * re.search(r"[^/e+{2}]+", str(exchange_rate)).group(0)
                            else:
                                exchange_rate = int(str(exchange_rate)[:7])
                                exchange_rate = exchange_rate / 10 ** (len(str(exchange_rate))-1)
                            fixed_deposit += (float(deposit) * exchange_rate)
                    # 借入
                    if "account_borrowBalance" in asset:
                        if int(asset["account_borrowBalance"]) > 0:
                            decimal = int(asset["collateralDecimal"])
                            borrow = int(asset["account_borrowBalance"]) / 10**decimal
                            exchange_rate = asset["exchangeRate"]
                            if "e" in str(exchange_rate):
                                exchange_rate = exchange_rate * re.search(r"[^/e+{2}]+", str(exchange_rate)).group(0)
                            else:
                                exchange_rate = int(str(exchange_rate)[:7])
                                exchange_rate = exchange_rate / 10 ** (len(str(exchange_rate))-1)
                            fixed_borrow += (float(borrow) * exchange_rate)
        else:
            return fixed_deposit, fixed_borrow

    def get_risk_value(self) -> float:
        deposit, borrow = self.get_deposit_and_borrow()
        if borrow <= 0:
            return 0.000
        """
        Total Borrow / Borrow Limit * 100
        It's equal to
        Total Borrow / (Total Supply * Collateral Factor)
        """
        risk_value = round(borrow / (deposit * 0.85), 4)
        return risk_value