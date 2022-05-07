from typing import List, Optional, Union
from pydantic import BaseModel
from uuid import UUID


class Transaction(BaseModel):
    from_wallet: UUID
    from_wallet_name: str
    from_wallet_user: str
    to_wallet: Optional[UUID] = None
    to_wallet_name: Optional[str] = None
    to_wallet_user: Optional[str] = None
    whence: Optional[str] = None
    date: Optional[str] = None           # when making new transaction date is not displayed
    payment: int
    comment: Optional[str] = None


class Wallet(BaseModel):
    pk: UUID      # primary key => id of wallet
    name: str
    user: int     # user id
    balance: int


def serialize_wallet(data: Union[dict, list]) -> Union[Wallet, List[Wallet]]:
    if not isinstance(data, (dict, list)):
        raise TypeError(f"data must be dict or list, not {type(data)}")
    if isinstance(data, dict):
        return Wallet(**data)
    if isinstance(data, list):
        return [Wallet(**i) for i in data]


def serialize_transaction(data: Union[dict, list]) -> Union[Transaction, List[Transaction]]:
    if not isinstance(data, (dict, list)):
        raise TypeError(f"data must be dict or list, not {type(data)}")
    if isinstance(data, dict):
        return Transaction(**data)
    if isinstance(data, list):
        return [Transaction(**i) for i in data]
