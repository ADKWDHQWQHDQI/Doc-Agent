"""Conversation Manager for Interactive Agent Orchestration"""

import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class ConversationContext:
    """Tracks the ongoing conversation state"""
    user_request: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    gathered_info: Dict[str, Any] = field(default_factory=dict)
    clarification_round: int = 0
    max_clarification_rounds: int = 3
    confidence_score: float = 0.0
    # Store CLI arguments to pass through to generation
    code_directory: Optional[str] = None
    input_files: Optional[List[str]] = None
    # Track last questions asked for proper multi-question handling
    last_questions: List[str] = field(default_factory=list)
    # Track empty/spam responses
    empty_response_count: int = 0
    max_empty_responses: int = 2
    # Self-critique loop configuration
    critique_iterations: int = 0
    max_critique_iterations: int = 2
    enable_self_critique: bool = True
    
    def __post_init__(self):
        """Validate fields after initialization"""
        # Validate confidence_score range
        if not 0.0 <= self.confidence_score <= 1.0:
            self.confidence_score = max(0.0, min(1.0, self.confidence_score))
        
        # Validate rounds
        if self.clarification_round < 0:
            self.clarification_round = 0
        if self.max_clarification_rounds < 1:
            self.max_clarification_rounds = 3
        
        # Validate empty response tracking
        if self.empty_response_count < 0:
            self.empty_response_count = 0
        if self.max_empty_responses < 1:
            self.max_empty_responses = 2
    
    def add_exchange(self, agent: str, question: str, answer: str):
        """Add a question-answer exchange to history"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "question": question,
            "answer": answer
        })
    
    def update_info(self, key: str, value: Any):
        """Update gathered information"""
        self.gathered_info[key] = value
    
    def get_context_summary(self) -> str:
        """Generate a summary of what we know so far"""
        summary = f"Original Request: {self.user_request}\n\n"
        
        if self.gathered_info:
            summary += "Gathered Information:\n"
            for key, value in self.gathered_info.items():
                summary += f"- {key}: {value}\n"
            summary += "\n"
        
        if self.conversation_history:
            summary += "Previous Exchanges:\n"
            for i, exchange in enumerate(self.conversation_history[-3:], 1):
                summary += f"{i}. Q: {exchange['question'][:100]}...\n"
                summary += f"   A: {exchange['answer'][:100]}...\n"
        
        return summary


class ConversationalOrchestrator:
    """Manages multi-turn conversations for requirement gathering"""
    
    def __init__(self, base_orchestrator):
        self.orchestrator = base_orchestrator
        self.context: Optional[ConversationContext] = None
    
    async def start_conversation(
        self, 
        user_request: str,
        code_directory: Optional[str] = None,
        input_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Start a new conversational session with smart context detection"""
        self.context = ConversationContext(
            user_request=user_request,
            code_directory=code_directory,
            input_files=input_files
        )
        
        print("\n💬 Starting Interactive Conversation Mode\n")
        print("   I'll ask a few questions to understand your needs better.\n")
        
        # SMART CONTEXT AUTO-DETECTION
        await self._auto_detect_context()
        
        # Initial analysis
        return await self._analyze_and_clarify()
    
    async def _auto_detect_context(self) -> None:
        """Intelligently detect and auto-inject context from code/files"""
        if not self.context:
            return
        
        detected_info = []
        
        # 1. CODE DIRECTORY DETECTION
        if self.context.code_directory:
            from pathlib import Path
            code_path = Path(self.context.code_directory)
            
            if code_path.exists():
                detected_info.append(f"📁 Code directory: {code_path.name}")
                self.context.update_info("code_provided", "Yes")
                
                # Detect project type by analyzing file patterns
                detected_tech = await self._detect_technologies(code_path)
                if detected_tech:
                    detected_info.append(f"🔍 Detected: {', '.join(detected_tech)}")
                    self.context.update_info("detected_technologies", detected_tech)
                    
                    # Auto-suggest document types based on tech
                    suggested_docs = self._suggest_doc_types_from_tech(detected_tech)
                    if suggested_docs:
                        self.context.update_info("suggested_document_types", suggested_docs)
        
        # 2. INPUT FILES DETECTION
        if self.context.input_files:
            detected_info.append(f"📄 {len(self.context.input_files)} file(s) provided")
            self.context.update_info("files_provided", "Yes")
            
            # Analyze file types
            file_types = self._analyze_file_types(self.context.input_files)
            if file_types:
                detected_info.append(f"📋 File types: {', '.join(file_types)}")
                self.context.update_info("file_types", file_types)
        
        # 3. REQUEST PATTERN DETECTION
        request_lower = self.context.user_request.lower()
        
        # Detect application domain from request
        domain_keywords = {
            'e-commerce': ['ecommerce', 'e-commerce', 'shop', 'cart', 'checkout', 'payment', 'store'],
            'trading': ['trading', 'stock', 'forex', 'crypto', 'exchange', 'market'],
            'banking': ['banking', 'bank', 'finance', 'account', 'transaction', 'loan'],
            'healthcare': ['health', 'medical', 'patient', 'doctor', 'hospital', 'clinic'],
            'crm': ['crm', 'customer', 'lead', 'sales', 'contact management'],
            'api': ['api', 'rest', 'graphql', 'endpoint', 'microservice'],
            'mobile': ['mobile', 'ios', 'android', 'app'],
            'web': ['web', 'website', 'portal', 'dashboard']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in request_lower for kw in keywords):
                detected_info.append(f"🎯 Domain hint: {domain}")
                self.context.update_info("detected_domain", domain)
                break
        
        # Detect document type mentions
        doc_type_keywords = {
            'BRD': ['brd', 'business requirement'],
            'FRD': ['frd', 'functional requirement', 'technical spec'],
            'API': ['api doc', 'swagger', 'openapi'],
            'SECURITY': ['security', 'compliance', 'gdpr', 'hipaa'],
            'CLOUD': ['cloud', 'deployment', 'azure', 'aws', 'infrastructure']
        }
        
        for doc_type, keywords in doc_type_keywords.items():
            if any(kw in request_lower for kw in keywords):
                detected_info.append(f"📝 Document type hint: {doc_type}")
                self.context.update_info("mentioned_doc_type", doc_type)
                break
        
        # Display detected context
        if detected_info:
            print("   🧠 Smart Context Detection:")
            for info in detected_info:
                print(f"      {info}")
            print()
    
    async def _detect_technologies(self, code_path: Path) -> List[str]:
        """Detect technologies/frameworks from code directory structure"""
        detected = []
        
        try:
            # Check for specific files/patterns
            files_in_dir = list(code_path.glob('*'))
            file_names = [f.name for f in files_in_dir]
            
            # Python frameworks
            if 'requirements.txt' in file_names or 'pyproject.toml' in file_names:
                detected.append('Python')
                
                # Check for specific frameworks
                if any('fastapi' in f.name.lower() or 'main.py' in file_names for f in files_in_dir):
                    detected.append('FastAPI')
                elif 'app.py' in file_names or 'wsgi.py' in file_names:
                    detected.append('Flask/Django')
            
            # Node.js
            if 'package.json' in file_names:
                detected.append('Node.js')
                if 'next.config.js' in file_names:
                    detected.append('Next.js')
                elif 'vite.config' in str(file_names):
                    detected.append('Vite/React')
            
            # Java
            if 'pom.xml' in file_names or 'build.gradle' in file_names:
                detected.append('Java/Maven')
            
            # .NET
            if any('.csproj' in f.name for f in files_in_dir):
                detected.append('.NET/C#')
            
            # Docker
            if 'Dockerfile' in file_names or 'docker-compose.yml' in file_names:
                detected.append('Docker')
            
            # Kubernetes
            if any('kubernetes' in f.name.lower() or 'k8s' in f.name.lower() for f in files_in_dir):
                detected.append('Kubernetes')
            
            # Database files
            if any('.sql' in f.name for f in files_in_dir):
                detected.append('SQL Database')
            
        except Exception as e:
            # Silent fail - detection is optional
            pass
        
        return detected
    
    def _suggest_doc_types_from_tech(self, technologies: List[str]) -> List[str]:
        """Suggest document types based on detected technologies"""
        suggestions = set()
        
        tech_lower = [t.lower() for t in technologies]
        
        # API frameworks suggest API docs
        if any(t in tech_lower for t in ['fastapi', 'flask', 'node.js', 'express']):
            suggestions.add('API Documentation')
        
        # Cloud/Docker suggests deployment docs
        if any(t in tech_lower for t in ['docker', 'kubernetes', 'aws', 'azure']):
            suggestions.add('Cloud Deployment Guide')
        
        # Always suggest FRD for technical projects
        if len(technologies) > 0:
            suggestions.add('Functional Requirements Document (FRD)')
        
        # Database suggests data architecture
        if any('database' in t or 'sql' in t for t in tech_lower):
            suggestions.add('Data Architecture Document')
        
        return list(suggestions)
    
    def _analyze_file_types(self, file_paths: List[str]) -> List[str]:
        """Analyze file extensions to understand code type"""
        from pathlib import Path
        
        extensions = set()
        for file_path in file_paths:
            ext = Path(file_path).suffix
            if ext:
                extensions.add(ext)
        
        # Map to readable types
        type_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
            '.rb': 'Ruby',
            '.php': 'PHP'
        }
        
        return [type_map[ext] for ext in extensions if ext in type_map]
    
    async def _analyze_and_clarify(self) -> Dict[str, Any]:
        """Analyze current context and decide next steps"""
        
        if not self.context:
            return {"status": "error", "message": "No context"}
        
        # Check if we have enough information
        confidence = self._calculate_confidence()
        self.context.confidence_score = confidence
        
        print(f"   📊 Confidence Level: {confidence:.0%}\n")
        
        # Termination conditions with clear reasoning
        # 1. High confidence - proceed
        if confidence >= 0.7:
            print("   ✅ I have enough information to proceed!\n")
            return await self._proceed_with_generation()
        
        # 2. Max rounds reached - must proceed
        if self.context.clarification_round >= self.context.max_clarification_rounds:
            print(f"   ⚠️  Reached maximum clarification rounds ({self.context.max_clarification_rounds})")
            print("   Proceeding with available information...\n")
            return await self._proceed_with_generation()
        
        # 3. Too many empty responses - user not engaging
        if self.context.empty_response_count >= self.context.max_empty_responses:
            print(f"   ⚠️  Too many empty or unhelpful responses ({self.context.empty_response_count})")
            print("   Proceeding with defaults based on initial request...\n")
            return await self._proceed_with_generation()
        
        # 4. No progress check - if confidence hasn't improved after 2 rounds, use defaults
        if self.context.clarification_round >= 2:
            # Check if we made any progress
            if not self.context.gathered_info or len(self.context.gathered_info) < 2:
                print("   ⚠️  Limited progress after multiple rounds")
                print("   Proceeding with intelligent defaults...\n")
                return await self._proceed_with_generation()
        
        # Continue with intelligent questions
        return await self._ask_intelligent_questions()
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence based on gathered information using data-driven approach"""
        if not self.context:
            return 0.0
        
        # Dynamic scoring based on actual gathered information
        score = 0.0
        total_possible = 0.0
        
        # Core information categories with dynamic weights
        core_categories = [
            "application_type", "document_types", "key_features",
            "stakeholders", "security_requirements", "technical_constraints",
            "business_objectives", "deployment_environment", "timeline"
        ]
        
        # Each piece of gathered info contributes equally
        if self.context.gathered_info:
            for key, value in self.context.gathered_info.items():
                if value and str(value).strip() and str(value).lower() not in ["none", "n/a", "unknown"]:
                    # Check content quality (not just existence)
                    content_length = len(str(value).strip())
                    if content_length >= 5:  # Meaningful content threshold
                        score += 1.0
                        # Bonus for detailed responses
                        if content_length > 50:
                            score += 0.3
                    total_possible += 1.0
        
        # Base score from gathered info
        info_score = (score / max(total_possible, 1.0)) if total_possible > 0 else 0.0
        
        # Conversation depth bonus (diminishing returns)
        conversation_bonus = 0.0
        if self.context.conversation_history:
            # More weight to quality exchanges, not just quantity
            quality_exchanges = sum(
                1 for ex in self.context.conversation_history
                if len(ex.get('answer', '').strip()) > 20
            )
            conversation_bonus = min(quality_exchanges * 0.1, 0.25)
        
        # Penalize for too many rounds without progress
        round_penalty = 0.0
        if self.context.clarification_round > 2 and not self.context.gathered_info:
            round_penalty = 0.2 * (self.context.clarification_round - 2)
        
        # Penalize for empty responses (spam detection)
        spam_penalty = self.context.empty_response_count * 0.15
        
        # Combine scores with safeguards
        final_score = max(0.0, min(1.0, 
            (info_score * 0.7) + conversation_bonus - round_penalty - spam_penalty
        ))
        
        return final_score
    
    async def _ask_intelligent_questions(self) -> Dict[str, Any]:
        """Ask contextual, intelligent questions based on what we know"""
        
        if not self.context:
            return {"status": "error", "message": "No context"}
        
        self.context.clarification_round += 1
        
        # Use Dispatcher to analyze what we know and what we need
        context_summary = self.context.get_context_summary()
        
        # Build enhanced context with detected information
        detected_context = ""
        if self.context.gathered_info:
            detected_items = []
            if self.context.gathered_info.get('detected_technologies'):
                tech_list = ', '.join(self.context.gathered_info['detected_technologies'])
                detected_items.append(f"Detected Technologies: {tech_list}")
            if self.context.gathered_info.get('detected_domain'):
                detected_items.append(f"Detected Domain: {self.context.gathered_info['detected_domain']}")
            if self.context.gathered_info.get('suggested_document_types'):
                doc_list = ', '.join(self.context.gathered_info['suggested_document_types'])
                detected_items.append(f"Suggested Documents: {doc_list}")
            if self.context.gathered_info.get('file_types'):
                file_list = ', '.join(self.context.gathered_info['file_types'])
                detected_items.append(f"File Types: {file_list}")
            
            if detected_items:
                detected_context = "\n\nAuto-Detected Context:\n" + "\n".join(f"- {item}" for item in detected_items)
        
        analysis_prompt = f"""Analyze this conversation and determine what critical information is still missing:

{context_summary}{detected_context}

Based on what we know (including auto-detected context), generate 2-3 SPECIFIC, HIGHLY TARGETED questions.

IMPORTANT Guidelines:
1. Use detected technologies to ask framework-specific questions (e.g., "I see FastAPI - do you need OpenAPI/Swagger docs?")
2. If domain is detected, ask domain-specific questions (e.g., for e-commerce: "payment integration docs needed?")
3. Build on previous answers and detected context
4. Focus on the most critical missing information
5. Be conversational and easy to answer
6. Suggest document types based on detected tech stack

Respond in JSON format:
{{
  "analysis": "what we know vs what's missing",
  "priority_questions": ["question1", "question2", "question3"],
  "suggested_defaults": {{"key": "reasonable default value"}},
  "confidence_assessment": "why we can/cannot proceed"
}}
"""
        
        response = await self.orchestrator.dispatcher.execute_async(analysis_prompt)
        
        try:
            analysis = self._extract_json_from_response(response)
            
            print(f"   🤔 Round {self.context.clarification_round} - Let me ask a few questions:\n")
            
            questions = analysis.get("priority_questions", [])
            # Store questions in context for proper retrieval
            self.context.last_questions = questions[:3]
            
            for i, q in enumerate(self.context.last_questions, 1):
                print(f"   {i}. {q}")
            
            print(f"\n   💡 Alternatively, provide more context or I can proceed with reasonable defaults.\n")
            
            return {
                "status": "needs_clarification",
                "round": self.context.clarification_round,
                "questions": self.context.last_questions,  # Return stored questions for consistency
                "analysis": analysis.get("analysis", ""),
                "can_use_defaults": bool(analysis.get("suggested_defaults")),
                "context": self.context
            }
        
        except:
            # Fallback to basic questions
            return self._ask_basic_questions()
    
    def _ask_basic_questions(self) -> Dict[str, Any]:
        """Context-aware fallback questions that adapt to what we know"""
        if not self.context:
            return {"status": "error", "message": "No context"}
        
        # Build adaptive questions based on what's missing
        adaptive_questions = []
        gathered_keys = set(self.context.gathered_info.keys())
        
        # Application type
        if "application_type" not in gathered_keys:
            adaptive_questions.append("What type of application is this? (e.g., web app, mobile app, API, microservices)")
        
        # Document types
        if "document_types" not in gathered_keys and "document_type" not in gathered_keys:
            adaptive_questions.append("What documentation do you need? (e.g., BRD, FRD, API docs, deployment guide)")
        
        # Features or functionality
        if "key_features" not in gathered_keys and "features" not in gathered_keys:
            adaptive_questions.append("What are the main features or capabilities of this application?")
        
        # Stakeholders
        if "stakeholders" not in gathered_keys and len(adaptive_questions) < 3:
            adaptive_questions.append("Who are the primary users or stakeholders?")
        
        # Technical context
        if "technical_stack" not in gathered_keys and "tech_stack" not in gathered_keys and len(adaptive_questions) < 3:
            # Infer from request if code is provided
            if self.context.code_directory or self.context.input_files:
                adaptive_questions.append("Any specific technical requirements or constraints we should document?")
            else:
                adaptive_questions.append("What technologies or platforms does this use?")
        
        # Fallback to generic if we couldn't build enough questions
        if len(adaptive_questions) < 2:
            adaptive_questions = [
                "Can you provide more details about your documentation needs?",
                "What specific aspects should the documentation cover?",
                "Are there any particular requirements or constraints?"
            ]
        
        # Store questions in context
        self.context.last_questions = adaptive_questions[:3]
        
        print(f"   🤔 Round {self.context.clarification_round} - Targeted Questions:\n")
        for i, q in enumerate(self.context.last_questions, 1):
            print(f"   {i}. {q}")
        
        return {
            "status": "needs_clarification",
            "round": self.context.clarification_round,
            "questions": self.context.last_questions,
            "context": self.context
        }
    
    async def process_user_response(self, user_response: str) -> Dict[str, Any]:
        """Process user's answer and continue conversation"""
        
        if not self.context:
            return {"status": "error", "message": "No active conversation"}
        
        # Validate response quality - detect empty/spam responses
        response_clean = user_response.strip() if user_response else ""
        
        # Empty or too short responses
        if not response_clean or len(response_clean) < 3:
            self.context.empty_response_count += 1
            print(f"\n   ⚠️  Empty response detected ({self.context.empty_response_count}/{self.context.max_empty_responses})\n")
            
            if self.context.empty_response_count >= self.context.max_empty_responses:
                print("   Too many empty responses. Proceeding with available information...\n")
                return await self._proceed_with_generation()
            else:
                print("   Please provide a meaningful response, or I'll proceed with defaults.\n")
                # Re-ask the same questions
                return {
                    "status": "needs_clarification",
                    "round": self.context.clarification_round,
                    "questions": self.context.last_questions,
                    "context": self.context
                }
        
        # Detect unhelpful responses (e.g., "idk", "skip", "whatever")
        unhelpful_patterns = ["idk", "i don't know", "dunno", "skip", "pass", "whatever", "n/a", "none"]
        if any(pattern in response_clean.lower() for pattern in unhelpful_patterns) and len(response_clean) < 20:
            self.context.empty_response_count += 1
            print(f"\n   ⚠️  Unhelpful response detected. Please provide more detail or I'll use defaults.\n")
        else:
            # Reset empty count on good response
            self.context.empty_response_count = 0
        
        # Add to conversation history
        last_questions = self._get_last_questions()
        self.context.add_exchange(
            agent="System",
            question="; ".join(last_questions),
            answer=user_response
        )
        
        # Extract information from response using Requirement Analyst
        extraction_prompt = f"""Extract structured information from this user response:

User Response: {user_response}

Context of Conversation:
{self.context.get_context_summary()}

Extract and structure:
1. Application type/domain
2. Document types requested
3. Key features mentioned
4. Security requirements
5. Any other relevant details

Respond in JSON format with extracted information."""
        
        extracted = await self.orchestrator.analyst.execute_async(extraction_prompt, {})
        
        # Update gathered info
        try:
            info = self._extract_json_from_response(extracted)
            for key, value in info.items():
                if value:
                    self.context.update_info(key, value)
        except:
            # Store as raw text
            self.context.update_info("latest_response", user_response)
        
        print(f"\n   ✅ Thanks! Processing your response...\n")
        
        # Continue the conversation
        return await self._analyze_and_clarify()
    
    async def _proceed_with_generation(self) -> Dict[str, Any]:
        """Proceed with document generation using gathered context with self-critique loop."""
        
        if not self.context:
            return {"status": "error", "message": "No context"}
        
        print("   🚀 Generating documentation with collected information...\n")
        
        # Build enriched request
        enriched_request = self.context.user_request
        
        if self.context.gathered_info:
            enriched_request += "\n\nAdditional Context:\n"
            for key, value in self.context.gathered_info.items():
                enriched_request += f"- {key}: {value}\n"
        
        if self.context.conversation_history:
            enriched_request += "\n\nFrom our conversation:\n"
            for exchange in self.context.conversation_history:
                enriched_request += f"Q: {exchange['question']}\n"
                enriched_request += f"A: {exchange['answer']}\n\n"
        
        # Call original generation logic with stored CLI arguments
        result = await self.orchestrator.generate_documentation_async(
            user_request=enriched_request,
            code_directory=self.context.code_directory,
            input_files=self.context.input_files
        )
        
        # Self-critique loop: Iterate on low-confidence outputs
        if (self.context.enable_self_critique and 
            "low_confidence" in result.get("flags", []) and 
            self.context.critique_iterations < self.context.max_critique_iterations):
            
            self.context.critique_iterations += 1
            print(f"\n🔍 Self-Critique Loop (Iteration {self.context.critique_iterations}/{self.context.max_critique_iterations})")
            print("   ⚠️  Low confidence detected in generated document")
            print("   🧐 Requesting critique and improvements...\n")
            
            # Get critique from editor
            document_preview = result['document'][:2000]  # First 2000 chars for critique
            quality_issues = result.get('quality', {}).get('issues', [])
            
            critique_prompt = f"""Critique this document and suggest specific improvements:

Document Preview:
{document_preview}

Detected Issues:
{chr(10).join(f'- {issue}' for issue in quality_issues)}

Provide:
1. Specific problems with structure, content, or completeness
2. Concrete suggestions for improvement
3. Missing sections that should be added
4. Content that needs expansion

Format your response as actionable recommendations."""
            
            critique = await self.orchestrator.editor.execute_async(critique_prompt)
            
            print("   ✅ Critique received\n")
            print("   🔄 Regenerating document with critique feedback...\n")
            
            # Loop back: Add critique to enriched request
            enriched_request += f"\n\n=== SELF-CRITIQUE FEEDBACK (Iteration {self.context.critique_iterations}) ===\n"
            enriched_request += f"Previous attempt had the following issues:\n{critique}\n\n"
            enriched_request += "Please address these issues in the regenerated document.\n"
            
            # Store critique in context
            self.context.update_info(f"critique_iteration_{self.context.critique_iterations}", critique)
            
            # Regenerate with critique feedback
            result = await self.orchestrator.generate_documentation_async(
                user_request=enriched_request,
                code_directory=self.context.code_directory,
                input_files=self.context.input_files
            )
            
            # Check if improvement was achieved
            new_quality = result.get('quality', {})
            if new_quality.get('confidence') != 'low':
                print(f"   ✅ Quality improved to {new_quality.get('confidence', 'unknown').upper()}\n")
            elif self.context.critique_iterations < self.context.max_critique_iterations:
                print(f"   ⚠️  Still low confidence, will retry...\n")
                # Recursive call for next iteration
                return await self._proceed_with_generation()
            else:
                print(f"   ⚠️  Max critique iterations reached, proceeding with current version\n")
        
        return result
    
    def _get_last_questions(self) -> List[str]:
        """Get the last set of questions asked"""
        if self.context and self.context.last_questions:
            return self.context.last_questions
        # Fallback: try to extract from conversation history
        if self.context and self.context.conversation_history:
            last = self.context.conversation_history[-1]
            # Split on semicolon if multiple questions were joined
            return [q.strip() for q in last["question"].split(";") if q.strip()]
        return []
    
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
        
        # Strategy 3: Find JSON object anywhere in text with proper nesting
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
        
        # Strategy 4: Try to extract key-value pairs with regex (conversation-specific)
        try:
            result = {}
            # Extract priority_questions array
            questions_match = re.search(r'["\']?priority_questions["\']?\s*:\s*\[(.*?)\]', response, re.DOTALL)
            if questions_match:
                questions_str = questions_match.group(1)
                # Extract individual questions
                questions = re.findall(r'["\']([^"\']+ \?)["\']', questions_str)
                if questions:
                    result['priority_questions'] = questions
            
            # Extract analysis field
            analysis_match = re.search(r'["\']?analysis["\']?\s*:\s*["\']([^"\']+ )["\']', response)
            if analysis_match:
                result['analysis'] = analysis_match.group(1)
            
            if result:
                return result
        except Exception:
            pass
        
        return {}
