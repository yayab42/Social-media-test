from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
)
from python_usernames import is_safe_username


class RegistrationPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=3, max_length=80)
    email: EmailStr = Field(max_length=255)
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_must_be_safe(cls, value: str) -> str:
        if not is_safe_username(value, max_length=80):
            raise ValueError("username is invalid or reserved")
        return value


class LoginPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=1, max_length=80)
    password: SecretStr = Field(min_length=1, max_length=128)


class PostPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(min_length=1, max_length=5000)


def validation_details(error: ValidationError) -> dict:
    details = {}

    for item in error.errors():
        field = ".".join(str(part) for part in item["loc"])
        message = item["msg"]
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        details[field] = message

    return details
