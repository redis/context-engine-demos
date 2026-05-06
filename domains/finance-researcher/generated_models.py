"""Generated Context Retriever models for the ShiftIQ domain."""

from __future__ import annotations

from context_surfaces.context_model import ContextField, ContextModel, ContextRelationship


class AnalystProfile(ContextModel):
    """AnalystProfile entity for the ShiftIQ domain."""

    __redis_key_template__ = "finance_researcher_analyst_profile:{analyst_id}"

    analyst_id: str = ContextField(
        description="Unique analyst identifier",
        is_key_component=True,
    )

    name: str = ContextField(
        description="Analyst full name",
        index="text",
        weight=2.0,
    )

    email: str = ContextField(
        description="Analyst email",
        index="text",
        no_stem=True,
    )

    firm_name: str = ContextField(
        description="Research firm or desk",
        index="text",
    )

    role: str = ContextField(
        description="Analyst role or title",
        index="text",
    )

    watchlist_name: str = ContextField(
        description="Named watchlist used for the demo",
        index="text",
    )

    watchlist_theme: str = ContextField(
        description="Primary coverage theme",
        index="tag",
    )

    active_watchlist_count: int = ContextField(
        description="Number of companies in the active watchlist",
        index="numeric",
        sortable=True,
    )

    as_of_date: str = ContextField(
        description="ISO date for the analyst context snapshot",
    )


class Company(ContextModel):
    """Company entity for the ShiftIQ domain."""

    __redis_key_template__ = "finance_researcher_company:{company_id}"

    company_id: str = ContextField(
        description="Unique company identifier",
        is_key_component=True,
    )

    ticker: str = ContextField(
        description="Public ticker symbol",
        index="tag",
        no_stem=True,
    )

    company_name: str = ContextField(
        description="Company legal or common name",
        index="text",
        weight=2.0,
    )

    cik: str = ContextField(
        description="SEC CIK identifier",
        index="tag",
        no_stem=True,
    )

    sector: str = ContextField(
        description="GICS sector",
        index="tag",
    )

    subsector: str = ContextField(
        description="GICS subsector or business line",
        index="tag",
    )

    benchmark_group: str = ContextField(
        description="Peer benchmark group",
        index="tag",
    )

    exchange: str = ContextField(
        description="Primary listing exchange",
        index="tag",
    )

    headquarters_city: str = ContextField(
        description="Company headquarters city",
        index="tag",
    )

    headquarters_state: str = ContextField(
        description="Company headquarters state",
        index="tag",
    )

    watchlist_rank: int = ContextField(
        description="Priority rank in the analyst watchlist",
        index="numeric",
        sortable=True,
    )

    website_url: str = ContextField(
        description="Investor relations or corporate website",
        index="text",
    )

    documents: list[ResearchDocument] = ContextRelationship(
        description="Research documents for this company",
        source_field="company_id",
    )

    metrics: list[FinancialMetricPoint] = ContextRelationship(
        description="Financial metrics for this company",
        source_field="company_id",
    )

    prices: list[PriceBar] = ContextRelationship(
        description="Price history for this company",
        source_field="company_id",
    )

    events: list[CoverageEvent] = ContextRelationship(
        description="Coverage events for this company",
        source_field="company_id",
    )


class ResearchDocument(ContextModel):
    """ResearchDocument entity for the ShiftIQ domain."""

    __redis_key_template__ = "finance_researcher_research_document:{document_id}"

    document_id: str = ContextField(
        description="Unique document identifier",
        is_key_component=True,
    )

    company_id: str = ContextField(
        description="Parent company identifier",
        index="tag",
    )

    ticker: str = ContextField(
        description="Company ticker symbol",
        index="tag",
        no_stem=True,
    )

    title: str = ContextField(
        description="Document title",
        index="text",
        weight=2.0,
    )

    source_type: str = ContextField(
        description="Source type such as sec_filing, earnings_release, presentation, or remarks",
        index="tag",
    )

    document_family: str = ContextField(
        description="Normalized family label for the source document",
        index="tag",
    )

    published_at: str = ContextField(
        description="ISO timestamp when the source was published",
    )

    fiscal_period: str | None = ContextField(
        description="Fiscal period such as Q1, Q2, Q3, or FY",
        index="tag",
    )

    fiscal_year: int | None = ContextField(
        description="Fiscal year",
        index="numeric",
        sortable=True,
    )

    source_url: str = ContextField(
        description="Canonical source URL",
        index="text",
    )

    local_path: str = ContextField(
        description="Relative path to the downloaded artifact",
        index="text",
    )

    mime_type: str = ContextField(
        description="Artifact mime type",
        index="tag",
    )

    sha256: str = ContextField(
        description="SHA-256 digest of the downloaded artifact",
        index="tag",
        no_stem=True,
    )

    company: Company = ContextRelationship(
        description="Owning company",
        source_field="company_id",
    )

    chunks: list[ResearchChunk] = ContextRelationship(
        description="Text chunks derived from this document",
        source_field="document_id",
    )


class ResearchChunk(ContextModel):
    """ResearchChunk entity for the ShiftIQ domain."""

    __redis_key_template__ = "finance_researcher_research_chunk:{chunk_id}"

    chunk_id: str = ContextField(
        description="Unique chunk identifier",
        is_key_component=True,
    )

    document_id: str = ContextField(
        description="Parent research document",
        index="tag",
    )

    company_id: str = ContextField(
        description="Parent company identifier",
        index="tag",
    )

    ticker: str = ContextField(
        description="Company ticker symbol",
        index="tag",
        no_stem=True,
    )

    section_heading: str | None = ContextField(
        description="Section heading or subsection title",
        index="text",
    )

    page_label: str | None = ContextField(
        description="Page label, page number, or extracted section marker",
        index="tag",
    )

    chunk_text: str = ContextField(
        description="Normalized chunk text",
        index="text",
        weight=2.0,
    )

    content_embedding: list[float] = ContextField(
        description="Vector embedding of the chunk text",
        index="vector",
        vector_dim=1536,
        distance_metric="cosine",
    )

    document: ResearchDocument = ContextRelationship(
        description="Parent research document",
        source_field="document_id",
    )

    company: Company = ContextRelationship(
        description="Owning company",
        source_field="company_id",
    )


class FinancialMetricPoint(ContextModel):
    """FinancialMetricPoint entity for the ShiftIQ domain."""

    __redis_key_template__ = "finance_researcher_financial_metric_point:{point_id}"

    point_id: str = ContextField(
        description="Unique metric point identifier",
        is_key_component=True,
    )

    company_id: str = ContextField(
        description="Parent company identifier",
        index="tag",
    )

    ticker: str = ContextField(
        description="Company ticker symbol",
        index="tag",
        no_stem=True,
    )

    metric_name: str = ContextField(
        description="Metric name such as revenue or net_income",
        index="tag",
    )

    period_type: str = ContextField(
        description="Annual or quarterly period type",
        index="tag",
    )

    fiscal_year: int = ContextField(
        description="Fiscal year",
        index="numeric",
        sortable=True,
    )

    fiscal_period: str | None = ContextField(
        description="Fiscal period label such as Q1, Q2, Q3, Q4, or FY",
        index="tag",
    )

    period_end: str = ContextField(
        description="ISO period end date",
    )

    value: float = ContextField(
        description="Metric value",
        index="numeric",
        sortable=True,
    )

    unit: str = ContextField(
        description="Unit of measure",
        index="tag",
    )

    currency: str | None = ContextField(
        description="Currency code such as USD",
        index="tag",
    )

    company: Company = ContextRelationship(
        description="Owning company",
        source_field="company_id",
    )


class PriceBar(ContextModel):
    """PriceBar entity for the ShiftIQ domain."""

    __redis_key_template__ = "finance_researcher_price_bar:{bar_id}"

    bar_id: str = ContextField(
        description="Unique price bar identifier",
        is_key_component=True,
    )

    company_id: str = ContextField(
        description="Parent company identifier",
        index="tag",
    )

    ticker: str = ContextField(
        description="Company ticker symbol",
        index="tag",
        no_stem=True,
    )

    trade_date: str = ContextField(
        description="Trading date",
        index="tag",
    )

    open: float = ContextField(
        description="Opening price",
        index="numeric",
        sortable=True,
    )

    high: float = ContextField(
        description="High price",
        index="numeric",
        sortable=True,
    )

    low: float = ContextField(
        description="Low price",
        index="numeric",
        sortable=True,
    )

    close: float = ContextField(
        description="Close price",
        index="numeric",
        sortable=True,
    )

    adj_close: float = ContextField(
        description="Adjusted close price",
        index="numeric",
        sortable=True,
    )

    volume: int = ContextField(
        description="Trading volume",
        index="numeric",
        sortable=True,
    )

    company: Company = ContextRelationship(
        description="Owning company",
        source_field="company_id",
    )


class CoverageEvent(ContextModel):
    """CoverageEvent entity for the ShiftIQ domain."""

    __redis_key_template__ = "finance_researcher_coverage_event:{event_id}"

    event_id: str = ContextField(
        description="Unique event identifier",
        is_key_component=True,
    )

    company_id: str = ContextField(
        description="Parent company identifier",
        index="tag",
    )

    ticker: str = ContextField(
        description="Company ticker symbol",
        index="tag",
        no_stem=True,
    )

    event_family: str = ContextField(
        description="Normalized family such as filing, earnings, presentation, or price",
        index="tag",
    )

    event_type: str = ContextField(
        description="Event type such as new_filing, new_release, new_presentation, or price_move",
        index="tag",
    )

    published_at: str = ContextField(
        description="ISO timestamp of the event",
    )

    document_id: str | None = ContextField(
        description="Related research document",
        index="tag",
    )

    headline: str = ContextField(
        description="Short human-readable event headline",
        index="text",
        weight=2.0,
    )

    importance_score: float = ContextField(
        description="Relative importance score",
        index="numeric",
        sortable=True,
    )

    company: Company = ContextRelationship(
        description="Owning company",
        source_field="company_id",
    )

    document: ResearchDocument | None = ContextRelationship(
        description="Related research document",
        source_field="document_id",
    )
