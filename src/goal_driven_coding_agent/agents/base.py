"""Abstract base classes for agent runners."""

from __future__ import annotations

from abc import ABC, abstractmethod

from goal_driven_coding_agent.agents.types import (
    GoalDrivenAgentConfig,
    GoalDrivenAgentResult,
)


class AgentRunner(ABC):
    """Base contract every agent runner must satisfy."""

    @abstractmethod
    def run(self, config: GoalDrivenAgentConfig) -> GoalDrivenAgentResult:
        """Execute the agent for the provided configuration."""

