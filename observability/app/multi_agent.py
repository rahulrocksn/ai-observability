"""
Multi-Agent System with Specialized Agents
Each agent has a specific role and is tracked separately in observability
"""

import os
from typing import Dict, Any, List
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain.tools import Tool
from langchain.schema import BaseMessage
from .callbacks import TraceLoggerCallbackHandler
import logging

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """Orchestrates multiple specialized agents"""
    
    def __init__(self):
        self.db = SQLDatabase.from_uri(os.getenv("DATABASE_URL"))
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        # Initialize specialized agents
        self.sql_agent = self._create_sql_agent()
        self.analytics_agent = self._create_analytics_agent()
        self.reporting_agent = self._create_reporting_agent()
        
    def _create_sql_agent(self) -> AgentExecutor:
        """Creates an agent specialized in SQL operations"""
        toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        tools = toolkit.get_tools()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a SQL Database Expert Agent. Your role is to:
            1. Explore database schemas and understand table structures
            2. Execute SQL queries to retrieve data
            3. Validate data quality and constraints
            4. Return structured data for other agents to analyze
            
            Always be precise with SQL syntax and provide clean, well-formatted results.
            If you encounter an error, explain what went wrong and suggest alternatives.
            """),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15
        )
    
    def _create_analytics_agent(self) -> AgentExecutor:
        """Creates an agent specialized in data analysis"""
        
        def calculate_statistics(data_description: str) -> str:
            """Analyze data and calculate statistical insights"""
            return f"Statistical analysis of: {data_description}"
        
        def identify_trends(data_description: str) -> str:
            """Identify trends and patterns in data"""
            return f"Trend analysis of: {data_description}"
        
        def compare_metrics(data_description: str) -> str:
            """Compare different metrics and KPIs"""
            return f"Comparative analysis of: {data_description}"
        
        tools = [
            Tool(
                name="calculate_statistics",
                func=calculate_statistics,
                description="Calculate statistical insights like averages, totals, distributions"
            ),
            Tool(
                name="identify_trends",
                func=identify_trends,
                description="Identify trends, patterns, and anomalies in data"
            ),
            Tool(
                name="compare_metrics",
                func=compare_metrics,
                description="Compare different metrics, KPIs, and performance indicators"
            )
        ]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Data Analytics Expert Agent. Your role is to:
            1. Analyze data provided by the SQL Agent
            2. Calculate statistical insights and metrics
            3. Identify trends, patterns, and anomalies
            4. Provide quantitative analysis and comparisons
            
            Focus on mathematical accuracy and provide actionable insights.
            Always explain your analytical approach and reasoning.
            """),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    def _create_reporting_agent(self) -> AgentExecutor:
        """Creates an agent specialized in reporting and summarization"""
        
        def create_executive_summary(content: str) -> str:
            """Create an executive summary of findings"""
            return f"Executive Summary: {content}"
        
        def format_insights(content: str) -> str:
            """Format insights into a readable report"""
            return f"Formatted Report: {content}"
        
        def generate_recommendations(content: str) -> str:
            """Generate actionable recommendations"""
            return f"Recommendations based on: {content}"
        
        tools = [
            Tool(
                name="create_executive_summary",
                func=create_executive_summary,
                description="Create concise executive summaries of findings"
            ),
            Tool(
                name="format_insights",
                func=format_insights,
                description="Format data insights into readable reports"
            ),
            Tool(
                name="generate_recommendations",
                func=generate_recommendations,
                description="Generate actionable business recommendations"
            )
        ]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Business Reporting Expert Agent. Your role is to:
            1. Synthesize findings from SQL and Analytics agents
            2. Create clear, executive-level summaries
            3. Generate actionable business recommendations
            4. Format insights for different audiences
            
            Focus on clarity, business value, and actionable insights.
            Use professional business language and structure.
            """),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    def process_query(self, question: str, trace_handler: TraceLoggerCallbackHandler) -> Dict[str, Any]:
        """
        Process a query through the multi-agent system
        """
        trace_handler.steps = [] # Initialize steps
        all_steps = []
        
        try:
            trace_handler.set_agent_context("Orchestrator", question)
            
            # Step 1: SQL Agent gets the data
            logger.info(f"🔍 SQL Agent processing: {question}")
            sql_handler = TraceLoggerCallbackHandler()
            sql_result = self.sql_agent.invoke(
                {"input": f"Find data to answer: {question}"},
                config={"callbacks": [sql_handler]}
            )
            all_steps.extend(sql_handler.steps)
            
            # Step 2: Analytics Agent analyzes the data
            logger.info("📊 Analytics Agent analyzing data...")
            analytics_handler = TraceLoggerCallbackHandler()
            analytics_result = self.analytics_agent.invoke(
                {"input": f"Analyze this data: {sql_result['output']}"},
                config={"callbacks": [analytics_handler]}
            )
            all_steps.extend(analytics_handler.steps)
            
            # Step 3: Reporting Agent creates final summary
            logger.info("📝 Reporting Agent creating summary...")
            reporting_handler = TraceLoggerCallbackHandler()
            report_result = self.reporting_agent.invoke(
                {"input": f"Create a business report from: SQL Data: {sql_result['output']} Analytics: {analytics_result['output']}"},
                config={"callbacks": [reporting_handler]}
            )
            all_steps.extend(reporting_handler.steps)
            
            # Combine all results and log the final trace
            final_answer = report_result['output']
            trace_handler.steps = all_steps
            trace_handler.final_answer = final_answer
            
            return {
                "sql_findings": sql_result['output'],
                "analytics_insights": analytics_result['output'],
                "final_report": final_answer,
                "agent_flow": ["SQL Agent", "Analytics Agent", "Reporting Agent"]
            }
            
        except Exception as e:
            logger.error(f"Multi-agent processing failed: {e}")
            trace_handler.final_answer = "" # Ensure error is logged as empty string
            trace_handler.steps = all_steps
            raise e
        finally:
            # Explicitly end the run to log the combined trace
            if trace_handler.final_answer:
                trace_handler.on_chain_end({"output": trace_handler.final_answer})
            else:
                trace_handler.on_chain_end({}) 