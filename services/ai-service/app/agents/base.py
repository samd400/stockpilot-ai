"""
Upgraded Agent System — Multi-step agentic loop with Gemini tool calling.

Each agent runs a reasoning loop:
  1. Gather context from database
  2. Feed to Gemini with available tools
  3. Gemini decides which tool to call
  4. Execute tool, collect result
  5. Feed result back to Gemini
  6. Repeat until Gemini says "finish" or max iterations reached
  7. Log every step to AgentAuditLog
"""
import time
import uuid
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class AgentStep:
    """One iteration of the agentic loop."""
    iteration: int
    tool_called: Optional[str]
    params: Optional[Dict]
    result: Any
    reasoning: str = ""
    tokens_used: int = 0


@dataclass
class AgentResult:
    """Full result of an agent run."""
    agent_name: str
    tenant_id: str
    status: str = "completed"  # completed, failed, max_iterations_reached
    steps: List[AgentStep] = field(default_factory=list)
    final_summary: str = ""
    actions_executed: int = 0
    errors: List[str] = field(default_factory=list)
    execution_time_ms: int = 0
    tokens_used: int = 0


class AgentBase(ABC):
    """Base class for all agentic agents."""
    max_iterations = 10
    name = "base_agent"
    description = "Base agent"

    @abstractmethod
    def get_system_prompt(self) -> str:
        """System prompt describing agent's role and objectives."""
        pass

    @abstractmethod
    def get_tools_schema(self) -> List[Dict]:
        """Gemini function calling schema for available tools."""
        pass

    @abstractmethod
    def gather_context(self, tenant_id: str, db: Session) -> Dict[str, Any]:
        """Gather initial context from database."""
        pass

    def build_initial_prompt(self, context: Dict[str, Any]) -> str:
        """Build the initial prompt from context."""
        return f"Analyze the following business data and take appropriate actions:\n\n{context}"

    def run(self, tenant_id: str, db: Session, tools: "AgentTools",
            dry_run: bool = False) -> AgentResult:
        """Run the multi-step agentic loop."""
        start_time = time.time()
        result = AgentResult(agent_name=self.name, tenant_id=tenant_id)

        try:
            from app.services.gemini_service import call_gemini_with_tools, count_tokens

            # Step 1: Gather context
            context = self.gather_context(tenant_id, db)
            initial_prompt = self.build_initial_prompt(context)
            system_prompt = self.get_system_prompt()
            tools_schema = self.get_tools_schema()

            # Inject dry_run info
            if dry_run:
                system_prompt += "\n\nNOTE: This is a DRY RUN. Propose actions but do not execute them."

            conversation_history = []
            iteration = 0

            while iteration < self.max_iterations:
                iteration += 1
                prompt = initial_prompt if iteration == 1 else \
                    f"Previous action result: {result.steps[-1].result}\n\nContinue analysis or call 'finish' if done."

                # Call Gemini
                gemini_response = call_gemini_with_tools(
                    prompt=prompt,
                    tools_schema=tools_schema,
                    system_instruction=system_prompt,
                    conversation_history=conversation_history,
                )

                tokens = count_tokens(prompt)
                result.tokens_used += tokens

                if gemini_response["type"] == "text":
                    # Gemini returned text — agent is done
                    final_text = gemini_response["text"]
                    step = AgentStep(iteration=iteration, tool_called=None, params=None,
                                     result="Agent completed", reasoning=final_text[:500],
                                     tokens_used=tokens)
                    result.steps.append(step)
                    result.final_summary = final_text[:1000]
                    break

                elif gemini_response["type"] == "tool_call":
                    tool_name = gemini_response["name"]
                    params = gemini_response["params"]

                    # Check for finish signal
                    if tool_name == "finish":
                        result.final_summary = params.get("summary", "Agent completed analysis")
                        step = AgentStep(iteration=iteration, tool_called="finish",
                                         params=params, result="Completed",
                                         reasoning=params.get("summary", "")[:500])
                        result.steps.append(step)
                        break

                    # Execute tool
                    try:
                        if not dry_run:
                            tool_result = tools.execute(tool_name, {**params, "_tenant_id": tenant_id})
                            result.actions_executed += 1
                        else:
                            tool_result = f"[DRY RUN] Would call {tool_name}({params})"

                        step = AgentStep(iteration=iteration, tool_called=tool_name,
                                         params=params, result=str(tool_result)[:500],
                                         tokens_used=tokens)
                        result.steps.append(step)

                        # Add to conversation history for next iteration
                        conversation_history.append({
                            "role": "model",
                            "parts": [{"functionCall": {"name": tool_name, "args": params}}]
                        })
                        conversation_history.append({
                            "role": "user",
                            "parts": [{"functionResponse": {
                                "name": tool_name,
                                "response": {"result": str(tool_result)[:500]}
                            }}]
                        })

                    except Exception as e:
                        error_msg = f"Tool {tool_name} failed: {e}"
                        result.errors.append(error_msg)
                        logger.error(f"Agent {self.name} tool error: {e}")
                        step = AgentStep(iteration=iteration, tool_called=tool_name,
                                         params=params, result=f"ERROR: {e}")
                        result.steps.append(step)
                        conversation_history.append({
                            "role": "user",
                            "parts": [{"functionResponse": {
                                "name": tool_name,
                                "response": {"error": str(e)}
                            }}]
                        })
            else:
                result.status = "max_iterations_reached"
                result.final_summary = f"Agent reached max iterations ({self.max_iterations})"

        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))
            logger.error(f"Agent {self.name} failed: {e}", exc_info=True)

        result.execution_time_ms = int((time.time() - start_time) * 1000)

        # Log to audit table
        try:
            _log_agent_audit(db, tenant_id, self.name, result)
        except Exception as e:
            logger.warning(f"Agent audit log failed: {e}")

        return result


def _log_agent_audit(db: Session, tenant_id: str, agent_name: str, result: AgentResult):
    try:
        from app.models.agent_audit_log import AgentAuditLog
        log = AgentAuditLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            agent_name=agent_name,
            action="agent_run",
            status=result.status,
            execution_time_ms=result.execution_time_ms,
            llm_tokens_used=result.tokens_used,
            output_data={
                "final_summary": result.final_summary[:500] if result.final_summary else "",
                "actions_executed": result.actions_executed,
                "steps": len(result.steps),
                "errors": result.errors[:5],
            },
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.warning(f"Audit log write failed: {e}")
        db.rollback()


# Agent Registry
_AGENT_REGISTRY: Dict[str, "AgentBase"] = {}


def register_agent(agent: "AgentBase"):
    _AGENT_REGISTRY[agent.name] = agent
    logger.info(f"Registered agent: {agent.name}")


def get_agent(name: str) -> Optional["AgentBase"]:
    return _AGENT_REGISTRY.get(name)


def list_agents() -> Dict[str, str]:
    return {name: agent.description for name, agent in _AGENT_REGISTRY.items()}
