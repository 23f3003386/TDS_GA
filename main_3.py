import os
import yaml
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

def str_to_bool(val):
    if isinstance(val, bool): return val
    return str(val).lower() in ('true', '1', 'yes', 'on')

def cast_value(key, value):
    if key in ["port", "workers"]:
        return int(value)
    if key == "debug":
        return str_to_bool(value)
    return str(value)

@app.get("/effective-config")
def get_effective_config(set: list[str] = Query([])):
    # 1. Layer: Defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }

    # 2. Layer: YAML (config.development.yaml)
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml", "r") as f:
            yaml_config = yaml.safe_load(f) or {}
            for k, v in yaml_config.items():
                config[k] = v

    # 3. Layer: .env
    env_vars = dotenv_values(".env")
    # Alias Handling
    if "NUM_WORKERS" in env_vars:
        config["workers"] = int(env_vars["NUM_WORKERS"])
    # Generic mapping
    for k, v in env_vars.items():
        if k == "APP_LOG_LEVEL": config["log_level"] = v
        # Diğerlerini de ihtiyaca göre buraya ekleyebilirsin

    # 4. Layer: OS Environment Variables (APP_* prefix) - HIGHER PRECEDENCE
    # APP_PORT -> port, APP_WORKERS -> workers, APP_DEBUG -> debug, APP_LOG_LEVEL -> log_level, APP_API_KEY -> api_key
    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key"
    }
    for env_key, config_key in mapping.items():
        if env_key in os.environ:
            config[config_key] = cast_value(config_key, os.environ[env_key])

    # 5. Layer: CLI Overrides (Highest Precedence)
    for pair in set:
        if "=" in pair:
            key, value = pair.split("=", 1)
            config[key] = cast_value(key, value)

    # Secret Masking
    config["api_key"] = "****"

    return config
