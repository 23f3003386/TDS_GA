import os
import yaml
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values

app = FastAPI()

# Allow CORS for all origins (or restrict to your specific dev dash URL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

def str_to_bool(val):
    if isinstance(val, bool): return val
    return str(val).lower() in ('true', '1', 'yes', 'on')

@app.get("/effective-config")
def get_effective_config(set: list[str] = Query([])):
    # 1. Defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }

    # 2. config.development.yaml (Layer 2)
    try:
        with open("config.development.yaml", "r") as f:
            yaml_config = yaml.safe_load(f)
            config.update(yaml_config)
    except FileNotFoundError:
        pass

    # 3. .env file (Layer 3)
    # Using dotenv_values so we don't pollute os.environ with layer 3
    env_vars = dotenv_values(".env")
    if "NUM_WORKERS" in env_vars:
        config["workers"] = int(env_vars["NUM_WORKERS"])
    if "APP_LOG_LEVEL" in env_vars:
        config["log_level"] = env_vars["APP_LOG_LEVEL"]

    # 4. OS Env vars (Layer 4 - APP_* prefix)
    if "APP_LOG_LEVEL" in os.environ:
        config["log_level"] = os.environ["APP_LOG_LEVEL"]
    if "APP_API_KEY" in os.environ:
        config["api_key"] = os.environ["APP_API_KEY"]

    # 5. CLI Overrides / Query Parameters (Highest Precedence)
    for pair in set:
        key, value = pair.split("=", 1)
        if key in ["port", "workers"]:
            config[key] = int(value)
        elif key == "debug":
            config[key] = str_to_bool(value)
        else:
            config[key] = value

    # Masking
    config["api_key"] = "****"

    return config
