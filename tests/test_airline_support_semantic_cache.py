from types import SimpleNamespace

import pytest

from backend.app.core.domain_loader import load_domain
from backend.app.request_context import request_context_scope
from backend.app.semantic_cache import SemanticCacheService

AIRLINE_SUPPORT_DOMAIN = load_domain("airline-support")


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


def test_airline_support_demo_users_include_shared_group() -> None:
    users = AIRLINE_SUPPORT_DOMAIN.get_demo_users()
    senator_en = [user for user in users if user.cache_group_id == "senator_en"]
    assert len(senator_en) == 2


def test_airline_support_identity_uses_request_scoped_demo_user() -> None:
    demo_user = AIRLINE_SUPPORT_DOMAIN.resolve_demo_user("AIRCUST_002")
    with request_context_scope(demo_user_id="AIRCUST_002", demo_user=demo_user):
        result = AIRLINE_SUPPORT_DOMAIN.execute_internal_tool(
            AIRLINE_SUPPORT_DOMAIN.manifest.identity.tool_name,
            {},
            settings=SimpleNamespace(openai_api_key=""),
        )
    assert result["customer_id"] == "AIRCUST_002"
    assert result["status_tier"] == "Senator"
    assert result["cache_group_id"] == "senator_en"


def test_semantic_cache_service_classifies_airline_tools() -> None:
    service = SemanticCacheService(FakeSettings(), AIRLINE_SUPPORT_DOMAIN)
    assert service.classify_mcp_tool("search_travelpolicydoc_by_text") == "public"
    assert service.classify_mcp_tool("filter_operatingflight_by_flight_number") == "public"
    assert service.classify_mcp_tool("filter_customerprofile_by_customer_id") == "non-cacheable"
    assert service.classify_mcp_tool("filter_booking_by_customer_id") == "non-cacheable"
    assert service.classify_mcp_tool("some_unknown_tool") == "ignored"


@pytest.mark.asyncio
async def test_semantic_cache_service_thread_helpers() -> None:
    service = SemanticCacheService(FakeSettings(), AIRLINE_SUPPORT_DOMAIN)
    fresh_agent = FakeAgent(messages=[])
    used_agent = FakeAgent(messages=["prior"])
    config = {"configurable": {"thread_id": "demo"}}

    assert await service.thread_is_fresh(fresh_agent, config) is True
    assert await service.thread_is_fresh(used_agent, config) is False

    persisted = await service.persist_cached_turn(
        agent=fresh_agent,
        config=config,
        question="When does online check-in open?",
        answer="Online check-in typically opens 23 hours before departure.",
    )
    assert persisted is True
    assert fresh_agent.updated is not None


def test_semantic_cache_service_filter_policy_allows_public_plus_group() -> None:
    service = SemanticCacheService(FakeSettings(), AIRLINE_SUPPORT_DOMAIN)
    assert service.build_filter_policy(group_id=None) == {
        "allowPublic": True,
        "groupId": None,
    }
    assert service.build_filter_policy(group_id="senator_en") == {
        "allowPublic": True,
        "groupId": "senator_en",
    }


def test_semantic_cache_service_filter_expression_scopes_reads() -> None:
    service = SemanticCacheService(FakeSettings(), AIRLINE_SUPPORT_DOMAIN)
    public_expr = service.build_read_filter_expression(group_id=None)
    group_expr = service.build_read_filter_expression(group_id="senator_en")

    public_text = str(public_expr)
    group_text = str(group_expr)
    assert "@domain_id:{airline\\-support}" in public_text
    assert "@access_class:{public}" in public_text
    assert "@access_class:{group}" not in public_text
    assert "@group_id:{senator_en}" in group_text
    assert "@access_class:{group}" in group_text
    assert "@access_class:{public}" in group_text


@pytest.mark.parametrize(
    ("flags", "expected_class", "expected_reason"),
    [
        ({"public": True, "group": False, "non_cacheable": False}, "public", "public provenance"),
        ({"public": True, "group": True, "non_cacheable": False}, "group", "group provenance"),
        ({"public": False, "group": False, "non_cacheable": True}, None, "non-cacheable provenance"),
        ({"public": False, "group": False, "non_cacheable": False}, None, "no cacheable provenance"),
    ],
)
def test_semantic_cache_service_resolves_store_access(flags, expected_class, expected_reason) -> None:
    service = SemanticCacheService(FakeSettings(), AIRLINE_SUPPORT_DOMAIN)
    resolved_class, reason = service.resolve_store_access(
        saw_public=flags["public"],
        saw_group=flags["group"],
        saw_non_cacheable=flags["non_cacheable"],
    )
    assert resolved_class == expected_class
    assert reason == expected_reason
