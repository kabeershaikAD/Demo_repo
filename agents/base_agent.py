"""
Base agent class for the Agentic Legal RAG system.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from loguru import logger
import asyncio
from datetime import datetime


class AgentResponse(BaseModel):
    """Standard response format for all agents."""
    success: bool
    data: Any
    metadata: Dict[str, Any]
    timestamp: datetime
    agent_name: str
    error_message: Optional[str] = None


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logger.bind(agent=name)
        self.is_initialized = False
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent with required resources."""
        pass
    
    @abstractmethod
    async def process(self, input_data: Any) -> AgentResponse:
        """Process input data and return response."""
        pass
    
    async def execute(self, input_data: Any) -> AgentResponse:
        """Execute the agent with error handling."""
        try:
            if not self.is_initialized:
                self.logger.info(f"Initializing {self.name} agent...")
                init_success = await self.initialize()
                if not init_success:
                    return AgentResponse(
                        success=False,
                        data=None,
                        metadata={},
                        timestamp=datetime.now(),
                        agent_name=self.name,
                        error_message="Failed to initialize agent"
                    )
                self.is_initialized = True
            
            self.logger.info(f"Processing input with {self.name} agent...")
            result = await self.process(input_data)
            self.logger.info(f"{self.name} agent completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in {self.name} agent: {str(e)}")
            return AgentResponse(
                success=False,
                data=None,
                metadata={},
                timestamp=datetime.now(),
                agent_name=self.name,
                error_message=str(e)
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "name": self.name,
            "is_initialized": self.is_initialized,
            "config": self.config
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update agent configuration."""
        self.config.update(new_config)
        self.logger.info(f"Updated configuration for {self.name} agent")
