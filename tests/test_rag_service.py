import asyncio
import json

from backend.app.rag_service import SimpleRAGService


class FakeEmbeddingsAPI:
    async def create(self, input, model):
        del input, model

        class EmbeddingData:
            embedding = [0.1, 0.2, 0.3]

        class Response:
            data = [EmbeddingData()]

        return Response()


class FakeChatAPI:
    async def create(self, **kwargs):
        del kwargs
        if False:
            yield None


class FakeOpenAI:
    def __init__(self):
        self.embeddings = FakeEmbeddingsAPI()
        self.chat = type("Chat", (), {"completions": FakeChatAPI()})()


class FakeContextSurfaceService:
    def __init__(self, tools=None, responses=None):
        self._tools = tools or []
        self._responses = responses or {}

    async def list_tools(self):
        return self._tools

    async def call_tool(self, tool_name, arguments):
        del arguments
        return self._responses.get(tool_name, {"results": []})


class FakeRagConfig:
    tool_name = "vector_search_research_chunks"
    status_text = "Searching research chunks…"
    generating_text = "Generating answer…"
    index_name_contains = "research_chunk"
    vector_field = "content_embedding"
    return_fields = ["chunk_text"]
    num_results = 3
    answer_system_prompt = "Answer from documents only."


class FakeManifest:
    rag = FakeRagConfig()


class FakeDomain:
    manifest = FakeManifest()


class FakeSettings:
    openai_api_key = "test"
    openai_base_url = None
    openai_embedding_model = "text-embedding-3-small"
    openai_chat_model = "gpt-4.1-mini"


class FakeTimer:
    def elapsed_ms(self):
        return 0

    def lap_ms(self):
        return 1


def collect_events(service: SimpleRAGService):
    async def _collect():
        events = []
        async for chunk in service.stream_answer("What changed?", FakeTimer()):
            events.append(json.loads(chunk[6:]))
        return events

    return asyncio.run(_collect())


def test_simple_rag_service_discovers_context_surface_vector_tool(monkeypatch):
    monkeypatch.setattr("backend.app.rag_service.get_active_domain", lambda settings: FakeDomain())
    service = SimpleRAGService(
        FakeSettings(),
        FakeContextSurfaceService(
            tools=[{"name": "search_researchchunk_by_content_embedding_similarity"}]
        ),
    )
    service.openai = FakeOpenAI()

    assert asyncio.run(service._get_vector_tool_name()) == "search_researchchunk_by_content_embedding_similarity"


def test_simple_rag_service_returns_graceful_error_when_vector_tool_missing(monkeypatch):
    monkeypatch.setattr("backend.app.rag_service.get_active_domain", lambda settings: FakeDomain())
    service = SimpleRAGService(FakeSettings(), FakeContextSurfaceService())
    service.openai = FakeOpenAI()

    events = collect_events(service)

    assert any(event["type"] == "tool-result" and "error" in event["payload"] for event in events)
    assert any(event["type"] == "text-delta" and "Simple RAG is not available" in event["delta"] for event in events)


def test_simple_rag_service_falls_back_to_text_search(monkeypatch):
    monkeypatch.setattr("backend.app.rag_service.get_active_domain", lambda settings: FakeDomain())
    service = SimpleRAGService(
        FakeSettings(),
        FakeContextSurfaceService(
            tools=[
                {"name": "search_researchchunk_by_content_embedding_similarity"},
                {"name": "search_researchchunk_by_text"},
            ],
            responses={
                "search_researchchunk_by_content_embedding_similarity": {
                    "raw_text": "Error executing tool: unsupported query type: search_vector"
                },
                "search_researchchunk_by_text": {
                    "results": [{"section_heading": "Latest updates", "ticker": "NVDA", "chunk_text": "Revenue grew strongly."}]
                },
            },
        ),
    )
    service.openai = FakeOpenAI()

    results = asyncio.run(service._search_documents("What changed?", [0.1, 0.2, 0.3]))

    assert results == [{"section_heading": "Latest updates", "ticker": "NVDA", "chunk_text": "Revenue grew strongly."}]
