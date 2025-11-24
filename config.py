"""Configuration management for Universal Documentation Agent"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

# Load environment variables
load_dotenv()

# Check SDK availability with version validation
AGENT_SDK_AVAILABLE = False
AGENT_SDK_VERSION = None
AGENT_SDK_ERROR = None

try:
    # Try importing the SDK
    from agent_framework.azure import AzureAIAgentClient
    from agent_framework import ChatAgent
    
    # Try to get version info
    try:
        import agent_framework
        AGENT_SDK_VERSION = getattr(agent_framework, '__version__', 'unknown')
    except:
        AGENT_SDK_VERSION = 'unknown'
    
    AGENT_SDK_AVAILABLE = True
    
except ImportError as e:
    AGENT_SDK_AVAILABLE = False
    AGENT_SDK_ERROR = str(e)
    AzureAIAgentClient = None  # type: ignore
    ChatAgent = None  # type: ignore
    
except Exception as e:
    # Handle other SDK initialization errors
    AGENT_SDK_AVAILABLE = False
    AGENT_SDK_ERROR = f"SDK initialization failed: {str(e)}"
    AzureAIAgentClient = None  # type: ignore
    ChatAgent = None  # type: ignore

class Config:
    """Application configuration"""
    
    # Azure AI Foundry Project Settings
    AZURE_AI_PROJECT_ENDPOINT: Optional[str] = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    DEPLOYMENT_NAME: str = os.getenv("DEPLOYMENT_NAME", "gpt-4o-mini")
    
    # Azure Project Metadata (Required for proper agent registration per MAF docs)
    AZURE_SUBSCRIPTION_ID: Optional[str] = os.getenv("AZURE_SUBSCRIPTION_ID")
    AZURE_RESOURCE_GROUP: Optional[str] = os.getenv("AZURE_RESOURCE_GROUP")
    AZURE_PROJECT_NAME: Optional[str] = os.getenv("AZURE_PROJECT_NAME")
    
    # Azure AI Search Settings (Optional)
    AZURE_SEARCH_ENDPOINT: Optional[str] = os.getenv("AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_KEY: Optional[str] = os.getenv("AZURE_SEARCH_KEY")
    AZURE_SEARCH_INDEX_NAME: str = os.getenv("AZURE_SEARCH_INDEX_NAME", "docs-index")
    
    # Azure Document Intelligence Settings (Optional)
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: Optional[str] = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    AZURE_DOCUMENT_INTELLIGENCE_KEY: Optional[str] = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    
    # Application Settings
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "outputs"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Model Settings (now configurable via env vars)
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    @classmethod
    def get_env_var(cls, key: str, default: str = "") -> str:
        """Get environment variable with default fallback
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)
    
    @classmethod
    def get_config_mode(cls) -> str:
        """Determine which configuration mode is active.
        
        Returns:
            'foundry' - Azure AI Foundry
            'none' - No valid configuration
        """
        if cls.AZURE_AI_PROJECT_ENDPOINT:
            return 'foundry'
        else:
            return 'none'
    
    @classmethod
    def is_foundry_mode(cls) -> bool:
        """Check if Azure AI Foundry mode is active"""
        return cls.get_config_mode() == 'foundry'
    
    @classmethod
    def has_agents_support(cls) -> bool:
        """Check if Microsoft Agent Framework is available and configured"""
        return AGENT_SDK_AVAILABLE and cls.is_foundry_mode()
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.AZURE_AI_PROJECT_ENDPOINT:
            raise ValueError(
                "Configuration incomplete. Must provide AZURE_AI_PROJECT_ENDPOINT for Azure AI Foundry."
            )
        
        # Ensure output directory exists
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        return True
    
    @classmethod
    def validate_agent_config(cls) -> bool:
        """Validate configuration for Microsoft Agent Framework.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ImportError: If SDK not available
            ValueError: If AZURE_AI_PROJECT_ENDPOINT not configured
        """
        # Check SDK availability
        if not AGENT_SDK_AVAILABLE:
            error_msg = "Microsoft Agent Framework not available."
            if AGENT_SDK_ERROR:
                error_msg += f"\nError: {AGENT_SDK_ERROR}"
            error_msg += "\nInstall with: pip install agent-framework-azure-ai --pre"
            raise ImportError(error_msg)
        
        # Check Foundry configuration
        if not cls.AZURE_AI_PROJECT_ENDPOINT:
            raise ValueError(
                "AZURE_AI_PROJECT_ENDPOINT not configured. "
                "Set this environment variable to your Azure AI Foundry project endpoint."
            )
        
        return True
    
    @classmethod
    def get_sdk_diagnostics(cls) -> dict:
        """Get detailed SDK diagnostics for troubleshooting.
        
        Returns:
            Dictionary with SDK status and recommendations
        """
        diagnostics = {
            'sdk_available': AGENT_SDK_AVAILABLE,
            'sdk_version': AGENT_SDK_VERSION,
            'sdk_error': AGENT_SDK_ERROR,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'config_valid': False,
            'issues': [],
            'recommendations': []
        }
        
        # Check SDK availability
        if not AGENT_SDK_AVAILABLE:
            diagnostics['issues'].append('SDK not installed or import failed')
            diagnostics['recommendations'].append('pip install agent-framework-azure-ai --pre')
            if AGENT_SDK_ERROR:
                diagnostics['issues'].append(f'Import error: {AGENT_SDK_ERROR}')
        
        # Check configuration
        if not cls.AZURE_AI_PROJECT_ENDPOINT:
            diagnostics['issues'].append('AZURE_AI_PROJECT_ENDPOINT not set')
            diagnostics['recommendations'].append('Set AZURE_AI_PROJECT_ENDPOINT in .env file')
        
        # Check optional but recommended config
        if not cls.AZURE_SUBSCRIPTION_ID:
            diagnostics['recommendations'].append('Set AZURE_SUBSCRIPTION_ID for better Azure integration')
        
        if not cls.AZURE_RESOURCE_GROUP:
            diagnostics['recommendations'].append('Set AZURE_RESOURCE_GROUP for better Azure integration')
        
        # Overall status
        diagnostics['config_valid'] = (
            AGENT_SDK_AVAILABLE and 
            cls.AZURE_AI_PROJECT_ENDPOINT is not None
        )
        
        return diagnostics
    
    @classmethod
    def _get_mock_client(cls):
        """Return a mock AzureAIAgentClient for testing when SDK unavailable.
        
        This enables graceful degradation in development/testing environments.
        """
        class MockAzureAIClient:
            """Mock Azure AI Client for testing"""
            def __init__(self):
                self._mock = True
                
            def __getattr__(self, name):
                def method(*args, **kwargs):
                    raise NotImplementedError(
                        f"Mock client: {name}() not implemented. "
                        f"Install agent-framework-azure-ai SDK for real functionality."
                    )
                return method
        
        import warnings
        warnings.warn(
            "Using mock AzureAIClient. Install agent-framework-azure-ai --pre for real functionality.",
            UserWarning
        )
        return MockAzureAIClient()
