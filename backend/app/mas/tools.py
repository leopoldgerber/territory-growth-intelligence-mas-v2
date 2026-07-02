from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from app.analytics.channel_intelligence import get_channel_intelligence
from app.analytics.competitor_intelligence import get_competitor_intelligence
from app.analytics.country_intelligence import get_country_intelligence
from app.analytics.device_intelligence import get_device_intelligence
from app.analytics.scoring.service import list_scores, recalculate_scores
from app.analytics.signals.service import list_derived_signals, recalculate_signals
from app.core.config import Settings
from app.mas.rag_service import search_knowledge
from app.mas.schemas import (
    MasToolConfidence,
    RagSearchRequest,
    ToolContext,
    ToolInfo,
    ToolResult,
    ToolSourceRef,
)
from app.reports.budget_strategy.schemas import BudgetStrategyGenerateRequest
from app.reports.budget_strategy.service import generate_strategy
from app.schemas.analytics import OpportunityScoreRecalculateRequest, RecalculateSignalsRequest


class MasTool(Protocol):
    tool_name: str
    evidence_type: str
    source: str
    description: str

    def validate_input(self, context: ToolContext) -> list[str]:
        """Validate tool input.
        Args:
            context (ToolContext): Normalized tool context."""

    def run(self, session: Session, settings: Settings, context: ToolContext, parameters: dict[str, Any]) -> ToolResult:
        """Run MAS tool.
        Args:
            session (Session): Active database session.
            settings (Settings): Application settings.
            context (ToolContext): Normalized tool context.
            parameters (dict[str, Any]): Extra tool parameters."""

    def build_evidence(self, result: ToolResult) -> dict[str, Any]:
        """Build evidence payload.
        Args:
            result (ToolResult): Tool result."""

    def build_summary(self, data: dict[str, Any] | None) -> str:
        """Build tool summary.
        Args:
            data (dict[str, Any] | None): Tool data."""


class BaseTool:
    tool_name = 'base'
    evidence_type = 'methodology'
    source = 'system'
    description = 'Base MAS tool.'

    def validate_input(self, context: ToolContext) -> list[str]:
        """Validate tool input.
        Args:
            context (ToolContext): Normalized tool context."""
        errors: list[str] = []
        if context.date_from is None:
            errors.append('date_from is required')
        if context.date_to is None:
            errors.append('date_to is required')
        return errors

    def build_evidence(self, result: ToolResult) -> dict[str, Any]:
        """Build evidence payload.
        Args:
            result (ToolResult): Tool result."""
        return {
            'tool_name': result.tool_name,
            'status': result.status,
            'data': result.data,
            'warnings': result.warnings,
            'errors': result.errors,
            'source_refs': [source_ref.model_dump(mode='json') for source_ref in result.source_refs],
        }

    def build_summary(self, data: dict[str, Any] | None) -> str:
        """Build tool summary.
        Args:
            data (dict[str, Any] | None): Tool data."""
        if not data:
            return f'{self.tool_name} did not return usable data.'
        return f'{self.tool_name} returned structured evidence.'

    def failed_result(self, context: ToolContext, errors: list[str]) -> ToolResult:
        """Build failed result.
        Args:
            context (ToolContext): Normalized tool context.
            errors (list[str]): Validation or execution errors."""
        return ToolResult(
            tool_name=self.tool_name,
            status='failed',
            evidence_type=self.evidence_type,
            source=self.source,
            context=context,
            data=None,
            summary=self.build_summary(None),
            confidence='unknown',
            errors=errors,
            source_refs=[],
            created_at=current_time(),
        )

    def success_result(
        self,
        context: ToolContext,
        data: dict[str, Any],
        confidence: MasToolConfidence,
        source_refs: list[ToolSourceRef],
        warnings: list[str] | None = None,
    ) -> ToolResult:
        """Build success result.
        Args:
            context (ToolContext): Normalized tool context.
            data (dict[str, Any]): Tool data.
            confidence (MasToolConfidence): Evidence confidence.
            source_refs (list[ToolSourceRef]): Source references.
            warnings (list[str] | None): Tool warnings."""
        return ToolResult(
            tool_name=self.tool_name,
            status='success',
            evidence_type=self.evidence_type,
            source=self.source,
            context=context,
            data=data,
            summary=self.build_summary(data),
            confidence=confidence,
            warnings=warnings or [],
            source_refs=source_refs,
            created_at=current_time(),
        )


class CountryIntelligenceTool(BaseTool):
    tool_name = 'country_intelligence'
    evidence_type = 'country'
    source = 'analytics_db'
    description = 'Returns country-level market evidence.'

    def run(self, session: Session, settings: Settings, context: ToolContext, parameters: dict[str, Any]) -> ToolResult:
        """Run country intelligence tool.
        Args:
            session (Session): Active database session.
            settings (Settings): Application settings.
            context (ToolContext): Normalized tool context.
            parameters (dict[str, Any]): Extra tool parameters."""
        errors = self.validate_input(context)
        if errors:
            return self.failed_result(context, errors)
        response = get_country_intelligence(
            session=session,
            default_project_id=settings.default_project_id,
            project_id=project_value(context.project_id),
            date_from=context.date_from,
            date_to=context.date_to,
            country=country_value(context),
            tld=single_value(context.tld),
            company=company_value(context),
            company_domain=single_value(context.company_domain),
            competitors=list_value(context.competitors),
            competitor_domain=list_value(context.competitor_domains),
            limit=limit_value(parameters),
        )
        data = response.model_dump(mode='json')
        if response.summary.total_traffic <= 0 and response.competitor_summary.total_traffic <= 0:
            return self.failed_result(context, ['No country traffic data found for selected context'])
        return self.success_result(
            context,
            data,
            confidence_by_count(response.summary.date_count),
            traffic_refs(context),
        )

    def build_summary(self, data: dict[str, Any] | None) -> str:
        """Build tool summary.
        Args:
            data (dict[str, Any] | None): Tool data."""
        if not data:
            return 'Country Intelligence did not return usable country evidence.'
        summary = data.get('summary', {})
        competitor_summary = data.get('competitor_summary', {})
        total_traffic = int(summary.get('total_traffic') or 0)
        competitor_traffic = int(competitor_summary.get('total_traffic') or 0)
        return f'Country evidence returned {total_traffic} company visits and {competitor_traffic} competitor visits.'


class CompetitorIntelligenceTool(BaseTool):
    tool_name = 'competitor_intelligence'
    evidence_type = 'competitor'
    source = 'analytics_db'
    description = 'Returns competitor evidence for selected country and scope.'

    def run(self, session: Session, settings: Settings, context: ToolContext, parameters: dict[str, Any]) -> ToolResult:
        """Run competitor intelligence tool.
        Args:
            session (Session): Active database session.
            settings (Settings): Application settings.
            context (ToolContext): Normalized tool context.
            parameters (dict[str, Any]): Extra tool parameters."""
        errors = self.validate_input(context)
        if errors:
            return self.failed_result(context, errors)
        response = get_competitor_intelligence(
            session=session,
            default_project_id=settings.default_project_id,
            project_id=project_value(context.project_id),
            date_from=context.date_from,
            date_to=context.date_to,
            country=country_value(context),
            tld=single_value(context.tld),
            competitors=list_value(context.competitors),
            competitor_domain=list_value(context.competitor_domains),
            limit=limit_value(parameters),
        )
        data = response.model_dump(mode='json')
        if response.summary.total_traffic <= 0:
            return self.failed_result(context, ['No competitor traffic data found for selected context'])
        return self.success_result(context, data, 'high', traffic_refs(context))

    def build_summary(self, data: dict[str, Any] | None) -> str:
        """Build tool summary.
        Args:
            data (dict[str, Any] | None): Tool data."""
        if not data:
            return 'Competitor Intelligence did not return usable competitor evidence.'
        summary = data.get('summary', {})
        active_domains = int(summary.get('active_domains') or 0)
        top_country = summary.get('top_country') or 'selected market'
        return f'Competitor evidence found {active_domains} active domains, led by {top_country}.'


class ChannelIntelligenceTool(BaseTool):
    tool_name = 'channel_intelligence'
    evidence_type = 'channel'
    source = 'analytics_db'
    description = 'Returns deterministic channel evidence.'

    def run(self, session: Session, settings: Settings, context: ToolContext, parameters: dict[str, Any]) -> ToolResult:
        """Run channel intelligence tool.
        Args:
            session (Session): Active database session.
            settings (Settings): Application settings.
            context (ToolContext): Normalized tool context.
            parameters (dict[str, Any]): Extra tool parameters."""
        errors = self.validate_input(context)
        if errors:
            return self.failed_result(context, errors)
        response = get_channel_intelligence(
            session=session,
            default_project_id=settings.default_project_id,
            project_id=project_value(context.project_id),
            date_from=context.date_from,
            date_to=context.date_to,
            country=country_value(context),
            tld=single_value(context.tld),
            company=company_value(context),
            company_domain=single_value(context.company_domain),
            competitors=list_value(context.competitors),
            competitor_domain=list_value(context.competitor_domains),
            limit=limit_value(parameters),
        )
        data = response.model_dump(mode='json')
        scope = choose_scope(data, context)
        if not scope or int(scope.get('summary', {}).get('total_traffic') or 0) <= 0:
            return self.failed_result(context, ['No channel data found for selected context'])
        data['tool_scope'] = scope_label(context)
        return self.success_result(
            context,
            data,
            'high',
            source_refs(['fact_traffic_sources_daily', 'fact_journey_sources_daily'], context),
        )

    def build_summary(self, data: dict[str, Any] | None) -> str:
        """Build tool summary.
        Args:
            data (dict[str, Any] | None): Tool data."""
        if not data:
            return 'Channel Intelligence did not return usable channel evidence.'
        scope = choose_scope(data, data_context(data))
        summary = scope.get('summary', {}) if scope else {}
        dominant_channel = summary.get('dominant_channel') or 'unknown'
        total_traffic = int(summary.get('total_traffic') or 0)
        return f'Channel evidence returned {total_traffic} visits with {dominant_channel} as dominant channel.'


class DeviceIntelligenceTool(BaseTool):
    tool_name = 'device_intelligence'
    evidence_type = 'device'
    source = 'analytics_db'
    description = 'Returns deterministic device evidence.'

    def run(self, session: Session, settings: Settings, context: ToolContext, parameters: dict[str, Any]) -> ToolResult:
        """Run device intelligence tool.
        Args:
            session (Session): Active database session.
            settings (Settings): Application settings.
            context (ToolContext): Normalized tool context.
            parameters (dict[str, Any]): Extra tool parameters."""
        errors = self.validate_input(context)
        if errors:
            return self.failed_result(context, errors)
        response = get_device_intelligence(
            session=session,
            default_project_id=settings.default_project_id,
            project_id=project_value(context.project_id),
            date_from=context.date_from,
            date_to=context.date_to,
            country=country_value(context),
            tld=single_value(context.tld),
            company=company_value(context),
            company_domain=single_value(context.company_domain),
            competitors=list_value(context.competitors),
            competitor_domain=list_value(context.competitor_domains),
            limit=limit_value(parameters),
        )
        data = response.model_dump(mode='json')
        scope = choose_scope(data, context)
        if not scope or int(scope.get('summary', {}).get('visits_total') or 0) <= 0:
            return self.failed_result(context, ['No device data found for selected context'])
        data['tool_scope'] = scope_label(context)
        return self.success_result(context, data, 'high', source_refs(['fact_device_trends_daily'], context))

    def build_summary(self, data: dict[str, Any] | None) -> str:
        """Build tool summary.
        Args:
            data (dict[str, Any] | None): Tool data."""
        if not data:
            return 'Device Intelligence did not return usable device evidence.'
        scope = choose_scope(data, data_context(data))
        summary = scope.get('summary', {}) if scope else {}
        dominant_device = summary.get('dominant_device') or 'unknown'
        visits_total = int(summary.get('visits_total') or 0)
        return f'Device evidence returned {visits_total} visits with {dominant_device} as dominant device.'


class SignalsTool(BaseTool):
    tool_name = 'signals'
    evidence_type = 'signal'
    source = 'derived_signal'
    description = 'Returns derived signals evidence.'

    def run(self, session: Session, settings: Settings, context: ToolContext, parameters: dict[str, Any]) -> ToolResult:
        """Run signals tool.
        Args:
            session (Session): Active database session.
            settings (Settings): Application settings.
            context (ToolContext): Normalized tool context.
            parameters (dict[str, Any]): Extra tool parameters."""
        errors = self.validate_input(context)
        if errors:
            return self.failed_result(context, errors)
        response = list_derived_signals(
            session,
            settings.default_project_id,
            project_value(context.project_id),
            context.date_from,
            context.date_to,
            str(parameters.get('signal_group', 'all')),
            str(parameters.get('signal_type', 'all')),
            str(parameters.get('entity_type', 'all')),
            country_value(context),
            company_value(context),
            single_value(context.company_domain),
            str(parameters.get('severity', 'all')),
            str(parameters.get('scope', 'all')),
            limit_value(parameters),
        )
        dependency_status = 'existing'
        if not response and bool(parameters.get('auto_recalculate', True)):
            recalculate_response = recalculate_signals(
                session,
                settings.default_project_id,
                build_signal_request(context),
            )
            response = recalculate_response.signals
            dependency_status = 'recalculated'
        data = {'dependency_status': dependency_status, 'signals': [item.model_dump(mode='json') for item in response]}
        if not response:
            return self.failed_result(context, ['No derived signals found for selected context'])
        return self.success_result(context, data, 'high', source_refs(['derived_signal'], context))

    def build_summary(self, data: dict[str, Any] | None) -> str:
        """Build tool summary.
        Args:
            data (dict[str, Any] | None): Tool data."""
        if not data:
            return 'Signals tool did not return usable signal evidence.'
        signals = data.get('signals', [])
        return f'Signals evidence returned {len(signals)} derived signals.'


class OpportunityScoreTool(BaseTool):
    tool_name = 'opportunity_score'
    evidence_type = 'opportunity_score'
    source = 'opportunity_score'
    description = 'Returns opportunity score evidence.'

    def run(self, session: Session, settings: Settings, context: ToolContext, parameters: dict[str, Any]) -> ToolResult:
        """Run opportunity score tool.
        Args:
            session (Session): Active database session.
            settings (Settings): Application settings.
            context (ToolContext): Normalized tool context.
            parameters (dict[str, Any]): Extra tool parameters."""
        errors = self.validate_input(context)
        if errors:
            return self.failed_result(context, errors)
        response = list_scores(
            session,
            settings.default_project_id,
            context.date_from,
            context.date_to,
            country_value(context),
            str(parameters.get('scope', 'all')),
            str(parameters.get('score_category', 'all')),
            limit_value(parameters),
        )
        dependency_status = 'existing'
        if not response.items and bool(parameters.get('auto_recalculate', True)):
            recalculated = recalculate_scores(session, settings.default_project_id, build_score_request(context))
            response = recalculated.scores
            dependency_status = 'recalculated'
        data = {'dependency_status': dependency_status, 'scores': response.model_dump(mode='json')}
        if not response.items:
            return self.failed_result(context, ['No opportunity score found for selected context'])
        return self.success_result(context, data, 'medium', source_refs(['opportunity_score'], context))

    def build_summary(self, data: dict[str, Any] | None) -> str:
        """Build tool summary.
        Args:
            data (dict[str, Any] | None): Tool data."""
        if not data:
            return 'Opportunity Score tool did not return usable score evidence.'
        items = data.get('scores', {}).get('items', [])
        first_item = items[0] if items else {}
        score = first_item.get('opportunity_score')
        category = first_item.get('score_category') or 'unknown'
        return f'Opportunity Score evidence returned {category} score {score}.'


class BudgetStrategyTool(BaseTool):
    tool_name = 'budget_strategy'
    evidence_type = 'budget_strategy'
    source = 'budget_strategy_report'
    description = 'Returns deterministic budget strategy evidence.'

    def validate_input(self, context: ToolContext) -> list[str]:
        """Validate tool input.
        Args:
            context (ToolContext): Normalized tool context."""
        errors = super().validate_input(context)
        if context.budget_amount is None:
            errors.append('budget_amount is required')
        if context.currency is None:
            errors.append('currency is required')
        if not context.country_name and not context.country_code:
            errors.append('country is required')
        return errors

    def run(self, session: Session, settings: Settings, context: ToolContext, parameters: dict[str, Any]) -> ToolResult:
        """Run budget strategy tool.
        Args:
            session (Session): Active database session.
            settings (Settings): Application settings.
            context (ToolContext): Normalized tool context.
            parameters (dict[str, Any]): Extra tool parameters."""
        errors = self.validate_input(context)
        if errors:
            return self.failed_result(context, errors)
        try:
            response = generate_strategy(session, settings.default_project_id, build_budget_request(context))
        except ValueError as error:
            return self.failed_result(context, [str(error)])
        data = response.model_dump(mode='json')
        data['budget_strategy_report_id'] = response.id
        return self.success_result(context, data, 'medium', budget_refs(response.id, context))

    def build_summary(self, data: dict[str, Any] | None) -> str:
        """Build tool summary.
        Args:
            data (dict[str, Any] | None): Tool data."""
        if not data:
            return 'Budget Strategy tool did not return usable strategy evidence.'
        approach = data.get('recommended_approach') or 'No recommendation'
        return f'Budget Strategy recommends: {approach}'


class RagRetrievalTool(BaseTool):
    tool_name = 'rag_retrieval'
    evidence_type = 'methodology'
    source = 'rag'
    description = 'Returns methodology and historical context from RAG.'

    def run(self, session: Session, settings: Settings, context: ToolContext, parameters: dict[str, Any]) -> ToolResult:
        """Run RAG retrieval tool.
        Args:
            session (Session): Active database session.
            settings (Settings): Application settings.
            context (ToolContext): Normalized tool context.
            parameters (dict[str, Any]): Extra tool parameters."""
        query = str(parameters.get('query') or 'methodology context')
        request = RagSearchRequest(
            query=query,
            country=context.country_name or context.country_code,
            company=context.company_name,
            strategy_mode=context.strategy_mode,
            document_types=list_parameter(parameters, 'document_types'),
            top_k=limit_value(parameters),
            create_evidence_items=False,
        )
        try:
            response = search_knowledge(
                session,
                context.project_id or UUID(settings.default_project_id),
                request,
                settings,
            )
        except Exception as error:
            return self.failed_result(context, [str(error)])
        data = {'query': query, 'results': [item.model_dump(mode='json') for item in response.results]}
        if not response.results:
            return self.failed_result(context, ['No RAG results found for selected query and filters'])
        return self.success_result(context, data, 'medium', rag_refs(data, context))

    def build_summary(self, data: dict[str, Any] | None) -> str:
        """Build tool summary.
        Args:
            data (dict[str, Any] | None): Tool data."""
        if not data:
            return 'RAG Retrieval did not return usable context.'
        results = data.get('results', [])
        return f'RAG Retrieval returned {len(results)} knowledge chunks.'


class MasToolRegistry:
    def __init__(self) -> None:
        """Create MAS tool registry.
        Args:
            None (None): No arguments are required."""
        self.tools = {
            tool.tool_name: tool
            for tool in [
                CountryIntelligenceTool(),
                CompetitorIntelligenceTool(),
                ChannelIntelligenceTool(),
                DeviceIntelligenceTool(),
                SignalsTool(),
                OpportunityScoreTool(),
                BudgetStrategyTool(),
                RagRetrievalTool(),
            ]
        }

    def list_tools(self) -> list[ToolInfo]:
        """List registered tools.
        Args:
            None (None): No arguments are required."""
        return [
            ToolInfo(
                tool_name=tool.tool_name,
                evidence_type=tool.evidence_type,
                source=tool.source,
                description=tool.description,
            )
            for tool in self.tools.values()
        ]

    def get_tool(self, tool_name: str) -> MasTool | None:
        """Read registered tool.
        Args:
            tool_name (str): Tool name."""
        return self.tools.get(tool_name)


def current_time() -> datetime:
    """Build current UTC timestamp.
    Args:
        None (None): No arguments are required."""
    return datetime.now(UTC)


def project_value(project_id: UUID | None) -> str | None:
    """Build project value.
    Args:
        project_id (UUID | None): Project identifier."""
    if project_id is None:
        return None
    return str(project_id)


def single_value(value: str | None) -> str:
    """Build single filter value.
    Args:
        value (str | None): Source value."""
    if value is None or not str(value).strip():
        return 'all'
    return str(value)


def list_value(values: list[str]) -> str:
    """Build list filter value.
    Args:
        values (list[str]): Source values."""
    if not values:
        return 'all'
    return ','.join(values)


def list_parameter(parameters: dict[str, Any], key: str) -> list[str]:
    """Read list parameter.
    Args:
        parameters (dict[str, Any]): Tool parameters.
        key (str): Parameter key."""
    value = parameters.get(key)
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value:
        return [item.strip() for item in value.split(',') if item.strip()]
    return []


def company_value(context: ToolContext) -> str:
    """Build company filter value.
    Args:
        context (ToolContext): Normalized tool context."""
    if context.company_id is not None:
        return str(context.company_id)
    return 'all'


def country_value(context: ToolContext) -> str:
    """Build country filter value.
    Args:
        context (ToolContext): Normalized tool context."""
    return context.country_name or context.country_code or 'all'


def limit_value(parameters: dict[str, Any]) -> int:
    """Build limit value.
    Args:
        parameters (dict[str, Any]): Tool parameters."""
    value = parameters.get('limit') or parameters.get('top_k') or 10
    try:
        numeric_value = int(value)
    except (TypeError, ValueError):
        return 10
    return max(1, min(numeric_value, 100))


def confidence_by_count(date_count: int) -> MasToolConfidence:
    """Build confidence by date count.
    Args:
        date_count (int): Active date count."""
    if date_count >= 14:
        return 'high'
    if date_count > 0:
        return 'medium'
    return 'low'


def traffic_refs(context: ToolContext) -> list[ToolSourceRef]:
    """Build traffic source refs.
    Args:
        context (ToolContext): Normalized tool context."""
    return source_refs(['fact_traffic_countries_daily'], context)


def source_refs(source_names: list[str], context: ToolContext) -> list[ToolSourceRef]:
    """Build table source refs.
    Args:
        source_names (list[str]): Source table names.
        context (ToolContext): Normalized tool context."""
    return [
        ToolSourceRef(
            source_type='table',
            source_name=source_name,
            record_id=None,
            context_hash=context.context_hash,
        )
        for source_name in source_names
    ]


def budget_refs(report_id: int, context: ToolContext) -> list[ToolSourceRef]:
    """Build budget source refs.
    Args:
        report_id (int): Budget strategy report identifier.
        context (ToolContext): Normalized tool context."""
    return [
        ToolSourceRef(
            source_type='report',
            source_name='budget_strategy_report',
            record_id=str(report_id),
            context_hash=context.context_hash,
        )
    ]


def rag_refs(data: dict[str, Any], context: ToolContext) -> list[ToolSourceRef]:
    """Build RAG source refs.
    Args:
        data (dict[str, Any]): RAG data.
        context (ToolContext): Normalized tool context."""
    refs: list[ToolSourceRef] = []
    for item in data.get('results', []):
        refs.append(
            ToolSourceRef(
                source_type='rag',
                source_name='knowledge_document',
                record_id=str(item.get('document_id')),
                context_hash=context.context_hash,
            )
        )
    return refs


def scope_label(context: ToolContext) -> str:
    """Build analytical scope label.
    Args:
        context (ToolContext): Normalized tool context."""
    if context.strategy_mode == 'market_entry':
        return 'target_country_market'
    if context.company_id is not None:
        return 'selected_company_country'
    return 'selected_scope'


def choose_scope(data: dict[str, Any], context: ToolContext) -> dict[str, Any] | None:
    """Choose analytics scope.
    Args:
        data (dict[str, Any]): Analytics response data.
        context (ToolContext): Normalized tool context."""
    if context.strategy_mode == 'market_entry':
        return data.get('competitor_scope') or data.get('overall_scope')
    if context.company_id is not None:
        return data.get('company_scope') or data.get('overall_scope')
    if context.competitors:
        return data.get('competitor_scope') or data.get('overall_scope')
    return data.get('overall_scope')


def data_context(data: dict[str, Any]) -> ToolContext:
    """Build context from serialized data.
    Args:
        data (dict[str, Any]): Serialized tool data."""
    filters = data.get('filters', {})
    return ToolContext(
        project_id=filters.get('project_id'),
        strategy_mode=data.get('tool_scope'),
        country_name=filters.get('country'),
    )


def build_signal_request(context: ToolContext) -> RecalculateSignalsRequest:
    """Build signal recalculation request.
    Args:
        context (ToolContext): Normalized tool context."""
    return RecalculateSignalsRequest(
        project_id=project_value(context.project_id),
        date_from=required_date(context.date_from, 'date_from'),
        date_to=required_date(context.date_to, 'date_to'),
        country=country_value(context),
        tld=single_value(context.tld),
        company=company_value(context),
        company_domain=single_value(context.company_domain),
        competitors=list_value(context.competitors),
        competitor_domain=list_value(context.competitor_domains),
        calculation_version=context.calculation_version,
        context_hash=context.context_hash,
        context_json=context.model_dump(mode='json'),
    )


def build_score_request(context: ToolContext) -> OpportunityScoreRecalculateRequest:
    """Build opportunity score recalculation request.
    Args:
        context (ToolContext): Normalized tool context."""
    return OpportunityScoreRecalculateRequest(
        date_from=required_date(context.date_from, 'date_from'),
        date_to=required_date(context.date_to, 'date_to'),
        country=country_value(context),
        tld=single_value(context.tld),
        company=company_value(context),
        company_domain=single_value(context.company_domain),
        competitors=list_value(context.competitors),
        competitor_domain=list_value(context.competitor_domains),
        calculation_version=context.calculation_version,
        context_hash=context.context_hash,
        context_json=context.model_dump(mode='json'),
    )


def build_budget_request(context: ToolContext) -> BudgetStrategyGenerateRequest:
    """Build budget strategy request.
    Args:
        context (ToolContext): Normalized tool context."""
    return BudgetStrategyGenerateRequest(
        strategy_mode=strategy_value(context.strategy_mode),
        date_from=required_date(context.date_from, 'date_from'),
        date_to=required_date(context.date_to, 'date_to'),
        country=country_value(context),
        budget_amount=required_budget(context.budget_amount),
        currency=currency_value(context.currency),
        company=company_value(context),
        company_domain=single_value(context.company_domain),
        competitors=list_value(context.competitors),
        competitor_domain=list_value(context.competitor_domains),
        tld=single_value(context.tld),
        calculation_version=context.calculation_version,
    )


def required_date(value: date | None, field_name: str) -> date:
    """Read required date.
    Args:
        value (date | None): Date value.
        field_name (str): Field name."""
    if value is None:
        raise ValueError(f'{field_name} is required')
    return value


def required_budget(value: Decimal | None) -> Decimal:
    """Read required budget.
    Args:
        value (Decimal | None): Budget value."""
    if value is None:
        raise ValueError('budget_amount is required')
    return value


def currency_value(value: str | None) -> str:
    """Build currency value.
    Args:
        value (str | None): Currency value."""
    if value in {'USD', 'EUR'}:
        return value
    return 'USD'


def strategy_value(value: str | None) -> str:
    """Build strategy value.
    Args:
        value (str | None): Strategy mode value."""
    if value == 'market_entry':
        return 'market_entry'
    return 'existing_presence'


def create_registry() -> MasToolRegistry:
    """Create MAS tool registry.
    Args:
        None (None): No arguments are required."""
    return MasToolRegistry()
