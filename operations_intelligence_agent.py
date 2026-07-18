# ==========================================================
# OPERATIONS INTELLIGENCE ORCHESTRATOR
# ==========================================================

from downtime_agent import DowntimeAgent
from production_loss_agent import ProductionLossAgent
from operator_equipment_agent import OperatorEquipmentAgent
from operations_correlation_agent import OperationsCorrelationAgent
from executive_operations_report_agent import ExecutiveOperationsReportAgent


class OperationsIntelligenceAgent:

    def __init__(self, api_key):

        self.api_key = api_key

    def investigate(
        self,
        downtime_df,
        start_date,
        end_date,
        production_rate_tph=250
    ):

        # =====================================================
        # Stage 1
        # Downtime Investigation
        # =====================================================

        downtime_agent = DowntimeAgent(downtime_df)

        downtime_result = downtime_agent.investigate(
            start_date=start_date,
            end_date=end_date
        )

        # =====================================================
        # Stage 2
        # Production Loss
        # =====================================================

        production_agent = ProductionLossAgent(
            production_rate_tph=production_rate_tph
        )

        production_result = production_agent.investigate(
            downtime_df
        )

        # =====================================================
        # Stage 3
        # Operator & Equipment Intelligence
        # =====================================================

        operator_agent = OperatorEquipmentAgent(
            self.api_key
        )

        operator_result = operator_agent.investigate(
            downtime_df
        )

        # =====================================================
        # Stage 4
        # Correlation
        # =====================================================

        correlation_agent = OperationsCorrelationAgent()

        correlation_result = correlation_agent.investigate(

            downtime_result=downtime_result,

            production_loss_result=production_result,

            operator_result=operator_result

        )

        # =====================================================
        # Stage 5
        # Executive Report
        # =====================================================

        executive_agent = ExecutiveOperationsReportAgent()

        executive_result = executive_agent.investigate(
            correlation_result
        )

        # =====================================================
        # Final Output
        # =====================================================

        return {

            "downtime": downtime_result,

            "production_loss": production_result,

            "operator_equipment": operator_result,

            "correlation": correlation_result,

            "executive_report": executive_result

        }
