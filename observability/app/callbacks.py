# in app/callbacks.py
import os
import uuid
import datetime
import logging
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.agents import AgentAction, AgentFinish
from elasticsearch import Elasticsearch

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to Elasticsearch using the environment variable
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
INDEX_NAME = "agent_traces"

try:
    es_client = Elasticsearch(
        ELASTICSEARCH_URL,
        # Optional: Add authentication here if needed in the future
        # api_key="YOUR_API_KEY",
        # basic_auth=("user", "password")
    )
    # Test connection with a simple info() call instead of ping()
    cluster_info = es_client.info()
    logger.info(f"Successfully connected to Elasticsearch at {ELASTICSEARCH_URL}")
    logger.info(f"Cluster: {cluster_info.get('cluster_name')}, Version: {cluster_info.get('version', {}).get('number')}")
except Exception as e:
    logger.error(f"Could not configure Elasticsearch client: {e}")
    es_client = None

# --- Custom Callback Handler ---
class TraceLoggerCallbackHandler(BaseCallbackHandler):
    """
    A comprehensive callback handler that logs LangChain agent traces
    to both the console and Elasticsearch for deep observability.
    """

    def __init__(self) -> None:
        super().__init__()
        self.run_id = str(uuid.uuid4())
        self.steps: List[Dict[str, Any]] = []
        self.final_answer: Optional[str] = None
        self.start_time = datetime.datetime.utcnow().isoformat()
        self.agent_type = "single_agent" # Default
        self.original_question = ""
        self.trace_data = {
            "run_id": self.run_id,
            "steps": [],
            "final_output": None,
            "status": "started",
            "@timestamp": self.start_time,
        }

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        """Log the agent's action and tool input."""
        step = {
            "type": "action",
            "action": {
                "tool": action.tool,
                "tool_input": action.tool_input,
                "log": action.log.strip(),
            },
            "@timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self.trace_data["steps"].append(step)
        logger.info(f"[{self.run_id}] Agent Action: {action.tool} with input {action.tool_input}")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Log the tool's output (observation)."""
        step = {
            "type": "observation",
            "observation": output,
            "@timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self.trace_data["steps"].append(step)
        logger.info(f"[{self.run_id}] Tool Output: {output}")

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """
        Log the final output of the agent and write the entire trace
        to Elasticsearch.
        """
        self.trace_data["final_output"] = finish.return_values.get("output", "")
        self.trace_data["status"] = "finished"
        end_time = datetime.datetime.now(datetime.timezone.utc)
        self.trace_data["duration_ms"] = (end_time - self.start_time).total_seconds() * 1000
        logger.info(f"[{self.run_id}] Agent Finished. Final Output: {self.trace_data['final_output']}")

        self._log_to_elasticsearch()

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        self._handle_error(error)

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        self._handle_error(error)

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        """Called when chain errors."""
        self.final_answer = ""
        self.trace_data["status"] = "error"
        self.trace_data["error"] = str(error)
        end_time = datetime.datetime.now(datetime.timezone.utc)
        self.trace_data["duration_ms"] = (end_time - self.start_time).total_seconds() * 1000
        logger.error(f"[{self.run_id}] Agent Error: {error}")

        self._log_trace()

    def _handle_error(self, error: BaseException) -> None:
        """Helper to handle and log errors."""
        self.final_answer = f"Error: {str(error)}"
        self.trace_data["status"] = "error"
        self.trace_data["error"] = str(error)
        end_time = datetime.datetime.now(datetime.timezone.utc)
        self.trace_data["duration_ms"] = (end_time - self.start_time).total_seconds() * 1000
        logger.error(f"[{self.run_id}] Agent Error: {error}")

        self._log_to_elasticsearch()

    def _log_to_elasticsearch(self):
        """Send the completed trace to Elasticsearch."""
        if es_client:
            try:
                es_client.index(index=INDEX_NAME, document=self.trace_data, id=self.run_id)
                logger.info(f"[{self.run_id}] Successfully logged trace to Elasticsearch.")
            except Exception as e:
                logger.error(f"[{self.run_id}] Failed to log trace to Elasticsearch: {e}")

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """Called when LLM starts running."""
        logger.info(f"[{self.run_id}] LLM started with prompts: {prompts}")
        
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM ends running."""
        logger.info(f"[{self.run_id}] LLM completed with response: {response}")
        
    def on_text(self, text: str, **kwargs: Any) -> None:
        """Called when agent or tool outputs text."""
        logger.info(f"[{self.run_id}] Text output: {text}")
        
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when chain starts running."""
        logger.info(f"[{self.run_id}] Chain started: {serialized.get('name', 'unknown')} with inputs: {inputs}")
        
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when chain ends running."""
        # If the main answer hasn't been set, grab it from the outputs
        if self.final_answer is None and outputs.get("output"):
            self.final_answer = outputs["output"]
            
        # This check prevents intermediate agent steps from logging incomplete traces
        if self.final_answer is not None or self.steps:
            logger.info(f"[{self.run_id}] Logging final trace to Elasticsearch.")
            self._log_trace()

    def set_agent_context(self, agent_type: str, question: str = ""):
        """Set context for which agent is being tracked"""
        self.agent_type = agent_type
        if question:
            self.original_question = question

    def _log_trace(self):
        """Internal method to format and send the trace to Elasticsearch."""
        if not es_client:
            return
            
        end_time = datetime.datetime.utcnow()
        start_time_dt = datetime.datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
        
        trace_document = {
            "run_id": self.run_id,
            "question": self.original_question,
            "agent_type": self.agent_type,
            "final_answer": self.final_answer,
            "status": "completed" if self.final_answer and "Error" not in self.final_answer else "error",
            "steps": self.steps,
            "start_time": self.start_time,
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time_dt).total_seconds(),
            "@timestamp": end_time.isoformat()
        }
        try:
            es_client.index(index=INDEX_NAME, document=trace_document, id=self.run_id)
            logger.info(f"[{self.run_id}] Successfully logged trace to Elasticsearch.")
        except Exception as e:
            logger.error(f"[{self.run_id}] Failed to log trace to Elasticsearch: {e}")