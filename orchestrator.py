"""Multi-Agent Orchestration Workflow for Documentation Generation using Azure AI Foundry"""

import json
import re
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime

from agents import (
    DispatcherAgent,
    RequirementAnalystAgent,
    CodeResearcherAgent,
    TechnicalWriterAgent,
    SecurityReviewerAgent,
    EditorFormatterAgent
)
from agents.base_agent import BaseAgent
from tools import FileTools, CodeAnalysisTools
from config import Config
from delegation_coordinator import DelegationCoordinator


class DocumentationOrchestrator:
    """Orchestrates the multi-agent workflow for documentation generation"""
    
    # Extensible document type registry with aliases
    DOC_TYPE_REGISTRY = {
        "BRD": ["BRD", "BUSINESS", "BUSINESS_REQUIREMENTS"],
        "FRD": ["FRD", "FUNCTIONAL", "FNRD", "FUNCTIONAL_REQUIREMENTS"],
        "NFRD": ["NFRD", "NON-FUNCTIONAL", "NON_FUNCTIONAL", "NONFUNCTIONAL"],
        "CLOUD": ["CLOUD", "DEPLOYMENT", "IMPLEMENTATION", "INFRASTRUCTURE"],
        "SECURITY": ["SECURITY", "COMPLIANCE", "SECURITY_COMPLIANCE"],
        "API": ["API", "API_DOCUMENTATION", "REST_API"],
        "GENERIC": ["GENERIC", "GENERAL", "OTHER"]
    }
    
    def __init__(self):
        """Initialize all agents and register them in Azure AI Foundry"""
        print("\n🔧 Initializing Documentation Agent System...")
        
        self.dispatcher = DispatcherAgent()
        self.analyst = RequirementAnalystAgent()
        self.researcher = CodeResearcherAgent()
        self.writer = TechnicalWriterAgent()
        self.security_reviewer = SecurityReviewerAgent()
        self.editor = EditorFormatterAgent()
        
        self.file_tools = FileTools()
        self.code_tools = CodeAnalysisTools()
        
        self.context = {}
        self.workflow_log = []
        self._max_log_size = 1000  # Max chars per log entry to prevent memory bloat
        
        # Token management (approximate: 1 token ≈ 4 characters)
        self._max_input_tokens = Config.MAX_TOKENS * 0.7  # Reserve 30% for output
        self._chars_per_token = 4
        self._max_input_chars = int(self._max_input_tokens * self._chars_per_token)
        
        # Delegation coordinator for multi-agent collaboration
        self.delegation_coordinator = DelegationCoordinator(self)
        
        # Register all agents in Azure AI Foundry
        self._register_agents()
    
    def _register_agents(self):
        """Register all agents in Azure AI Foundry"""
        print("\n📋 Registering agents in Azure AI Foundry...")
        
        agents = [
            self.dispatcher,
            self.analyst,
            self.researcher,
            self.writer,
            self.security_reviewer,
            self.editor
        ]
        
        success_count = 0
        for agent in agents:
            if agent.register_agent():
                success_count += 1
        
        if success_count == len(agents):
            print(f"✅ All {success_count} agents registered successfully!\n")
        else:
            print(f"⚠️  {success_count}/{len(agents)} agents registered\n")
        
        # Display delegation graph if all agents registered
        if success_count == len(agents):
            from agents.specialized_agents import print_delegation_graph
            print_delegation_graph()

    async def generate_documentation_async(
        self,
        user_request: str,
        code_directory: Optional[str] = None,
        input_files: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Async documentation generation using MAF delegation coordination.
        
        NOW WITH AUTO-TRIGGER CONVERSATIONAL MODE:
        - If dispatcher detects ambiguous request → automatically launches conversational clarification
        - Uses DelegationCoordinator for multi-agent collaboration
        - Parallel execution (Analyst + Researcher work simultaneously)
        - Agent-to-agent delegation via connected_agents graph
        - State sharing through publish_state/get_shared_context
        - Dynamic workflow routing based on Dispatcher analysis
        
        Args:
            user_request: User's description of what documentation they need
            code_directory: Optional directory containing source code to analyze
            input_files: Optional list of specific files to analyze
        
        Returns:
            Dictionary containing the generated document and metadata
        """
        print("\n🚀 Starting Documentation Generation with Delegation Coordination\n")
        self._log_step("Workflow Started", {"request": user_request, "mode": "delegation"})
        
        # Build context for delegation coordinator
        context = {
            'code_directory': code_directory,
            'input_files': input_files
        }
        
        # Use delegation coordinator for multi-agent collaboration
        result = await self.delegation_coordinator.coordinate(user_request, context)
        
        # AUTO-TRIGGER CONVERSATIONAL MODE IF NEEDED
        if result.get("status") == "needs_clarification":
            print("\n" + "="*70)
            print("🤖 INTELLIGENT CLARIFICATION MODE ACTIVATED")
            print("="*70)
            print("\n💭 Your request needs more details. Let me ask a few questions...\n")
            
            # Lazy import to avoid circular dependency
            from conversation_manager import ConversationalOrchestrator, ConversationContext
            
            # Create conversational orchestrator on-the-fly
            conv_orchestrator = ConversationalOrchestrator(self)
            
            # Initialize context with user request and code/files
            conv_context = ConversationContext(
                user_request=user_request,
                code_directory=code_directory,
                input_files=input_files
            )
            
            # Pre-populate with dispatcher insights if available
            dispatch_info = result.get("dispatch_info", {})
            if dispatch_info.get("clarification_questions"):
                conv_context.last_questions = dispatch_info["clarification_questions"]
            
            conv_orchestrator.context = conv_context
            
            # Start interactive conversation loop
            result = await conv_orchestrator._analyze_and_clarify()
            
            # Interactive conversation loop - keep asking until ready
            while result.get('status') == 'needs_clarification':
                print("\n" + "─" * 70)
                
                # Get user input
                import sys
                user_response = input("\n💭 Your response (or 'proceed' to continue with defaults): ").strip()
                
                if user_response.lower() in ['proceed', 'continue', 'skip']:
                    print("\n   ⚡ Proceeding with available information...\n")
                    # Force generation by setting max rounds
                    if conv_orchestrator.context:
                        conv_orchestrator.context.clarification_round = conv_orchestrator.context.max_clarification_rounds
                        result = await conv_orchestrator._analyze_and_clarify()
                    else:
                        print("   ❌ Error: No conversation context available")
                        return {"status": "error", "message": "No conversation context"}
                    break
                
                if not user_response:
                    print("   ⚠️  Please provide a response or type 'proceed' to continue.\n")
                    continue
                
                # Process the user's response
                result = await conv_orchestrator.process_user_response(user_response)
            
            # After conversation completes, check final result
            if result.get('status') == 'completed' or result.get('document'):
                return result
            
            # If conversation finished but needs generation, trigger it
            if conv_orchestrator.context and conv_orchestrator.context.confidence_score >= 0.7:
                # Enrich the original request with gathered information
                enriched_request = user_request
                if conv_orchestrator.context.gathered_info:
                    enriched_request += "\n\nAdditional Context:\n"
                    for key, value in conv_orchestrator.context.gathered_info.items():
                        enriched_request += f"- {key}: {value}\n"
                
                # Recurse with enriched request (won't trigger clarification again due to higher confidence)
                return await self.generate_documentation_async(
                    enriched_request,
                    code_directory,
                    input_files
                )
            
            return result
        
        return result
    
    async def _analyze_code(self, code_directory: Optional[str], input_files: Optional[list]) -> str:
        """Analyze code files and generate summary with token management"""
        code_files = {}
        
        if code_directory:
            # Read with file size limits using async I/O
            code_files = await self.file_tools.read_code_files_async(
                code_directory,
                max_file_size=5 * 1024 * 1024
            )
        elif input_files:
            # Read files concurrently using aiofiles
            import aiofiles
            async def read_single(file_path: str) -> tuple:
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        if len(content) > 5 * 1024 * 1024:
                            content = content[:5 * 1024 * 1024] + "\n[Truncated]"
                        return (file_path, content)
                except Exception as e:
                    return (file_path, f"Error reading: {str(e)}")
            
            tasks = [read_single(fp) for fp in input_files]
            results = await asyncio.gather(*tasks)
            code_files = dict(results)
        
        if not code_files:
            return "No code files found or error reading files."
        
        # Create summary with token awareness
        code_summary = self.code_tools.extract_code_summary(code_files, max_lines_per_file=50, use_ast_parsing=True)
        
        # Validate and truncate if needed
        _, code_summary = self._validate_content_size(code_summary, 3000)
        
        # Use Code Researcher agent to analyze
        research_prompt = f"""Analyze this codebase and provide:
1. Architecture overview
2. Key components and their responsibilities
3. Dependencies and integrations
4. Technical patterns used
5. Important configuration or setup requirements

{code_summary}
"""
        
        # Pass workflow context to researcher for better analysis
        analysis = await self.researcher.execute_async(research_prompt, self.context)
        return analysis
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from agent response with robust error handling"""
        if not response or not isinstance(response, str):
            return {}
        
        # Strategy 1: Try direct JSON parse (cleanest responses)
        try:
            return json.loads(response)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Strategy 2: Find JSON object in markdown code blocks
        json_block_pattern = r'```(?:json)?\s*({[^`]+})\s*```'
        match = re.search(json_block_pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                return json.loads(match.group(1))
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Strategy 3: Find JSON object anywhere in text
        try:
            start = response.find('{')
            if start != -1:
                # Find matching closing brace with proper nesting
                depth = 0
                for i in range(start, len(response)):
                    if response[i] == '{':
                        depth += 1
                    elif response[i] == '}':
                        depth -= 1
                        if depth == 0:
                            json_str = response[start:i+1]
                            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError, IndexError):
            pass
        
        # Strategy 4: Try to extract key-value pairs with regex
        try:
            result = {}
            # Extract common fields
            if 'needs_clarification' in response.lower():
                result['needs_clarification'] = 'true' in response.lower() or 'yes' in response.lower()
            
            # Extract document_type
            doc_type_match = re.search(r'["\']?document_type["\']?\s*:\s*["\']?([A-Z_]+)["\']?', response, re.IGNORECASE)
            if doc_type_match:
                result['document_type'] = doc_type_match.group(1)
            
            # Extract workflow
            workflow_match = re.search(r'["\']?workflow["\']?\s*:\s*["\']?(\w+)["\']?', response, re.IGNORECASE)
            if workflow_match:
                result['workflow'] = workflow_match.group(1)
            
            if result:
                return result
        except Exception:
            pass
        
        return {}
    
    def _normalize_doc_type(self, doc_type) -> str:
        """Normalize document type using extensible registry"""
        # Handle list of document types (take first one)
        if isinstance(doc_type, list):
            if not doc_type:
                return "GENERIC"
            doc_type = doc_type[0]
        
        # Handle non-string types
        if not isinstance(doc_type, str):
            doc_type = str(doc_type)
        
        doc_type_clean = doc_type.upper().strip().replace("-", "_")
        
        # Check registry for matches
        for standard_type, aliases in self.DOC_TYPE_REGISTRY.items():
            # Direct match
            if doc_type_clean == standard_type:
                return standard_type
            # Alias match
            for alias in aliases:
                if alias in doc_type_clean or doc_type_clean in alias:
                    return standard_type
        
        # No match found - return GENERIC
        return "GENERIC"
    
    @classmethod
    def register_custom_doc_type(cls, standard_name: str, aliases: List[str]):
        """Register a custom document type
        
        Args:
            standard_name: Standard name for the document type (e.g., 'ARCHITECTURE')
            aliases: List of alternative names/keywords (e.g., ['ARCH', 'DESIGN', 'SYSTEM_DESIGN'])
        
        Example:
            DocumentationOrchestrator.register_custom_doc_type('ARCHITECTURE', ['ARCH', 'DESIGN'])
        """
        cls.DOC_TYPE_REGISTRY[standard_name.upper()] = [standard_name.upper()] + [a.upper() for a in aliases]
    
    def _log_step(self, step_name: str, data: Dict[str, Any]):
        """Log workflow step with size limits to prevent memory bloat"""
        # Truncate large data values
        truncated_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                truncated_data[key] = self._truncate_for_log(value)
            else:
                truncated_data[key] = value
        
        self.workflow_log.append({
            "step": step_name,
            "timestamp": self._get_timestamp(),
            "data": truncated_data
        })
    
    def _truncate_for_log(self, text: str) -> str:
        """Truncate text for logging to prevent memory bloat"""
        if not isinstance(text, str) or len(text) <= self._max_log_size:
            return text
        return text[:self._max_log_size] + f"... [truncated {len(text) - self._max_log_size} chars]"
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text (approximate: 1 token ≈ 4 chars)."""
        return len(text) // self._chars_per_token
    
    def _truncate_to_token_limit(self, text: str, max_tokens: Optional[int] = None) -> str:
        """Truncate text to stay within token limits."""
        if max_tokens is None:
            max_tokens = int(self._max_input_tokens)
        
        max_chars = max_tokens * self._chars_per_token
        
        if len(text) <= max_chars:
            return text
        
        # Intelligent truncation: try to keep beginning and end
        keep_start = int(max_chars * 0.7)
        keep_end = max_chars - keep_start
        
        truncated = (
            text[:keep_start] + 
            f"\n\n... [Content truncated for token limit: {len(text) - max_chars} chars omitted] ...\n\n" +
            text[-keep_end:]
        )
        return truncated
    
    def _chunk_content(self, content: str, chunk_size_tokens: int = 3000) -> List[str]:
        """Split content into chunks that fit within token limits."""
        chunk_size_chars = chunk_size_tokens * self._chars_per_token
        chunks = []
        
        for i in range(0, len(content), chunk_size_chars):
            chunk = content[i:i + chunk_size_chars]
            chunks.append(chunk)
        
        return chunks
    
    def _validate_content_size(self, content: str, max_tokens: Optional[int] = None) -> Tuple[bool, str]:
        """Validate content size and return (is_valid, processed_content)."""
        estimated_tokens = self._estimate_tokens(content)
        max_allowed = max_tokens or int(self._max_input_tokens)
        
        if estimated_tokens <= max_allowed:
            return (True, content)
        
        print(f"   ⚠️  Content size ({estimated_tokens} tokens) exceeds limit ({max_allowed} tokens)")
        print(f"   🔧 Auto-truncating to fit within limits...")
        
        truncated = self._truncate_to_token_limit(content, max_allowed)
        return (False, truncated)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _contains_security_keywords(self, text: str) -> bool:
        """Check if document contains security-related keywords that warrant review."""
        security_keywords = [
            'authentication', 'authorization', 'password', 'token', 'api key',
            'encryption', 'decrypt', 'ssl', 'tls', 'certificate', 'credential',
            'secret', 'security', 'vulnerability', 'attack', 'threat', 'compliance',
            'gdpr', 'hipaa', 'pci', 'oauth', 'jwt', 'firewall', 'access control',
            'privilege', 'permission', 'session', 'inject', 'xss', 'csrf', 'sql'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in security_keywords)
    
    def _assess_document_quality(self, document: str, doc_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess document quality and assign confidence flags.
        
        Returns quality assessment with flags for potential issues.
        """
        assessment = {
            'confidence': 'high',
            'flags': [],
            'issues': [],
            'word_count': len(document.split()),
            'has_sections': False,
            'completeness_score': 0.0
        }
        
        # Check document length
        if assessment['word_count'] < 500:
            assessment['confidence'] = 'low'
            assessment['flags'].append('low_confidence')
            assessment['issues'].append('Document too short (< 500 words)')
        elif assessment['word_count'] < 1000:
            assessment['confidence'] = 'medium'
            assessment['issues'].append('Document relatively short (< 1000 words)')
        
        # Check for standard sections
        section_indicators = ['#', '##', '###', 'Introduction', 'Overview', 'Requirements', 'Conclusion']
        assessment['has_sections'] = any(indicator in document for indicator in section_indicators)
        
        if not assessment['has_sections']:
            assessment['confidence'] = 'low'
            assessment['flags'].append('low_confidence')
            assessment['issues'].append('Missing standard document sections')
        
        # Check if document has meaningful content (not just error messages)
        error_indicators = ['Error:', 'Failed:', 'not available', 'not found', 'Exception']
        if any(indicator in document for indicator in error_indicators):
            assessment['confidence'] = 'low'
            assessment['flags'].append('low_confidence')
            assessment['issues'].append('Document contains error messages')
        
        # Check for placeholder text
        placeholders = ['TODO', 'TBD', '[Insert', '[Add', 'PLACEHOLDER']
        if any(placeholder in document for placeholder in placeholders):
            assessment['confidence'] = 'medium'
            assessment['issues'].append('Document contains placeholder text')
        
        # Calculate completeness score
        completeness_factors = [
            assessment['word_count'] >= 1000,
            assessment['has_sections'],
            len([s for s in section_indicators if s in document]) >= 3,
            'requirements' in document.lower() or 'specification' in document.lower(),
            len(document.split('\n')) >= 20
        ]
        assessment['completeness_score'] = sum(completeness_factors) / len(completeness_factors)
        
        if assessment['completeness_score'] < 0.5:
            assessment['confidence'] = 'low'
            assessment['flags'].append('low_confidence')
            assessment['issues'].append(f'Low completeness score: {assessment["completeness_score"]:.2f}')
        
        return assessment
    
    def _display_communication_summary(self) -> None:
        """Display summary of inter-agent communications."""
        from agents.base_agent import BaseAgent
        
        comm_log = BaseAgent.get_communication_log()
        
        if comm_log:
            print("\n" + "=" * 70)
            print("📡 INTER-AGENT COMMUNICATION SUMMARY")
            print("=" * 70)
            
            for entry in comm_log:
                print(f"   {entry}")
            
            # Display shared states
            shared_states = BaseAgent._shared_context.get("states", {})
            if shared_states:
                print(f"\n   📊 Shared States Published: {', '.join(shared_states.keys())}")
            
            # Display handovers
            handovers = BaseAgent._shared_context.get("handovers", [])
            if handovers:
                print(f"\n   🤝 Handovers: {len(handovers)}")
                for handover in handovers:
                    print(f"      {handover['from']} → {handover['to']}: {handover['reason']}")
            
            print("=" * 70 + "\n")
        else:
            print("\n   ℹ️  No inter-agent communications occurred\n")

