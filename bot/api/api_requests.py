from requests.adapters import HTTPAdapter
from typing import Optional, Tuple, List, Union
from settings import get_api_settings
from schemas.models import (Transaction, serialize_transaction,
                                Wallet, serialize_wallet)
from uuid import UUID
import requests


class DefaultAPIRequest:
    def __init__(self) -> None:
        config = get_api_settings()
        self.default_url = f"http://{config.host}:{config.port}/api/v1/"
        self.session = requests.session()
        self.session.mount("http://", HTTPAdapter(max_retries=5))


class UserAPIRequest(DefaultAPIRequest):
    def __init__(self) -> None:
        super().__init__()
        self.users_url = self.default_url + "users/"

    def get_user(self, user_id: int) -> Tuple[dict, int]:
        request = self.session.get(self.users_url + f"?vk_id={user_id}")
        return request.json()[0], request.status_code

    def get_users(self) -> Tuple[List[dict], int]:
        request = self.session.get(self.users_url)
        return request.json(), request.status_code

    def create_user(self, user_id: int, name: str) -> Tuple[dict, int]:
        data = {"vk_id": user_id, "user": name}
        request = self.session.post(self.users_url, data = data)
        return request.json(), request.status_code


class WalletAPIRequest(UserAPIRequest):
    def __init__(self) -> None:
        super().__init__()
        self.wallets_url = self.default_url + "wallets/"

    def get_user_wallets(self, user_id: int) -> Tuple[Union[List[Wallet], dict], int]:
        real_id  = self.get_user(user_id)[0]["id"]
        request = self.session.get(self.wallets_url + f"?user={real_id}")
        if request.status_code != 200:
            return request.json(), request.status_code
        return serialize_wallet(request.json()), request.status_code

    def create_new_wallet(self, user_id: int, wallet_name: str) -> Tuple[Union[Wallet, dict], int]:
        real_id  = self.get_user(user_id)[0]["id"]
        data = {
            "user": real_id,
            "name": wallet_name
        }
        request = self.session.post(self.wallets_url, data=data)
        if request.status_code != 201:
            return request.json(), request.status_code
        return serialize_wallet(request.json()), request.status_code

    def edit_user_wallet(
        self,
        wallet: UUID,
        new_name: str,
        user_id: int
    ) -> Tuple[Union[Wallet, dict], int]:
        real_id  = self.get_user(user_id)[0]["id"]
        data = {
            "name": new_name,
            "user": real_id
        }
        request = self.session.put(self.wallets_url + f"{wallet}/", data=data)
        if request.status_code != 200:
            return request.json(), request.status_code
        return serialize_wallet(request.json()), request.status_code

    def delete_wallet(self, wallet: UUID) -> int:
        request = self.session.delete(self.wallets_url + f"{wallet}/")
        return request.status_code

class TransactionsAPIRequest(UserAPIRequest):
    def __init__(self) -> None:
        super().__init__()
        self.transactions_api = self.default_url + "transactions/"

    def make_transaction(
        self,
        from_wallet: UUID,
        payment: int,
        to_wallet: UUID = None,
        whence: str = None,
        comment: Optional[str] = None,
        *args, **kwargs
    ) -> Tuple[Union[Transaction, dict], int]:
        if (to_wallet and whence) or (to_wallet is None and whence is None):
            raise TypeError("One of fields 'from_wallet' or 'whence' must have a value, neither both nor none of them.")
        data = {
            "from_wallet": from_wallet,
            "to_wallet": to_wallet,
            "whence": whence,
            "payment": payment,
            "comment": comment,
        }
        request = self.session.post(self.transactions_api, data=data)
        if request.status_code == 400:
            return request.json(), request.status_code
        return serialize_transaction(request.json()), request.status_code

    def get_user_transactions(self, user_id: int, limit: int=5, incoming=False) -> Tuple[Transaction, int]:
        real_id  = self.get_user(user_id)[0]["id"]
        if not incoming:
            request = self.session.get(self.transactions_api + f"?from_user={real_id}")
        else:
            request = self.session.get(self.transactions_api + f"?to_user={real_id}")
        return serialize_transaction(request.json())[:limit], request.status_code
