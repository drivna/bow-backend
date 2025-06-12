from typing import Union
import bcrypt  # type: ignore


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def are_passwords_matching(password_to_check: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password_to_check.encode("utf-8"), hashed_password.encode("utf-8"))
