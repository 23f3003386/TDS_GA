import os
import yaml
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# .env dosyasını sisteme yükle (Böylece os.environ'da görünecekler)
load_dotenv() 

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
    if key in ["port", "workers"]: return int(value)
    if key == "debug": return str_to_bool(value)
    return str(value)

@app.get("/effective-config")
def get_effective_config(set: list[str] = Query([])):
    # 1. LAYER: Defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }

    # 2. LAYER: YAML (config.development.yaml)
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml", "r") as f:
            yaml_config = yaml.safe_load(f) or {}
            config.update(yaml_config)

    # 3. LAYER: .env File (Yüklenen değerleri kontrol et)
    # Alias Handling: .env içindeki NUM_WORKERS -> workers
    if os.getenv("NUM_WORKERS"):
        config["workers"] = int(os.getenv("NUM_WORKERS"))
    if os.getenv("APP_LOG_LEVEL"):
        config["log_level"] = os.getenv("APP_LOG_LEVEL")

    # 4. LAYER: OS Environment Variables (APP_* prefix - Higher Precedence)
    # Bu katman .env'den gelenleri ezer.
    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key"
    }
    for env_key, config_key in mapping.items():
        val = os.getenv(env_key)
        if val is not None:
            config[config_key] = cast_value(config_key, val)

    # 5. LAYER: CLI/Query Overrides (Highest Precedence)
    for pair in set:
        if "=" in pair:
            key, value = pair.split("=", 1)
            config[key] = cast_value(key, value)

    # Masking
    config["api_key"] = "****"

    return config
