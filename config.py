import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()


def load_config() -> dict:
    config_path = Path(__file__).parent / 'config.yaml'
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    def env_or(env_key: str, nested_keys: list, default=''):
        val = os.getenv(env_key)
        if val:
            return val
        obj = cfg
        for k in nested_keys:
            obj = obj.get(k, {}) if isinstance(obj, dict) else {}
        return obj if obj else default

    cfg['anthropic_api_key'] = env_or('ANTHROPIC_API_KEY', ['anthropic_api_key'])
    cfg['picovoice_access_key'] = env_or('PICOVOICE_ACCESS_KEY', ['picovoice_access_key'])
    cfg.setdefault('tesla', {})['email'] = env_or('TESLA_EMAIL', ['tesla', 'email'])
    cfg.setdefault('google', {})['credentials_file'] = env_or(
        'GOOGLE_CREDENTIALS_FILE', ['google', 'credentials_file'], 'google_credentials.json'
    )
    cfg.setdefault('apple', {})['username'] = env_or('APPLE_ID', ['apple', 'username'])
    cfg.setdefault('apple', {})['password'] = env_or('APPLE_APP_PASSWORD', ['apple', 'password'])

    return cfg
