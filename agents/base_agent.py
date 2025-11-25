"""Base Agent class for Universal Documentation Agent using Microsoft Agent Framework"""

from typing import Dict, Any, Optional
import sys
from config import Config, AGENT_SDK_AVAILABLE, AGENT_SDK_VERSION, AGENT_SDK_ERROR

# Import SDK with detailed error handling
if AGENT_SDK_AVAILABLE:
    try:
        from agent_framework import ChatAgent
        from agent_framework.azure import AzureAIAgentClient
    except ImportError as e:
        print(f"⚠️  Warning: SDK import failed after availability check: {e}")
        ChatAgent = None  # type: ignore
        AzureAIAgentClient = None  # type: ignore
else:
    ChatAgent = None  # type: ignore
    AzureAIAgentClient = None  # type: ignore


class BaseAgent:
    """Base class for all specialized agents using Microsoft Agent Framework"""
    
    # Class-level registry to track existing agents and avoid duplicates
    _agent_registry: Dict[str, Any] = {}
    
    # Shared Azure AI Agent Client (SINGLETON) - prevents duplicate agent creation
    _shared_client: Optional[Any] = None
    _client_initialized: bool = False
    
    # Shared context store for inter-agent communication
    _shared_context: Dict[str, Any] = {
        "messages": [],  # Message queue for agent-to-agent communication
        "states": {},    # Shared state dictionary (e.g., requirements, analysis results)
        "handovers": []  # Handover requests between agents
    }
    
    # Communication history for debugging and tracing
    _communication_log: list = []
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[list] = None
    ):
        """
        Initialize the base agent
        
        Args:
            name: Name of the agent
            system_prompt: System prompt defining agent's role
            model: Model deployment name (defaults to config)
            temperature: Temperature for generation (defaults to config)
            tools: List of tool functions for the agent
        """
        self.name = name
        self.system_prompt = system_prompt
        self.model = model or Config.DEPLOYMENT_NAME
        self.temperature = temperature or Config.TEMPERATURE
        self.tools = tools or []
        self.agent: Optional[Any] = None
        self.agent_id: Optional[str] = None
        self._chat_client: Optional[Any] = None
    
    def register_agent(self) -> bool:
        """Register this agent with Microsoft Agent Framework.
        
        Reuses existing agents to avoid creating duplicates on each run.
        
        Returns:
            True if registration successful, False otherwise
        """
        # Check SDK availability and configuration
        if not AGENT_SDK_AVAILABLE:
            print(f"⚠️  Cannot register {self.name} - Microsoft Agent Framework not available")
            if AGENT_SDK_ERROR:
                print(f"   Error: {AGENT_SDK_ERROR}")
            print(f"   Install with: pip install agent-framework-azure-ai --pre")
            print(f"   Note: This is a preview SDK, use --pre flag")
            return False
        
        # Check for None types (import failure)
        if ChatAgent is None or AzureAIAgentClient is None:
            print(f"⚠️  Cannot register {self.name} - SDK classes not available")
            print(f"   SDK might be partially installed or incompatible version")
            print(f"   Try: pip uninstall agent-framework-azure-ai && pip install agent-framework-azure-ai --pre")
            return False
        
        # Display SDK version
        if AGENT_SDK_VERSION:
            print(f"   📦 Using Microsoft Agent Framework v{AGENT_SDK_VERSION}")
        
        if not Config.AZURE_AI_PROJECT_ENDPOINT:
            print(f"⚠️  Cannot register {self.name} - AZURE_AI_PROJECT_ENDPOINT not configured")
            print(f"   Set this environment variable in your .env file")
            print(f"   Example: AZURE_AI_PROJECT_ENDPOINT=https://your-project.aiservices.azure.com")
            return False
        
        # Check if agent already exists in registry (in-memory cache)
        if self.name in BaseAgent._agent_registry:
            existing = BaseAgent._agent_registry[self.name]
            self.agent = existing['agent']
            self._chat_client = existing['chat_client']
            self.agent_id = existing['agent_id']
            print(f"   ♻️  Reusing existing agent: {self.name}")
            return True
        
        try:
            print(f"   Creating agent: {self.name}...")
            
            # Create ChatAgent with Azure AI backend
            from azure.identity import DefaultAzureCredential
            
            # Use SHARED client (singleton pattern) to prevent duplicate agent creation in Foundry
            # The client is what actually creates agents in Foundry, so we must reuse it
            if not BaseAgent._client_initialized or BaseAgent._shared_client is None:
                print(f"   🔧 Initializing shared Azure AI Agent Client (first time only)...")
                
                # Extract project_id from endpoint if available
                project_id = None
                if Config.AZURE_AI_PROJECT_ENDPOINT:
                    import re
                    match = re.search(r'https://([^.]+)', Config.AZURE_AI_PROJECT_ENDPOINT)
                    if match:
                        project_id = match.group(1)
                        print(f"   📍 Project: {project_id}")
                
                # Build minimal client params (no agent_name - that would create agent)
                client_params = {
                    'project_endpoint': Config.AZURE_AI_PROJECT_ENDPOINT,
                    'model_deployment_name': self.model,
                    'async_credential': DefaultAzureCredential()
                }
                
                # Initialize shared client (only once for all agents)
                try:
                    BaseAgent._shared_client = AzureAIAgentClient(**client_params)
                    BaseAgent._client_initialized = True
                    print(f"   ✅ Shared client initialized")
                except TypeError as te:
                    print(f"   ⚠️  Client init failed, trying minimal config...")
                    minimal_params = {
                        'project_endpoint': Config.AZURE_AI_PROJECT_ENDPOINT,
                        'model_deployment_name': self.model,
                        'async_credential': DefaultAzureCredential()
                    }
                    BaseAgent._shared_client = AzureAIAgentClient(**minimal_params)
                    BaseAgent._client_initialized = True
            else:
                print(f"   ♻️  Reusing shared Azure AI Agent Client")
            
            # Use the shared client
            self._chat_client = BaseAgent._shared_client
            
            # IMPORTANT: Check if agent already exists in Azure AI Foundry
            # This prevents creating duplicate agents across different Python runs
            try:
                print(f"   🔍 Checking Azure AI Foundry for existing '{self.name}' agent...")
                existing_agents = self._chat_client.agents.list()
                
                for existing_agent in existing_agents:
                    agent_name = getattr(existing_agent, 'name', None)
                    if agent_name == self.name:
                        print(f"   ♻️  Found existing agent in Foundry: {self.name}")
                        self.agent = existing_agent
                        self.agent_id = getattr(existing_agent, 'agent_id', None) or getattr(existing_agent, 'id', None)
                        
                        # Store in registry for this session
                        BaseAgent._agent_registry[self.name] = {
                            'agent': self.agent,
                            'chat_client': self._chat_client,
                            'agent_id': self.agent_id
                        }
                        
                        if self.agent_id:
                            print(f"   🆔 Agent ID: {self.agent_id}")
                        print(f"   ✅ Reusing: {self.name} (from Azure AI Foundry)")
                        return True
                
                print(f"   ➕ No existing agent found, creating new one in Foundry...")
            except Exception as list_error:
                print(f"   ⚠️  Could not list existing agents: {list_error}")
                print(f"   ➕ Proceeding with agent creation...")
            
            # Use the shared client
            self._chat_client = BaseAgent._shared_client
            
            # Setup connected_agents for delegation (empty for now, will be linked later)
            connected_agents = []
            
            agent_params = {
                'name': self.name,  # CRITICAL: Set agent name for Azure AI Foundry visibility
                'chat_client': self._chat_client,
                'instructions': self.system_prompt
            }
            
            # Add tools if available (preview feature)
            if self.tools:
                try:
                    agent_params['tools'] = self.tools
                except (TypeError, AttributeError):
                    print(f"   ⚠️  Tools not supported in this SDK version")
            
            # Add connected_agents for delegation graph (MAF preview feature)
            if hasattr(self, '_connected_agent_names'):
                try:
                    agent_params['connected_agents'] = self._connected_agent_names
                except (TypeError, AttributeError):
                    print(f"   ⚠️  Connected agents not supported in this SDK version")
            
            # Initialize ChatAgent with error handling
            try:
                self.agent = ChatAgent(**agent_params)
            except TypeError as te:
                # SDK version mismatch - try minimal params
                print(f"   ⚠️  ChatAgent parameter mismatch, using minimal config...")
                if self._chat_client is None:
                    print(f"   Chat client is not initialized")
                    return False
                self.agent = ChatAgent(
                    name=self.name,  # Always include name
                    chat_client=self._chat_client,
                    instructions=self.system_prompt
                )
            
            # Store in registry to reuse
            BaseAgent._agent_registry[self.name] = {
                'agent': self.agent,
                'chat_client': self._chat_client,
                'agent_id': getattr(self.agent, 'agent_id', None) or getattr(self.agent, 'id', None)
            }
            
            # Store agent_id for delegation
            self.agent_id = BaseAgent._agent_registry[self.name]['agent_id']
            if self.agent_id:
                print(f"   🆔 Agent ID: {self.agent_id}")
            
            print(f"   ✅ Registered: {self.name}")
            return True
            
        except ImportError as ie:
            print(f"   ❌ Failed to register {self.name}: Import error")
            print(f"   Details: {ie}")
            print(f"   This usually means the SDK is not installed or version mismatch")
            print(f"   Try: pip install agent-framework-azure-ai --pre --upgrade")
            return False
            
        except TypeError as te:
            print(f"   ❌ Failed to register {self.name}: Parameter type mismatch")
            print(f"   Details: {te}")
            print(f"   This usually means SDK version doesn't support the parameters used")
            print(f"   Try: pip install agent-framework-azure-ai --pre --upgrade")
            return False
            
        except AttributeError as ae:
            print(f"   ❌ Failed to register {self.name}: Missing SDK attribute")
            print(f"   Details: {ae}")
            print(f"   SDK might be incomplete or wrong version")
            print(f"   Try: pip uninstall agent-framework-azure-ai && pip install agent-framework-azure-ai --pre")
            return False
            
        except Exception as e:
            print(f"   ❌ Failed to register {self.name}: Unexpected error")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Details: {e}")
            import traceback
            print(f"   Stack trace:")
            traceback.print_exc()
            return False
    
    def connect_to_agents(self, agent_names: list) -> None:
        """Connect this agent to other agents for delegation.
        
        This sets up the delegation graph for Microsoft Agent Framework.
        Must be called before register_agent() for proper workflow graphs.
        
        Args:
            agent_names: List of agent names this agent can delegate to
        """
        self._connected_agent_names = agent_names
        print(f"   🔗 {self.name} connected to: {', '.join(agent_names)}")
    
    async def delegate_to(self, target_agent_name: str, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Delegate work to another registered agent using MAF's delegation system.
        
        This method leverages MAF's connected_agents feature when available,
        falling back to direct execution for broader compatibility.
        
        Args:
            target_agent_name: Name of the agent to delegate to
            message: Message/task for the target agent
            context: Optional context dictionary
            
        Returns:
            Response from the target agent
        """
        # Import here to avoid circular dependency
        from agents.specialized_agents import get_agent
        
        target = get_agent(target_agent_name)
        if not target:
            return f"Error: Agent '{target_agent_name}' not found in registry. Available: {list(BaseAgent._agent_registry.keys())}"
        
        # Check if both agents are properly initialized
        if not self.agent:
            return f"Error: {self.name} not initialized. Call register_agent() first."
        
        if not target.agent:
            return f"Error: {target_agent_name} not initialized. Call register_agent() first."
        
        # Try MAF's native delegation if connected_agents is set up
        if hasattr(self.agent, 'connected_agents') and self.agent.connected_agents:
            try:
                # Check if target is in connected agents
                target_id = target.agent_id
                if target_id:
                    connected_ids = [getattr(a, 'id', None) or getattr(a, 'agent_id', None) for a in self.agent.connected_agents]
                    if target_id in connected_ids:
                        print(f"   🔄 {self.name} → {target_agent_name} (MAF delegation)")
                        
                        # Use MAF's native delegate method if available
                        if hasattr(self.agent, 'delegate'):
                            return await self.agent.delegate(
                                target_agent_id=target_id,
                                message=message
                            )
            except (AttributeError, TypeError) as e:
                # MAF delegation not available, fall through to direct call
                print(f"   ℹ️  MAF delegation not available ({e}), using direct call")
        
        # Fallback: Direct execution (always works)
        print(f"   📞 {self.name} → {target_agent_name} (direct call)")
        return await target.execute_async(message, context or {})
    
    async def execute_async(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Execute the agent asynchronously using Microsoft Agent Framework.
        
        Native async support - no thread pool executors needed!
        
        Args:
            user_message: The user's message or task
            context: Optional context from previous agents
            
        Returns:
            Agent's response
        """
        # Check SDK availability
        if not AGENT_SDK_AVAILABLE:
            return f"Error: Microsoft Agent Framework not available for {self.name}"
        
        if not self.agent:
            return f"Error: {self.name} not registered. Call register_agent() first."
        
        # Build full message with context
        full_message = user_message
        if context:
            context_str = self._format_context(context)
            full_message = f"Context from previous steps:\n{context_str}\n\n{user_message}"
        
        try:
            # Agent Framework handles everything - just call run()
            result = await self.agent.run(full_message)
            return str(result)
            
        except Exception as e:
            return f"Error in {self.name}: {str(e)}"
    
    # ==================== Inter-Agent Communication Methods ====================
    
    async def send_message_to_agent(self, target_agent_name: str, message: str, message_type: str = "info") -> bool:
        """Send a message to another agent via shared message queue.
        
        Args:
            target_agent_name: Name of the recipient agent
            message: Message content
            message_type: Type of message ('info', 'query', 'handover', 'result')
            
        Returns:
            True if message was queued successfully
        """
        message_obj = {
            "from": self.name,
            "to": target_agent_name,
            "message": message,
            "type": message_type,
            "timestamp": self._get_timestamp()
        }
        
        BaseAgent._shared_context["messages"].append(message_obj)
        BaseAgent._communication_log.append(f"[MSG] {self.name} → {target_agent_name}: {message[:100]}...")
        
        print(f"   📨 {self.name} → {target_agent_name}: {message_type.upper()}")
        return True
    
    async def query_agent(self, target_agent_name: str, query: str) -> Optional[str]:
        """Query another agent and wait for response.
        
        This enables agents to ask each other for clarifications or additional context.
        
        Args:
            target_agent_name: Agent to query
            query: Question or request
            
        Returns:
            Response from the target agent, or None if agent not found
        """
        # Check if target agent exists in registry
        target_agent_data = BaseAgent._agent_registry.get(target_agent_name)
        if not target_agent_data:
            print(f"   ⚠️  Agent '{target_agent_name}' not found in registry")
            return None
        
        print(f"   🔄 {self.name} querying {target_agent_name}...")
        
        # Send query message
        await self.send_message_to_agent(target_agent_name, query, "query")
        
        # Get target agent instance and execute query
        # In a real GroupChat scenario, this would go through a message broker
        # For now, we directly invoke the agent
        target_agent = target_agent_data.get('agent')
        if target_agent:
            response = await target_agent.run(query)
            
            # Log the response
            await self.send_message_to_agent(
                self.name, 
                f"Response to query: {str(response)[:200]}",
                "result"
            )
            
            print(f"   ✅ {target_agent_name} responded to {self.name}")
            return str(response)
        
        return None
    
    def publish_state(self, state_key: str, state_value: Any) -> None:
        """Publish state to shared context for other agents to access.
        
        Args:
            state_key: Key identifying the state (e.g., 'requirements', 'code_analysis')
            state_value: Value to store (can be dict, list, string, etc.)
        """
        BaseAgent._shared_context["states"][state_key] = state_value
        BaseAgent._communication_log.append(f"[STATE] {self.name} published '{state_key}'")
        print(f"   📤 {self.name} published state: {state_key}")
    
    def get_shared_state(self, state_key: str) -> Optional[Any]:
        """Retrieve shared state published by another agent.
        
        Args:
            state_key: Key of the state to retrieve
            
        Returns:
            The state value, or None if not found
        """
        state_value = BaseAgent._shared_context["states"].get(state_key)
        if state_value:
            print(f"   📥 {self.name} retrieved state: {state_key}")
        return state_value
    
    def request_handover(self, target_agent_name: str, context: str, reason: str) -> None:
        """Request handover to another agent with context.
        
        Args:
            target_agent_name: Agent to hand over to
            context: Context information to pass
            reason: Reason for handover
        """
        handover_obj = {
            "from": self.name,
            "to": target_agent_name,
            "context": context,
            "reason": reason,
            "timestamp": self._get_timestamp()
        }
        
        BaseAgent._shared_context["handovers"].append(handover_obj)
        BaseAgent._communication_log.append(f"[HANDOVER] {self.name} → {target_agent_name}: {reason}")
        print(f"   🤝 {self.name} requesting handover to {target_agent_name}: {reason}")
    
    @classmethod
    def get_messages_for_agent(cls, agent_name: str) -> list:
        """Get all unread messages for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of messages addressed to this agent
        """
        return [msg for msg in cls._shared_context["messages"] if msg["to"] == agent_name]
    
    @classmethod
    def get_communication_log(cls) -> list:
        """Get full communication log for debugging."""
        return cls._communication_log.copy()
    
    @classmethod
    def clear_shared_context(cls) -> None:
        """Clear shared context (useful for starting fresh workflow)."""
        cls._shared_context = {
            "messages": [],
            "states": {},
            "handovers": []
        }
        cls._communication_log = []
        print("   🧹 Shared context cleared")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for logging."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ===========================================================================
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into a readable string"""
        lines = []
        for key, value in context.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

