from pydantic import BaseModel, ConfigDict, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    # Login accepts "username-or-email" to support seeded defaults like "admin".
    # Public registration remains EmailStr(candidate-only).
    email: str
    password: str


class RegisterRequest(BaseModel):
    # Public registration is candidate-only.
    # For security clarity, forbid extra fields like "role".
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str
    name: str
