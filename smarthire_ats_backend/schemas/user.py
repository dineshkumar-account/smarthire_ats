from datetime import datetime

from pydantic import BaseModel


class UserBase(BaseModel):
    # Accept "username-like" values (e.g. seeded default admin "admin")
    # while authentication still verifies the password + RBAC roles.
    email: str
    name: str
    role: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserMe(UserRead):
    pass
