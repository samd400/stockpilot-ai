"""
Agent System Base Classes — Controller, Executor, Registry.

Agents are autonomous workers that run via Celery periodic tasks.
They use Gemini LLM for decision-making and AgentTools for actions.
All actions are validated before execution.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AgentAction:
    """Represents a validated action to be executed."""
    tool_name: str
    params: Dict[str, Any]
    reason: str = ""
    approved: bool = False


@dataclass
class AgentResult:
    """Result of an agent run."""
    agent_name: str
    tenant_id: str
    actions_proposed: int = 0
    actions_executed: int = 0
    actions_failed: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class AgentBase(ABC):
    """Base class for all agents."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def analyze(self, tenant_id: str, db_session, tools: "AgentTools") -> List[AgentAction]:
        """Analyze the current state and propose actions."""
        pass

    @abstractmethod
    def get_llm_prompt(self, context: Dict[str, Any]) -> str:
        """Generate the prompt for Gemini LLM decision layer."""
        pass

    def validate_action(self, action: AgentAction) -> bool:
        """Validate an action before execution. Override for custom validation."""
        if not action.tool_name or not action.params:
            return False
        return True

    def run(self, tenant_id: str, db_session, tools: "AgentTools") -> AgentResult:
        """Main execution loop: analyze → validate → execute."""
        result = AgentResult(agent_name=self.name, tenant_id=tenant_id)

        try:
            actions = self.analyze(tenant_id, db_session, tools)
            result.actions_proposed = len(actions)

            for action in actions:
                if not self.validate_action(action):
                    result.errors.append(f"Validation failed for {action.tool_name}: {action.reason}")
                    continue

                action.approved = True
                try:
                    exec_result = tools.execute(action.tool_name, action.params)
                    result.actions_executed += 1
                    result.details.append({
                        "tool": action.tool_name,
                        "params": action.params,
                        "result": str(exec_result),
                        "reason": action.reason,
                    })
                except Exception as e:
                    result.actions_failed += 1
                    result.errors.append(f"Execution failed for {action.tool_name}: {str(e)}")
                    logger.error(f"Agent {self.name} action failed: {e}")

        except Exception as e:
            result.errors.append(f"Agent analysis failed: {str(e)}")
            logger.error(f"Agent {self.name} run failed: {e}")

        return result


class AgentRegistry:
    """Registry for all available agents."""

    _agents: Dict[str, AgentBase] = {}

    @classmethod
    def register(cls, agent: AgentBase):
        cls._agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")

    @classmethod
    def get(cls, name: str) -> Optional[AgentBase]:
        return cls._agents.get(name)

    @classmethod
    def all(cls) -> Dict[str, AgentBase]:
        return cls._agents.copy()

    @classmethod
    def names(cls) -> List[str]:
        return list(cls._agents.keys())


class AgentExecutor:
    """Orchestrates agent execution for a tenant."""

    def __init__(self, db_session, tools: "AgentTools"):
        self.db = db_session
        self.tools = tools

    def run_agent(self, agent_name: str, tenant_id: str) -> AgentResult:
        agent = AgentRegistry.get(agent_name)
        if not agent:
            return AgentResult(agent_name=agent_name, tenant_id=tenant_id,
                               errors=[f"Agent '{agent_name}' not found"])
        return agent.run(tenant_id, self.db, self.tools)

    def run_all(self, tenant_id: str) -> List[AgentResult]:
        results = []
        for name, agent in AgentRegistry.all().items():
            result = agent.run(tenant_id, self.db, self.tools)
            results.append(result)
        return results
