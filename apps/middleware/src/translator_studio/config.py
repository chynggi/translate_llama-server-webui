from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "config.yaml"


class LlamaServerSettings(BaseModel):
    base_url: str = "http://127.0.0.1:8080"
    api_key: str = ""
    default_model: str = ""
    request_timeout: float = 600.0


class PathSettings(BaseModel):
    glossary_dir: Path = REPO_ROOT / "glossary"
    presets_dir: Path = REPO_ROOT / "presets"
    prompts_dir: Path = REPO_ROOT / "prompts"
    logs_dir: Path = REPO_ROOT / "logs"
    cache_dir: Path = REPO_ROOT / "cache"

    @model_validator(mode="after")
    def _resolve_relative(self) -> "PathSettings":
        for name in ("glossary_dir", "presets_dir", "prompts_dir", "logs_dir", "cache_dir"):
            value: Path = getattr(self, name)
            if not value.is_absolute():
                object.__setattr__(self, name, (REPO_ROOT / value).resolve())
        return self

    def ensure(self) -> None:
        for name in ("glossary_dir", "presets_dir", "prompts_dir", "logs_dir", "cache_dir"):
            getattr(self, name).mkdir(parents=True, exist_ok=True)


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )


class DetectorSettings(BaseModel):
    min_alias_length: int = 2
    longest_match_first: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        yaml_file=str(DEFAULT_CONFIG_PATH),
        env_prefix="TS_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    llama_server: LlamaServerSettings = Field(default_factory=LlamaServerSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    detector: DetectorSettings = Field(default_factory=DetectorSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, env_settings, YamlConfigSettingsSource(settings_cls))


def load_settings(config_path: str | Path | None = None) -> Settings:
    if config_path is not None:
        return Settings(_yaml_file=str(config_path))  # type: ignore[call-arg]
    return Settings()
