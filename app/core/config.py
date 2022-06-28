"""
File with environment variables and general configuration logic.
`SECRET_KEY`, `ENVIRONMENT` etc. map to env variables with the same names.

Pydantic priority ordering:

1. (Most important, will overwrite everything) - environment variables
2. `.env` file in root folder of project
3. Default values

For project name, version, description we use pyproject.toml
For the rest, we use file `.env` (gitignored), see `.env.example`

`DEFAULT_SQLALCHEMY_DATABASE_URI` and `TEST_SQLALCHEMY_DATABASE_URI`:
Both are ment to be validated at the runtime, do not change unless you know
what are you doing. All the two validators do is to build full URI (TCP protocol)
to databases to avoid typo bugs.

See https://pydantic-docs.helpmanual.io/usage/settings/
"""

from pathlib import Path
from typing import Literal, Optional, Union

import toml
from pydantic import AnyHttpUrl, AnyUrl, BaseSettings, EmailStr, validator

PROJECT_DIR = Path(__file__).parent.parent.parent
PYPROJECT_CONTENT = toml.load(f"{PROJECT_DIR}/pyproject.toml")["tool"]["poetry"]


class Settings(BaseSettings):
    # CORE SETTINGS
    SECRET_KEY: str
    ENVIRONMENT: Literal["DEV", "PYTEST", "STAGE", "STAGING", "PROD", "PRODUCTION"]
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    BACKEND_CORS_ORIGINS: Union[str, list[AnyHttpUrl]]

    # PROJECT NAME, VERSION AND DESCRIPTION
    PROJECT_NAME: str = PYPROJECT_CONTENT["name"]
    VERSION: str = PYPROJECT_CONTENT["version"]
    DESCRIPTION: str = PYPROJECT_CONTENT["description"]

    # FILE STORE PATH
    FILE_STORE: Optional[str]

    # POSTGRESQL TEST DATABASE
    TEST_DATABASE_HOSTNAME: str
    TEST_DATABASE_USER: str
    TEST_DATABASE_PASSWORD: str
    TEST_DATABASE_PORT: str
    TEST_DATABASE_DB: str
    TEST_SQLALCHEMY_DATABASE_URI: str = ""

    # POSTGRESQL DEV DATABASE
    DEV_DATABASE_HOSTNAME: str
    DEV_DATABASE_USER: str
    DEV_DATABASE_PASSWORD: str
    DEV_DATABASE_PORT: str
    DEV_DATABASE_DB: str
    DEV_SQLALCHEMY_DATABASE_URI: str = ""

    STAGING_DATABASE_HOSTNAME: str
    STAGING_DATABASE_USER: str
    STAGING_DATABASE_PASSWORD: str
    STAGING_DATABASE_PORT: str
    STAGING_DATABASE_DB: str
    STAGING_SQLALCHEMY_DATABASE_URI: str = ""

    PROD_DATABASE_HOSTNAME: str
    PROD_DATABASE_USER: str
    PROD_DATABASE_PASSWORD: str
    PROD_DATABASE_PORT: str
    PROD_DATABASE_DB: str
    PROD_SQLALCHEMY_DATABASE_URI: str = ""

    # FIRST SUPERUSER
    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # VALIDATORS
    @validator("BACKEND_CORS_ORIGINS")
    def _assemble_cors_origins(cls, cors_origins: Union[str, list[AnyHttpUrl]]):
        if isinstance(cors_origins, str):
            return [item.strip() for item in cors_origins.split(",")]
        return cors_origins

    @validator("TEST_SQLALCHEMY_DATABASE_URI")
    def _assemble_test_db_connection(cls, v: str, values: dict[str, str]) -> str:
        return AnyUrl.build(
            scheme="postgresql+asyncpg",
            user=values["TEST_DATABASE_USER"],
            password=values["TEST_DATABASE_PASSWORD"],
            host=values["TEST_DATABASE_HOSTNAME"],
            port=values["TEST_DATABASE_PORT"],
            path=f"/{values['TEST_DATABASE_DB']}",
        )

    @validator("DEV_SQLALCHEMY_DATABASE_URI")
    def _assemble_dev_db_connection(cls, v: str, values: dict[str, str]) -> str:
        return AnyUrl.build(
            scheme="postgresql+asyncpg",
            user=values.get("DEV_DATABASE_USER", ""),
            password=values.get("DEV_DATABASE_PASSWORD", ""),
            host=values.get("DEV_DATABASE_HOSTNAME", ""),
            port=values.get("DEV_DATABASE_PORT", ""),
            path=f'/{values.get("DEV_DATABASE_DB","")}',
        )

    @validator("STAGING_SQLALCHEMY_DATABASE_URI")
    def _assemble_staging_db_connection(cls, v: str, values: dict[str, str]) -> str:
        return AnyUrl.build(
            scheme="postgresql+asyncpg",
            user=values.get("STAGING_DATABASE_USER", ""),
            password=values.get("STAGING_DATABASE_PASSWORD", ""),
            host=values.get("STAGING_DATABASE_HOSTNAME", ""),
            port=values.get("STAGING_DATABASE_PORT", ""),
            path=f'/{values.get("STAGING_DATABASE_DB","")}',
        )

    @validator("PROD_SQLALCHEMY_DATABASE_URI")
    def _assemble_prod_db_connection(cls, v: str, values: dict[str, str]) -> str:
        return AnyUrl.build(
            scheme="postgresql+asyncpg",
            user=values.get("PROD_DATABASE_USER", ""),
            password=values.get("PROD_DATABASE_PASSWORD", ""),
            host=values.get("PROD_DATABASE_HOSTNAME", ""),
            port=values.get("PROD_DATABASE_PORT", ""),
            path=f'/{values.get("PROD_DATABASE_DB","")}',
        )

    class Config:
        env_file = f"{PROJECT_DIR}/.env"
        case_sensitive = True


settings: Settings = Settings()  # type: ignore
