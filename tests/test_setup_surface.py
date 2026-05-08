import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETUP_SURFACE_PATH = ROOT / "scripts" / "setup_surface.py"


def _load_setup_surface_module():
    spec = importlib.util.spec_from_file_location("test_setup_surface_module", SETUP_SURFACE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_normalize_data_model_for_api_lowercases_distance_metric():
    module = _load_setup_surface_module()

    data_model = {
        "entities": [
            {
                "name": "Guide",
                "fields": [
                    {
                        "name": "content_embedding",
                        "type": "list[float]",
                        "redis_indices": [
                            {
                                "type": "vector",
                                "distance_metric": "COSINE",
                            }
                        ],
                    }
                ],
            }
        ]
    }

    normalized = module._normalize_data_model_for_api(data_model)

    distance_metric = normalized["entities"][0]["fields"][0]["redis_indices"][0]["distance_metric"]
    assert distance_metric == "cosine"


def test_extract_connection_config_supports_snake_case_payload():
    module = _load_setup_surface_module()
    payload = {
        "data_source": {
            "connection_config": {
                "addr": "redis.example:6379",
                "username": "default",
            }
        }
    }

    config = module._extract_connection_config(payload)

    assert config == {
        "addr": "redis.example:6379",
        "username": "default",
    }


def test_surface_connection_config_mismatch_detects_stale_embedded_config():
    module = _load_setup_surface_module()

    class FakeSettings:
        redis_host = "redis.example"
        redis_port = 6379
        redis_username = "default"
        redis_password = "secret"
        redis_db = 0
        redis_ssl = True

    payload = {
        "data_source": {
            "connection_config": {
                "addr": "redis.example:6379",
                "username": "default",
                "password": "old-secret",
                "db": 0,
                "tls_enabled": True,
                "pool_size": 10,
                "min_idle_conns": 2,
            }
        }
    }

    assert module._surface_connection_config_mismatch(
        surface_payload=payload,
        settings=FakeSettings(),
    ) is True


def test_surface_data_model_mismatch_detects_stale_surface_schema():
    module = _load_setup_surface_module()

    embedded = {
        "data_model": {
            "entities": [
                {
                    "name": "Guide",
                    "fields": [
                        {
                            "name": "content_embedding",
                            "type": "list[float]",
                            "redis_indices": [{"type": "vector", "distance_metric": "COSINE"}],
                        }
                    ],
                }
            ]
        }
    }
    expected = {
        "entities": [
            {
                "name": "Guide",
                "fields": [
                    {
                        "name": "content_embedding",
                        "type": "list[float]",
                        "redis_indices": [{"type": "vector", "distance_metric": "cosine"}],
                    },
                    {
                        "name": "title",
                        "type": "str",
                        "redis_indices": [{"type": "text"}],
                    },
                ],
            }
        ]
    }

    assert module._surface_data_model_mismatch(
        surface_payload=embedded,
        expected_data_model=expected,
    ) is True
