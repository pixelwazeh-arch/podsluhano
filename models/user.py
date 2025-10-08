from dataclasses import dataclass
from typing import Optional
from enum import Enum

class UserRole(Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

@dataclass
class User:
    id: int
    username: Optional[str]
    first_name: str
    role: UserRole
    created_at: str