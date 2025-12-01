"""
Router Agent: Iterative Refinement Orchestrator (ROBUSTNESS PATCHED)
====================================================================
Manages the Agent A -> Reviewer -> Meta-Reviewer loop for document refinement.

This orchestrator implements a maximum of 5 iterations, terminating early when:
- Previous_Kill_List_Fixed == "YES" AND
- The response does NOT contain "REJECTED"

CHANGELOG (Priority Fixes):
---------------------------
[Priority 1] ROBUSTNESS FIX (Scenario 4): Enhanced parse_scorecard() with regex-based 
             extraction and try/except for safe JSON parsing to prevent crashes on 
             malformed/corrupted input.

[Priority 2] EXIT CONDITION FIX (Scenario 2): Added explicit "REJECTED" keyword check 
             with immediate hard stop and detailed failure report, regardless of 
             Previous_Kill_List_Fixed value.

[Priority 3] ENHANCED LOGGING (Scenario 3): Added detailed trace logging in 
             MAX_ITERATION_FAILURE block, printing final failed prompt and 
             Meta-Reviewer response for root cause analysis.
"""

import json
import re
from typing import Dict, Any, Tuple, Optional


# --- Mock Agent Interface (Simulating ADK Invocation) ---
class MockAgent:
    """
    Simulates an ADK agent interface for testing purposes.
    In production, replace with actual ADK agent invocation.
    """
    def __init__(self, name: str):
        self.name = name
        
    def invoke(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Simulates invoking an agent and getting a response.
        
        Args:
            prompt: The instruction/prompt for the agent
            context: Additional context variables to inject
            
        Returns:
            The agent's response as a string
        """
        print(f"\n[{self.name} Invoking...]")
        print(f"  Prompt preview: {prompt[:100]}...")
        if context:
            print(f"  Context keys: {list(context.keys())}")
        
        # In production, this would be: return agent_instance.run(prompt, context=context)
        return f"Mock response from {self.name}"


# --- Helper Functions for Robust Parsing ---
def _clean_kill_list(audit_report: str) -> str:
    """
    [PRIORITY 1 FIX] Cleans the audit_report (Kill List) of redundant headers
    and Meta-Reviewer artifacts that pollute state propagation.
    
    Removes common patterns like:
    - "A. The Kill List Status:"
    - "B. Structural Compliance:"
    - Other lettered section headers
    
    Args:
        audit_report: Raw audit report text from the Reviewer
        
    Returns:
        Cleaned audit report with redundant headers removed
    """
    if not audit_report:
        return audit_report
    
    # Remove common section headers that Meta-Reviewer might include
    patterns_to_remove = [
        r'^A\.\s+The Kill List Status:\s*\n?',
        r'^B\.\s+Structural Compliance:\s*\n?',
        r'^C\.\s+ADK Architecture Review:\s*\n?',
        r'^D\.\s+Evidence Review.*?:\s*\n?',
        r'^[A-Z]\.\s+[^:]+:\s*\n?',  # Generic lettered section headers
    ]
    
    cleaned = audit_report
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned


# --- Helper Function for Parsing Reviewer Output (ROBUSTNESS PATCHED) ---
def parse_scorecard(full_response: str) -> Tuple[Dict[str, str], str]:
    """
    [PRIORITY 1 FIX] Extracts the JSON scorecard and the remaining audit text/Kill List
    with enhanced robustness using regex and safe JSON parsing.
    
    The scorecard is expected to be between '**REVIEWER_SCORECARD**' and 
    '**END_SCORECARD**' markers.
    
    ROBUSTNESS IMPROVEMENTS:
    - Uses regex for more flexible marker detection
    - Implements try/except for safe JSON parsing
    - Gracefully handles malformed/corrupted input without crashing
    - Returns empty dict on parsing failure instead of raising exceptions
    
    Args:
        full_response: The complete response from the Reviewer Agent
        
    Returns:
        A tuple of (scorecard_dict, audit_report_text)
    """
    try:
        # Use regex for more robust marker detection (case-insensitive, flexible whitespace)
        start_pattern = r'\*\*REVIEWER_SCORECARD\*\*'
        end_pattern = r'\*\*END_SCORECARD\*\*'
        
        start_match = re.search(start_pattern, full_response, re.IGNORECASE)
        if not start_match:
            print("⚠️  WARNING: REVIEWER_SCORECARD marker not found - returning empty scorecard")
            return {}, full_response
        
        start_idx = start_match.end()
        end_match = re.search(end_pattern, full_response[start_idx:], re.IGNORECASE)
        
        if not end_match:
            print("⚠️  WARNING: END_SCORECARD marker not found - parsing until end of response")
            scorecard_section = full_response[start_idx:].strip()
            audit_report = ""
        else:
            scorecard_section = full_response[start_idx:start_idx + end_match.start()].strip()
            audit_report = full_response[start_idx + end_match.end():].strip()
        
        # Parse the scorecard section into a dictionary with enhanced error handling
        scorecard = {}
        
        # Try JSON parsing first (if the scorecard is in JSON format)
        try:
            # Check if the scorecard section looks like JSON
            if scorecard_section.strip().startswith('{'):
                scorecard = json.loads(scorecard_section)
                print("✓ Scorecard parsed as JSON")
                return scorecard, audit_report
        except json.JSONDecodeError:
            # Not JSON format, continue with line-by-line parsing
            pass
        
        # Line-by-line parsing for markdown-style scorecard
        for line in scorecard_section.split('\n'):
            line = line.strip()
            if ':' in line:
                # Remove markdown formatting (* and [])
                line = line.replace('*', '').replace('[', '').replace(']', '')
                # Use regex to split on first colon only
                match = re.match(r'([^:]+):(.*)', line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    scorecard[key] = value
        
        if not scorecard:
            print("⚠️  WARNING: No valid scorecard entries found - returning empty scorecard")
        else:
            print(f"✓ Scorecard parsed successfully ({len(scorecard)} fields)")
        
        # [PRIORITY 1 FIX] Clean the audit_report (Kill List) of redundant headers
        # Remove common Meta-Reviewer artifacts that pollute state propagation
        audit_report = _clean_kill_list(audit_report)
        
        return scorecard, audit_report
        
    except Exception as e:
        # CRITICAL: Never crash on parsing errors - log and return safe defaults
        print(f"🛑 ERROR: Scorecard parsing failed with exception: {e}")
        print(f"   Returning empty scorecard to prevent system crash")
        return {}, full_response


# --- Main Orchestration Logic (EXIT CONDITION & LOGGING ENHANCED) ---
def run_refinement_loop(
    agent_a: MockAgent,
    reviewer_agent: MockAgent,
    meta_reviewer_agent: MockAgent,
    initial_prompt: str,
    max_iterations: int = 5
) -> bool:
    """
    Manages the Agent A -> Reviewer -> Meta-Reviewer Iterative Refinement Loop.
    
    Loop phases:
    1. DRAFT/REDRAFT: Agent A generates document using current prompt
    2. AUDIT: Reviewer evaluates document against previous Kill List
    3. DECISION: Check termination condition (Kill List Fixed + Not Rejected)
    4. STRATEGIZE: Meta-Reviewer generates new prompt for next iteration
    
    [PRIORITY 2 FIX] Added explicit "REJECTED" keyword check with immediate hard stop
    [PRIORITY 3 FIX] Enhanced logging in MAX_ITERATION_FAILURE block
    
    Args:
        agent_a: The Author Agent instance
        reviewer_agent: The Reviewer/Auditor Agent instance
        meta_reviewer_agent: The Meta-Reviewer/Strategist Agent instance
        initial_prompt: The initial comprehensive prompt for Agent A
        max_iterations: Maximum number of refinement iterations (default: 5)
        
    Returns:
        True if document passed audit, False if max iterations reached
    """
    current_prompt = initial_prompt
    previous_kill_list = ""
    
    print(f"\n{'='*70}")
    print(f"STARTING ITERATIVE REFINEMENT LOOP (Max {max_iterations} Iterations)")
    print(f"{'='*70}")

    for iteration in range(1, max_iterations + 1):
        print(f"\n{'='*70}")
        print(f"ITERATION {iteration}: DRAFTING & AUDIT")
        print(f"{'='*70}")

        # === PHASE 1: Draft/Redraft (Agent A) ===
        print(f"\n[PHASE 1: DRAFTING]")
        print(f"Invoking {agent_a.name}...")
        
        draft_document = agent_a.invoke(
            prompt=current_prompt,
            context={"PREVIOUS_KILL_LIST": previous_kill_list}
        )
        
        print(f"✓ Draft generated ({len(draft_document)} characters)")

        # === PHASE 2: Audit (Reviewer Agent) ===
        print(f"\n[PHASE 2: AUDIT]")
        print(f"Invoking {reviewer_agent.name}...")
        
        audit_context = {
            "NEW_DOCUMENT": draft_document,
            "PREVIOUS_KILL_LIST": previous_kill_list
        }
        
        full_review_response = reviewer_agent.invoke(
            prompt="Perform the Critical Audit and generate the Scorecard and Kill List.",
            context=audit_context
        )
        
        # Parse the reviewer's response (with robustness patch)
        scorecard, audit_report = parse_scorecard(full_review_response)
        
        print(f"✓ Audit completed")
        print(f"  Scorecard fields: {list(scorecard.keys())}")

        # === PHASE 3: Decision & Exit (Router Logic) ===
        print(f"\n[PHASE 3: DECISION]")
        
        kill_list_fixed = scorecard.get("Previous_Kill_List_Fixed", "NO").upper()
        is_rejected = "REJECTED" in full_review_response.upper()
        
        print(f"  Previous Kill List Fixed: {kill_list_fixed}")
        print(f"  Document Rejected: {is_rejected}")

        # [PRIORITY 2 FIX] EXPLICIT REJECTION CHECK - Hard stop regardless of Kill List status
        if is_rejected:
            print(f"\n{'='*70}")
            print("🛑 IMMEDIATE REJECTION DETECTED")
            print(f"{'='*70}")
            print(f"\n📋 FAILURE REPORT (Iteration {iteration}):")
            print(f"   Reason: Auditor explicitly REJECTED the document")
            print(f"   Previous_Kill_List_Fixed: {kill_list_fixed}")
            print(f"\n📄 AUDIT RESPONSE EXCERPT:")
            print(f"   {full_review_response[:500]}...")
            print(f"\n{'='*70}")
            print(f"❌ TERMINATING: Document rejected after {iteration} iteration(s)")
            print(f"{'='*70}")
            return False

        # Check success condition (Kill List Fixed AND Not Rejected)
        if kill_list_fixed == "YES":
            print(f"\n{'='*70}")
            print("🎉 SUCCESS: TERMINATION CONDITION MET")
            print("  ✓ Previous Kill List Fixed: YES")
            print("  ✓ Document NOT Rejected")
            print(f"{'='*70}")
            print(f"\nDocument passed audit after {iteration} iteration(s)")
            return True

        print(f"\n  ❌ Audit failed - continuing to refinement...")
        
        # Update the Kill List for the next iteration
        previous_kill_list = audit_report.strip()

        # === PHASE 4: Strategize (Meta-Reviewer) ===
        print(f"\n[PHASE 4: STRATEGIZE]")
        print(f"Invoking {meta_reviewer_agent.name}...")
        
        meta_context = {
            "RAW_DOCUMENT": draft_document,
            "REVIEWER_SCORECARD": json.dumps(scorecard, indent=2),
            "AUDIT_REPORT": audit_report
        }
        
        current_prompt = meta_reviewer_agent.invoke(
            prompt="Analyze the scorecard and report. Generate the next System Prompt for Agent A.",
            context=meta_context
        )
        
        print(f"✓ New prompt generated for next iteration")

    # [PRIORITY 3 FIX] ENHANCED LOGGING FOR MAX_ITERATION_FAILURE
    print(f"\n{'='*70}")
    print(f"🛑 LOOP TERMINATED: Maximum iterations ({max_iterations}) reached")
    print(f"{'='*70}")
    print(f"\n📋 DETAILED FAILURE TRACE (for Root Cause Analysis):")
    print(f"\n1. FINAL FAILED PROMPT (sent to Agent A in last iteration):")
    print(f"   {'-'*66}")
    print(f"   {current_prompt[:1000]}")
    if len(current_prompt) > 1000:
        print(f"   ... (truncated, total length: {len(current_prompt)} chars)")
    print(f"   {'-'*66}")
    
    print(f"\n2. FINAL REVIEWER RESPONSE (from last audit):")
    print(f"   {'-'*66}")
    print(f"   {full_review_response[:1000]}")
    if len(full_review_response) > 1000:
        print(f"   ... (truncated, total length: {len(full_review_response)} chars)")
    print(f"   {'-'*66}")
    
    print(f"\n3. FINAL SCORECARD:")
    print(f"   {json.dumps(scorecard, indent=4)}")
    
    print(f"\n{'='*70}")
    print(f"❌ Document failed to pass audit after {max_iterations} iterations")
    print(f"{'='*70}")
    return False


# --- Example Usage with Mock Agents ---
def create_mock_reviewer_response(iteration: int) -> str:
    """
    Creates a mock reviewer response that simulates gradual improvement.
    
    Args:
        iteration: Current iteration number
        
    Returns:
        Mock reviewer response with scorecard and audit report
    """
    if iteration == 1:
        return """
**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [N/A] (Initial run)
* Lean_Plan_Table_Present: [NO] 
* Appendix_A_Toulmin_Present: [NO] 
* Marketing_AB_Structure_Correct: [YES] 
* ADK_Architecture_Compliant: [NO] 
* Citation_Quality_Pass: [YES] 
* Financial_Model_Reality_Check: [FAIL]
**END_SCORECARD**

The document requires significant improvements. The following items must be fixed:

A. Structural Compliance:
   * The Lean Plan Table is missing 2 headers: Team and Milestones.

B. ADK Architecture Review:
   * The orchestration layer is called 'The Brain'. Correct terminology must be used.

C. Financial Model:
   * Revenue projections lack supporting evidence.
"""
    elif iteration == 2:
        return """
**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [PARTIAL] (2 of 3 items fixed)
* Lean_Plan_Table_Present: [YES] 
* Appendix_A_Toulmin_Present: [NO] 
* Marketing_AB_Structure_Correct: [YES] 
* ADK_Architecture_Compliant: [YES] 
* Citation_Quality_Pass: [YES] 
* Financial_Model_Reality_Check: [PASS]
**END_SCORECARD**

Progress made, but critical items remain:

A. Kill List Status:
   * Lean Plan Table: FIXED
   * ADK Architecture: FIXED
   * Financial Model: FIXED
   * Appendix A (Toulmin): IGNORED - Still missing

B. New Issues:
   * Citation formatting inconsistent in Section 3.
"""
    else:  # iteration >= 3
        return """
**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [YES]
* Lean_Plan_Table_Present: [YES] 
* Appendix_A_Toulmin_Present: [YES] 
* Marketing_AB_Structure_Correct: [YES] 
* ADK_Architecture_Compliant: [YES] 
* Citation_Quality_Pass: [YES] 
* Financial_Model_Reality_Check: [PASS]
**END_SCORECARD**

All previous issues have been addressed. The document meets all requirements.
"""


def main():
    """
    Demonstrates the Router Agent with mock agents that simulate improvement.
    """
    print("\n" + "="*70)
    print("ROUTER AGENT ORCHESTRATOR - DEMONSTRATION")
    print("="*70)
    
    # Initialize mock agents
    author = MockAgent("Agent A (Author)")
    reviewer = MockAgent("Reviewer Agent (Auditor)")
    meta_reviewer = MockAgent("Meta-Reviewer Agent (Strategist)")
    
    # Track iteration for mock responses
    iteration_counter = [0]
    
    # Override reviewer's invoke to return realistic mock responses
    original_reviewer_invoke = reviewer.invoke
    def mock_reviewer_invoke(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        original_reviewer_invoke(prompt, context)
        iteration_counter[0] += 1
        return create_mock_reviewer_response(iteration_counter[0])
    
    reviewer.invoke = mock_reviewer_invoke
    
    # Define the initial prompt for Agent A
    initial_author_prompt = """
You are Agent A, the Author Agent for the Mobile App Retention research document.

Your mission is to generate a comprehensive business plan that includes:
1. A Lean Plan Table with all required headers (Problem, Solution, Key Metrics, etc.)
2. Appendix A with Toulmin argument structure
3. Marketing section with A/B testing framework
4. ADK Architecture description using correct terminology
5. Financial model with evidence-based projections
6. Proper citations throughout

Begin by generating the Source Manifest and then proceed with the full document.
"""
    
    # Run the refinement loop
    success = run_refinement_loop(
        agent_a=author,
        reviewer_agent=reviewer,
        meta_reviewer_agent=meta_reviewer,
        initial_prompt=initial_author_prompt,
        max_iterations=5
    )
    
    print(f"\n{'='*70}")
    print(f"FINAL RESULT: {'SUCCESS' if success else 'FAILURE'}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
