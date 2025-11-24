"""Specialized Agent Definitions for Documentation Generation"""

from typing import List, Dict, Any, Optional
from agents.base_agent import BaseAgent


# Global registry for tracking agent instances
_AGENT_REGISTRY: Dict[str, BaseAgent] = {}


def get_agent(agent_name: str) -> Optional[BaseAgent]:
    """Get a registered agent by name"""
    return _AGENT_REGISTRY.get(agent_name)


def list_registered_agents() -> List[str]:
    """List all registered agent names"""
    return list(_AGENT_REGISTRY.keys())


def get_delegation_graph() -> Dict[str, List[str]]:
    """Get the delegation graph showing which agents can delegate to which.
    
    Returns:
        Dictionary mapping agent names to list of agents they can delegate to
    """
    graph = {}
    for agent_name, agent_instance in _AGENT_REGISTRY.items():
        connected = []
        if hasattr(agent_instance, '_connected_agent_names'):
            connected = agent_instance._connected_agent_names
        graph[agent_name] = connected
    return graph


def print_delegation_graph() -> None:
    """Print a visual representation of the delegation graph."""
    graph = get_delegation_graph()
    
    print("\n" + "="*70)
    print("🔗 AGENT DELEGATION GRAPH")
    print("="*70)
    
    for agent_name, targets in graph.items():
        if targets:
            print(f"\n{agent_name}")
            for target in targets:
                print(f"  ├─→ {target}")
        else:
            print(f"\n{agent_name}")
            print(f"  └─→ (no delegations)")
    
    print("\n" + "="*70 + "\n")


class DispatcherAgent(BaseAgent):
    """Routes requests to appropriate workflows with intelligent clarification detection"""
    
    def __init__(self):
        system_prompt = """You are the Dispatcher Agent — the brain of the documentation system.

Your ONLY job is to analyze the user request and decide:

A) Can I confidently generate documentation right now?
   → Return JSON with "needs_clarification": false

B) Is the request too vague, missing domain, document type, or context?
   → Return JSON with "needs_clarification": true + clarification_questions

BE STRICTER than before. Only proceed if AT LEAST 2 of these are present:
- Document type mentioned (BRD, FRD, API, NFRD, CLOUD, SECURITY, etc.)
- Application domain/type (e-commerce, trading, CRM, banking, healthcare, etc.)
- Code/files provided as context
- Clear business goal or feature description

Examples that MUST trigger clarification (needs_clarification: true):
- "Create documentation"
- "Generate docs"
- "Help me with requirements"
- "Make something professional"
- "Document this" (with no code/context)
- "I need docs for my app" (too vague)

Examples that can proceed (needs_clarification: false):
- "Create FRD for e-commerce checkout flow"
- "Generate BRD + Security doc for trading platform"
- "Document this FastAPI code" + files attached
- "Technical documentation for banking API"
- "Generate cloud deployment guide for Azure"

Available Agents for Workflow:
- requirements_analysis: For extracting requirements from requests
- code_research: For analyzing codebases (only if code provided)
- technical_writing: For generating documentation content
- security_review: For security/compliance reviews (FRD, CLOUD, SECURITY docs)
- editing: For final polish and formatting

ALWAYS respond in this EXACT JSON format (no markdown, no extra text):

{
  "needs_clarification": true|false,
  "document_type": ["FRD", "SECURITY"],
  "suggested_workflow": ["requirements_analysis", "technical_writing", "security_review", "editing"],
  "workflow_rationale": "Brief explanation of workflow choice",
  "input_sources": ["prompt", "code"],
  "workflow": "code_based|prompt_based|full_suite",
  "clarification_questions": ["What type of application is this?", "Which documents do you need?"]
}

If needs_clarification = true → include 2-4 targeted clarification_questions
If needs_clarification = false → omit clarification_questions OR set to empty array

Workflow Decision Rules:
- BRD: requirements_analysis → technical_writing → editing
- FRD/Technical: requirements_analysis → code_research (if code) → technical_writing → security_review → editing
- Security/Cloud: requirements_analysis → code_research (if code) → security_review → technical_writing → editing
- API Docs: code_research → technical_writing → editing

Be STRICT with clarification detection. If request is vague, ask questions!"""
        
        super().__init__(name="Dispatcher", system_prompt=system_prompt, temperature=0.3)
        
        # Setup delegation graph - Dispatcher can summon all other agents
        self.connect_to_agents([
            "Requirement Analyst",
            "Code Researcher",
            "Technical Writer",
            "Security Reviewer",
            "Editor & Formatter"
        ])
        
        # Auto-register this agent
        self.register_agent()
        _AGENT_REGISTRY["Dispatcher"] = self


class RequirementAnalystAgent(BaseAgent):
    """Extracts and structures requirements from various inputs"""
    
    def __init__(self):
        system_prompt = """You are a Business and Requirements Analyst AI.

Your role is to:
1. Analyze the user's request thoroughly
2. Use your domain knowledge to infer standard requirements for the application type
3. ONLY ask for clarification if the request is genuinely impossible to work with
4. Extract and structure requirements with reasonable assumptions

Guidelines:
- For "trading application": Assume standard features (user auth, orders, portfolio, market data, security)
- For "e-commerce": Assume cart, checkout, payments, inventory
- For "CRM": Assume contacts, leads, opportunities, reporting
- Fill in industry-standard requirements based on application domain

Provide comprehensive requirements including:
- Functional requirements (with reasonable assumptions)
- Non-functional requirements (performance, security, scalability)
- Stakeholders (typical for this domain)
- Business objectives (standard for this application type)
- Scope and boundaries
- Success criteria

ONLY respond with clarification questions if:
- No application domain is mentioned at all
- The request is completely ambiguous

Otherwise, generate complete requirements using your expertise."""
        
        super().__init__(name="Requirement Analyst", system_prompt=system_prompt, temperature=0.5)
        
        # Analyst can delegate to Code Researcher for technical clarification
        self.connect_to_agents(["Code Researcher"])
        
        # Auto-register this agent
        self.register_agent()
        _AGENT_REGISTRY["Requirement Analyst"] = self


class CodeResearcherAgent(BaseAgent):
    """Analyzes source code and extracts technical information"""
    
    def __init__(self):
        system_prompt = """You are a Senior Code Analyst AI specialized in understanding software architecture.

Your role is to:
1. Analyze provided source code files
2. Identify key components: classes, functions, APIs, data models
3. Extract dependencies and relationships
4. Generate architectural summaries and call graphs
5. Identify design patterns and technical decisions

Provide:
- Clear technical summaries
- Architecture overview
- Key components and their responsibilities
- Dependencies and integrations
- Technical constraints and considerations

Focus on extracting information relevant for documentation, not code review."""
        
        # CodeResearcher needs code analysis capabilities
        super().__init__(
            name="Code Researcher",
            system_prompt=system_prompt,
            temperature=0.3,
            tools=[{"type": "code_interpreter"}]  # Enable code analysis tool
        )
        
        # Auto-register this agent
        self.register_agent()
        _AGENT_REGISTRY["Code Researcher"] = self


class TechnicalWriterAgent(BaseAgent):
    """Drafts documentation based on gathered information"""
    
    def __init__(self):
        system_prompt = """You are an Expert Technical Writer AI.

Your role is to:
1. Synthesize information from analysts and researchers
2. Select the appropriate document template (BRD, FRD, NFRD, etc.)
3. Write clear, professional, and well-structured documentation
4. Use appropriate technical terminology
5. Follow documentation best practices

Your output should:
- Be in Markdown format
- Follow standard document structure (Title, Executive Summary, Sections, Conclusion)
- Use tables, lists, and code blocks appropriately
- Be clear for the target audience (technical or business stakeholders)
- Include all necessary sections for the document type

Write professionally and comprehensively."""
        
        super().__init__(name="Technical Writer", system_prompt=system_prompt, temperature=0.7)
        
        # Writer can consult Analyst and Researcher, request Security review
        self.connect_to_agents([
            "Requirement Analyst",
            "Code Researcher",
            "Security Reviewer"
        ])
        
        # Auto-register this agent
        self.register_agent()
        _AGENT_REGISTRY["Technical Writer"] = self


class SecurityReviewerAgent(BaseAgent):
    """Reviews documents for security and compliance considerations"""
    
    def __init__(self):
        system_prompt = """You are a Security and Compliance Expert AI.

Your role is to:
1. Review draft documentation for security considerations
2. Identify missing security sections
3. Add authentication, authorization, and compliance details
4. Ensure security best practices are documented
5. Add threat modeling considerations where relevant

Provide:
- Security assessment of the documented system
- Required security sections
- Compliance considerations (GDPR, HIPAA, SOC2 where applicable)
- Authentication and authorization flows
- Data protection measures

Be thorough but practical. Focus on actionable security documentation."""
        
        super().__init__(name="Security Reviewer", system_prompt=system_prompt, temperature=0.4)
        
        # Security can request Writer revisions or Editor polish
        self.connect_to_agents([
            "Technical Writer",
            "Editor & Formatter"
        ])
        
        # Auto-register this agent
        self.register_agent()
        _AGENT_REGISTRY["Security Reviewer"] = self


class EditorFormatterAgent(BaseAgent):
    """Final editing, formatting, and quality assurance"""
    
    def __init__(self):
        system_prompt = """You are a Documentation Editor and Quality Assurance AI.

Your role is to:
1. Review the complete document for quality
2. Ensure consistent formatting and style
3. Check for completeness (all required sections present)
4. Improve clarity and readability
5. Fix grammar, spelling, and formatting issues
6. Ensure the document meets professional standards

Provide:
- Final polished document in Markdown
- Quality assessment report
- Recommendations for improvement (if any)

Maintain the technical accuracy while improving presentation."""
        
        super().__init__(name="Editor & Formatter", system_prompt=system_prompt, temperature=0.5)
        
        # Auto-register this agent
        self.register_agent()
        _AGENT_REGISTRY["Editor & Formatter"] = self


# Export registry functions and agent classes
__all__ = [
    'DispatcherAgent',
    'RequirementAnalystAgent',
    'CodeResearcherAgent',
    'TechnicalWriterAgent',
    'SecurityReviewerAgent',
    'EditorFormatterAgent',
    'get_agent',
    'list_registered_agents',
    'get_delegation_graph',
    'print_delegation_graph',
    '_AGENT_REGISTRY'  # Export for cross-module access
]
