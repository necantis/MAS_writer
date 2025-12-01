"""
Live Agent Orchestrator with Real Gemini API Integration
=========================================================
Production-ready orchestrator that uses real Gemini API calls for:
- Author Agent (Agent A): 4-phase document generation workflow
- Reviewer Agent: LLM-as-a-Judge quality audits
- Meta-Reviewer Agent: Prompt refinement strategist

This replaces the mock agents from router_agent_orchestrator.py with live LLM calls.
"""

import sys
import json
from typing import Dict, Any, Optional, Tuple

# Import utilities and prompts
from gemini_utils import (
    create_gemini_client,
    call_gemini_with_retry,
    extract_scorecard
)
from prompts import (
    build_author_prompt,
    build_reviewer_prompt,
    build_meta_reviewer_prompt
)


# ============================================================================
# LIVE GEMINI AGENT CLASSES
# ============================================================================

class GeminiAuthorAgent:
    """
    Author Agent (Agent A) powered by Gemini API.
    
    Executes the full 4-phase workflow:
    1. Source Manifest Generation
    2. Hypothesis Generation
    3. DS-STAR Analysis Integration
    4. Final Document Assembly
    """
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        """
        Initialize the Author Agent with a Gemini model.
        
        Args:
            model_name: Name of the Gemini model to use
        """
        self.model_name = model_name
        self.model = create_gemini_client(model_name)
        print(f"✓ Author Agent initialized with {model_name}")
    
    def run_workflow(self, user_query: str, previous_kill_list: str = "") -> str:
        """
        Execute the full 4-phase workflow to generate a document.
        
        Args:
            user_query: The user's research topic/request
            previous_kill_list: Feedback from previous iteration (if any)
            
        Returns:
            Complete generated document
        """
        print(f"\n[AUTHOR AGENT]: Running 4-phase workflow using {self.model_name}...")
        
        # Build the complete prompt
        prompt = build_author_prompt(user_query, previous_kill_list)
        
        # Call Gemini API with retry logic
        print("  Phase 1-4: Generating complete document...")
        document = call_gemini_with_retry(self.model, prompt)
        
        print(f"✓ Document generated ({len(document)} characters)")
        
        # Simulate DS-STAR tool integration (mock for now)
        # In production, this would call an external analysis service
        ds_star_result = self._mock_ds_star_analysis()
        print(f"  [DS-STAR MOCK]: Analysis complete - {ds_star_result['summary']}")
        
        return document
    
    def _mock_ds_star_analysis(self) -> Dict[str, Any]:
        """
        Mock DS-STAR tool for demonstration purposes.
        
        In production, this would call the actual ds_star_agent.py
        or an external Kaggle analysis service.
        
        Returns:
            Mock analysis results
        """
        return {
            "success": True,
            "summary": "Hypothesis validated (p<0.001), Burn Rate: $50k/month",
            "statistical_significance": 0.001,
            "financial_metrics": {
                "burn_rate_monthly": 50000,
                "roi_projected": 2.5
            }
        }


class GeminiReviewerAgent:
    """
    Reviewer Agent powered by Gemini API.
    
    Acts as LLM-as-a-Judge to perform rigorous quality audits
    and generate structured scorecards with actionable feedback.
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Reviewer Agent with a Gemini model.
        
        Args:
            model_name: Name of the Gemini model to use
        """
        self.model_name = model_name
        self.model = create_gemini_client(model_name)
        print(f"✓ Reviewer Agent initialized with {model_name}")
    
    def audit(self, document: str, previous_kill_list: str = "") -> str:
        """
        Perform a comprehensive audit of the document.
        
        Args:
            document: The document to audit
            previous_kill_list: Previous feedback to check against
            
        Returns:
            Audit response with scorecard and feedback
        """
        print(f"\n[REVIEWER AGENT]: Auditing document using {self.model_name}...")
        
        # Build the audit prompt
        prompt = build_reviewer_prompt(document, previous_kill_list)
        
        # Call Gemini API with retry logic
        audit_response = call_gemini_with_retry(self.model, prompt)
        
        print(f"✓ Audit completed ({len(audit_response)} characters)")
        
        return audit_response


class GeminiMetaReviewerAgent:
    """
    Meta-Reviewer Agent powered by Gemini API.
    
    Analyzes audit failures and generates optimized prompts
    for Agent A to fix the issues in the next iteration.
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Meta-Reviewer Agent with a Gemini model.
        
        Args:
            model_name: Name of the Gemini model to use
        """
        self.model_name = model_name
        self.model = create_gemini_client(model_name)
        print(f"✓ Meta-Reviewer Agent initialized with {model_name}")
    
    def strategize(self, scorecard: Dict[str, str], audit_report: str, document: str) -> str:
        """
        Analyze the audit failure and generate the next prompt for Agent A.
        
        Args:
            scorecard: Parsed scorecard dictionary
            audit_report: Detailed audit feedback
            document: The document that failed
            
        Returns:
            Optimized prompt for Agent A
        """
        print(f"\n[META-REVIEWER AGENT]: Analyzing failure using {self.model_name}...")
        
        # Build the strategy prompt
        prompt = build_meta_reviewer_prompt(scorecard, audit_report, document)
        
        # Call Gemini API with retry logic
        next_prompt = call_gemini_with_retry(self.model, prompt)
        
        print(f"✓ Next prompt generated ({len(next_prompt)} characters)")
        
        return next_prompt


# ============================================================================
# ORCHESTRATION LOOP (Reuses validated logic from router_agent_orchestrator.py)
# ============================================================================

def run_refinement_loop(
    author_agent: GeminiAuthorAgent,
    reviewer_agent: GeminiReviewerAgent,
    meta_reviewer_agent: GeminiMetaReviewerAgent,
    user_query: str,
    max_iterations: int = 5
) -> Tuple[bool, Optional[str]]:
    """
    Execute the iterative refinement loop with live Gemini agents.
    
    This function reuses the validated orchestration logic from
    router_agent_orchestrator.py with the three priority fixes:
    1. Robust scorecard parsing
    2. Explicit REJECTED keyword detection
    3. Enhanced logging for failures
    
    Args:
        author_agent: Initialized Author Agent
        reviewer_agent: Initialized Reviewer Agent
        meta_reviewer_agent: Initialized Meta-Reviewer Agent
        user_query: The user's research topic/request
        max_iterations: Maximum number of refinement iterations
        
    Returns:
        Tuple of (success: bool, final_document: Optional[str])
    """
    previous_kill_list = ""
    final_document = None
    
    print(f"\n{'='*70}")
    print(f"STARTING LIVE ITERATIVE REFINEMENT LOOP (Max {max_iterations} Iterations)")
    print(f"{'='*70}")
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n{'='*70}")
        print(f"ITERATION {iteration}: LIVE DRAFTING & AUDIT")
        print(f"{'='*70}")
        
        # === PHASE 1: Draft/Redraft (Author Agent) ===
        draft_document = author_agent.run_workflow(user_query, previous_kill_list)
        final_document = draft_document
        
        # === PHASE 2: Audit (Reviewer Agent) ===
        audit_response = reviewer_agent.audit(draft_document, previous_kill_list)
        
        # Parse the reviewer's response
        scorecard, audit_report = extract_scorecard(audit_response)
        
        print(f"  Scorecard fields: {list(scorecard.keys())}")
        
        # === PHASE 3: Decision & Exit (Router Logic) ===
        print(f"\n[PHASE 3: DECISION]")
        
        kill_list_fixed = scorecard.get("Previous_Kill_List_Fixed", "NO").upper()
        is_rejected = "REJECTED" in audit_response.upper()
        
        print(f"  Previous Kill List Fixed: {kill_list_fixed}")
        print(f"  Document Rejected: {is_rejected}")
        
        # [PRIORITY 2 FIX] Explicit REJECTED keyword check
        if is_rejected:
            print(f"\n{'='*70}")
            print("🛑 IMMEDIATE REJECTION DETECTED")
            print(f"{'='*70}")
            print(f"\n📋 FAILURE REPORT (Iteration {iteration}):")
            print(f"   Reason: Auditor explicitly REJECTED the document")
            print(f"\n📄 AUDIT RESPONSE EXCERPT:")
            print(f"   {audit_response[:500]}...")
            print(f"\n{'='*70}")
            print(f"❌ TERMINATING: Document rejected after {iteration} iteration(s)")
            print(f"{'='*70}")
            return False, final_document
        
        # Check success condition
        if kill_list_fixed == "YES":
            print(f"\n{'='*70}")
            print("🎉 SUCCESS: TERMINATION CONDITION MET")
            print("  ✓ Previous Kill List Fixed: YES")
            print("  ✓ Document NOT Rejected")
            print(f"{'='*70}")
            print(f"\n✅ Document passed audit after {iteration} iteration(s)")
            return True, final_document
        
        print(f"\n  ❌ Audit failed - continuing to refinement...")
        
        # Update the Kill List for next iteration
        previous_kill_list = audit_report.strip()
        
        # === PHASE 4: Strategize (Meta-Reviewer) ===
        user_query = meta_reviewer_agent.strategize(scorecard, audit_report, draft_document)
    
    # [PRIORITY 3 FIX] Enhanced logging for MAX_ITERATION_FAILURE
    print(f"\n{'='*70}")
    print(f"🛑 LOOP TERMINATED: Maximum iterations ({max_iterations}) reached")
    print(f"{'='*70}")
    print(f"\n📋 DETAILED FAILURE TRACE:")
    print(f"\n1. FINAL PROMPT (last iteration):")
    print(f"   {user_query[:500]}...")
    print(f"\n2. FINAL SCORECARD:")
    print(f"   {json.dumps(scorecard, indent=4)}")
    print(f"\n{'='*70}")
    print(f"❌ Document failed to pass audit after {max_iterations} iterations")
    print(f"{'='*70}")
    
    return False, final_document


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution function for live agent orchestrator.
    """
    print("\n" + "="*70)
    print("🚀 LIVE AGENT ORCHESTRATOR - GEMINI API INTEGRATION")
    print("="*70)
    
    # Initialize live Gemini agents
    try:
        print("\n[INITIALIZATION]: Creating live Gemini agents...")
        author = GeminiAuthorAgent(model_name="gemini-2.0-flash-exp")
        reviewer = GeminiReviewerAgent(model_name="gemini-2.0-flash-exp")
        meta_reviewer = GeminiMetaReviewerAgent(model_name="gemini-2.0-flash-exp")
        print("\n✓ All agents initialized successfully")
        
    except Exception as e:
        print(f"\n🛑 ERROR: Failed to initialize agents: {e}")
        print("\nPlease ensure:")
        print("  1. You have created a .env file with your GEMINI_API_KEY")
        print("  2. You have installed dependencies: pip install -r requirements.txt")
        print("  3. Your API key is valid and has access to Gemini models")
        sys.exit(1)
    
    # Define the live test query
    LIVE_TEST_QUERY = """Generate the Capstone Project document. The core subject must be: 'The impact of signal reliability on sensor-based supply chain efficiency.' You must use the 'google-search' built-in tool to find literature and generate a hypothesis suitable for testing with a real-world Kaggle dataset."""
    
    print(f"\n{'='*70}")
    print("📝 USER QUERY:")
    print(f"{'='*70}")
    print(LIVE_TEST_QUERY)
    print(f"{'='*70}")
    
    # Run the refinement loop
    success, final_document = run_refinement_loop(
        author_agent=author,
        reviewer_agent=reviewer,
        meta_reviewer_agent=meta_reviewer,
        user_query=LIVE_TEST_QUERY,
        max_iterations=5
    )
    
    # Final results
    print(f"\n{'='*70}")
    print(f"📊 FINAL RESULT: {'SUCCESS ✅' if success else 'FAILURE ❌'}")
    print(f"{'='*70}")
    
    if success and final_document:
        # Save the final document
        output_file = "capstone_project_final.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_document)
        print(f"\n✓ Final document saved to: {output_file}")
        print(f"  Document length: {len(final_document)} characters")
    
    print(f"\n{'='*70}\n")
    
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
