from abc import abstractmethod
from datetime import datetime
import hashlib
from typing import Any, Dict, List
from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column


def get_delimiter() -> str:
    return "|"


def calculate_sha256_hash_first_ten(input_string: str) -> str:
    # Create a new SHA-256 hash object
    sha256_hash = hashlib.sha256()

    # Update the hash object with the input string
    sha256_hash.update(input_string.encode("utf-8"))

    # Get the hexadecimal representation of the hash
    hashed_string: str = sha256_hash.hexdigest()

    return hashed_string[0:10]


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column("CREATED_AT", DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column("UPDATED_AT", DateTime, nullable=False)

    meta_data: Mapped[Dict[Any, Any]] = mapped_column("METADATA", JSON, nullable=False, default={})

    # this column is used to handle optimistic locking
    # if the current version does not match the version in the object that was read
    # then the update fails

    @abstractmethod
    def token(self) -> str:
        pass

    @abstractmethod
    def get_identifiers(self) -> List[Any]:
        pass

    def compute_and_get_id(self) -> str:
        identifier_string: str = ""
        for identifier in self.get_identifiers():
            identifier_string += str(identifier) + get_delimiter()

        return self.token() + "_" + calculate_sha256_hash_first_ten(identifier_string)
