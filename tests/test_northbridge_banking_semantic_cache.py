from types import SimpleNamespace

import pytest

from backend.app.core.domain_loader import load_domain
from backend.app.request_context import request_context_scope
from backend.app.semantic_cache import SemanticCacheService

NORTHBRIDGE_BANKING_DOMAIN = load_domain("northbridge-banking")


class FakeSnapshot:
    def __init__(self, messages):
        self.values = {"messages": messages}


class FakeAgent:
    def __init__(self, messages=None):
        self._messages = messages or []
        self.updated = None

    async def aget_state(self, config):
        del config
        return FakeSnapshot(self._messages)

    async def aupdate_state(self, config, values, as_node=None, task_id=None):
        del as_node, task_id
        self.updated = (config, values)
        return config


class FakeSettings:
    openai_chat_model = "gpt-4o"
    semantic_cache_embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    redis_host = "localhost"
    redis_port = 6379
    redis_username = "default"
    redis_password = ""
    redis_db = 0
    redis_ssl = False


def test_northbridge_demo_users_include_shared_group() -> None:
    users = NORTHBRIDGE_BANKING_DOMAIN.get_demo_users()
    plus_en = [user for user in users if user.cache_group_id == "plus_en"]
    assert len(plus_en) == 2


def test_northbridge_identity_uses_request_scoped_demo_user() -> None:
    demo_user = NORTHBRIDGE_BANKING_DOMAIN.resolve_demo_user("NBCUST_002")
    with request_context_scope(demo_user_id="NBCUST_002", demo_user=demo_user):
        result = NORTHBRIDGE_BANKING_DOMAIN.execute_internal_tool(
            NORTHBRIDGE_BANKING_DOMAIN.manifest.identity.tool_name,
            {},
            settings=SimpleNamespace(openai_api_key=""),
        )
    assert result["customer_id"] == "NBCUST_002"
    assert result["customer_segment"] == "Plus"
    assert result["cache_group_id"] == "plus_en"


def test_northbridge_submit_card_recovery_selection_validates_inputs() -> None:
    result = NORTHBRIDGE_BANKING_DOMAIN.execute_internal_tool(
        "submit_card_recovery_selection",
        {
            "account_id": "ACC_001",
            "selected_option_code": "UNFREEZE_AFTER_VERIFICATION",
            "confirm_change": True,
        },
        settings=None,
    )
    assert result["status"] == "confirmed"
    assert result["to_option_code"] == "UNFREEZE_AFTER_VERIFICATION"

    plain_language = NORTHBRIDGE_BANKING_DOMAIN.execute_internal_tool(
        "submit_card_recovery_selection",
        {
            "account_id": "ACC_001",
            "selected_option_code": "Unfreeze after verification",
            "confirm_change": True,
        },
        settings=None,
    )
    assert plain_language["status"] == "confirmed"
    assert plain_language["to_option_code"] == "UNFREEZE_AFTER_VERIFICATION"

    invalid = NORTHBRIDGE_BANKING_DOMAIN.execute_internal_tool(
        "submit_card_recovery_selection",
        {
            "account_id": "ACC_003",
            "selected_option_code": "UNFREEZE_AFTER_VERIFICATION",
            "confirm_change": True,
        },
        settings=None,
    )
    assert invalid["status"] == "error"
    assert invalid["error_code"] == "CARD_RECOVERY_ACCOUNT_MISMATCH"

    wrong_customer = NORTHBRIDGE_BANKING_DOMAIN.resolve_demo_user("NBCUST_002")
    with request_context_scope(demo_user_id="NBCUST_002", demo_user=wrong_customer):
        unauthorized = NORTHBRIDGE_BANKING_DOMAIN.execute_internal_tool(
            "submit_card_recovery_selection",
            {
                "account_id": "ACC_001",
                "selected_option_code": "UNFREEZE_AFTER_VERIFICATION",
                "confirm_change": True,
            },
            settings=None,
        )
    assert unauthorized["status"] == "error"
    assert unauthorized["error_code"] == "CARD_RECOVERY_ACCOUNT_MISMATCH"


def test_semantic_cache_service_classifies_northbridge_tools() -> None:
    service = SemanticCacheService(FakeSettings(), NORTHBRIDGE_BANKING_DOMAIN)
    assert service.classify_mcp_tool("search_supportguidancedoc_by_text") == "public"
    assert service.classify_mcp_tool("filter_servicestatus_by_service_name") == "public"
    assert service.classify_mcp_tool("filter_customerprofile_by_customer_id") == "non-cacheable"
    assert service.classify_mcp_tool("filter_depositaccount_by_customer_id") == "non-cacheable"
    assert service.classify_mcp_tool("some_unknown_tool") == "ignored"


@pytest.mark.asyncio
async def test_semantic_cache_service_thread_helpers() -> None:
    service = SemanticCacheService(FakeSettings(), NORTHBRIDGE_BANKING_DOMAIN)
    fresh_agent = FakeAgent(messages=[])
    used_agent = FakeAgent(messages=["prior"])
    config = {"configurable": {"thread_id": "demo"}}

    assert await service.thread_is_fresh(fresh_agent, config) is True
    assert await service.thread_is_fresh(used_agent, config) is False

    persisted = await service.persist_cached_turn(
        agent=fresh_agent,
        config=config,
        question="How do card controls work in the Northbridge app?",
        answer="In the Northbridge app, customers can review card controls and freeze or unfreeze an eligible card.",
    )
    assert persisted is True
    assert fresh_agent.updated is not None
