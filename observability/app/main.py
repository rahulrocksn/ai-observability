# in app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from .agent import agent
from .callbacks import TraceLoggerCallbackHandler 
from prometheus_fastapi_instrumentator import Instrumentator
from .multi_agent import MultiAgentOrchestrator

app = FastAPI(
    title="Cognosys - Autonomous BI Agent",
    description="An AI agent that can answer questions by querying a SQL database."
)

Instrumentator().instrument(app).expose(app)

# Initialize multi-agent system
multi_agent_system = MultiAgentOrchestrator()

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    run_id: str # Also return the run_id for correlation
    error: str | None = None

@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """Handles a user's natural language query."""
    try:
        prompt = (
            "You are an expert business intelligence analyst. "
            "Your goal is to provide concise, accurate, and actionable insights based on the user's question. "
            f"Here is the user's question: {request.question}"
        )
        
        # Instantiate a new handler for each request
        trace_handler = TraceLoggerCallbackHandler()
        
        response = agent.invoke(
            {"input": prompt},
            # Pass the handler into the agent's config
            config={"callbacks": [trace_handler]}
        )
        
        return {
            "answer": response.get("output", "No output found."),
            "run_id": trace_handler.run_id # Return the unique ID for this run
        }

    except Exception as e:
        return {"answer": "", "run_id": trace_handler.run_id, "error": f"An error occurred: {str(e)}"}

@app.post("/multi-agent-query")
async def multi_agent_query(request: QueryRequest):
    """Process a query through the multi-agent system with specialized agents"""
    trace_handler = TraceLoggerCallbackHandler()
    
    try:
        # Process through multi-agent system
        result = multi_agent_system.process_query(request.question, trace_handler)
        
        return {
            "question": request.question,
            "sql_findings": result["sql_findings"],
            "analytics_insights": result["analytics_insights"], 
            "final_report": result["final_report"],
            "agent_flow": result["agent_flow"],
            "run_id": trace_handler.run_id,
            "error": None
        }
    except Exception as e:
        return {
            "question": request.question,
            "sql_findings": "",
            "analytics_insights": "",
            "final_report": "",
            "agent_flow": [],
            "run_id": trace_handler.run_id,
            "error": f"Multi-agent processing failed: {str(e)}"
        }

@app.get("/healthz", status_code=200)
async def health_check():
    """Provides a detailed health check of the service and its dependencies."""
    from .callbacks import es_client
    
    services = {
        "elasticsearch": {
            "status": "unknown",
            "info": None
        }
    }
    
    # Check Elasticsearch connection
    if es_client:
        try:
            # Use info() instead of ping() for better compatibility
            cluster_info = es_client.info()
            services["elasticsearch"]["status"] = "healthy"
            services["elasticsearch"]["info"] = {
                "cluster_name": cluster_info.get("cluster_name"),
                "version": cluster_info.get("version", {}).get("number")
            }
        except Exception as e:
            services["elasticsearch"]["status"] = "unhealthy"
            services["elasticsearch"]["info"] = str(e)
    else:
        services["elasticsearch"]["status"] = "disabled"
        services["elasticsearch"]["info"] = "Elasticsearch client is not configured."
        
    return {
        "status": "ok",
        "services": services
    }