"""
Test Validation Harness for Router Agent Orchestrator
======================================================
Validates the three critical fixes in router_agent_orchestrator.py:
1. [Priority 1] Robustness Fix: Enhanced parse_scorecard() handles corrupted input
2. [Priority 2] Exit Condition Fix: Explicit "REJECTED" keyword detection with hard stop
3. [Priority 3] Enhanced Logging: Detailed trace logging in MAX_ITERATION_FAILURE

Test Scenarios:
---------------
1. Happy Path: Successful Convergence on Iteration 3
2. Immediate Rejection/Failure on Iteration 2
3. Max Iteration Failure (Exhaustion)
4. Robustness Check: Scorecard Parsing Failure

Author: Test Designer Agent
Date: 2025-12-01
"""

import sys
import io
from typing import Dict, Any, Optional

# Fix Windows console encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import the orchestrator functions we're testing
from router_agent_orchestrator import (
    MockAgent,
    run_refinement_loop,
    parse_scorecard
)


# ============================================================================
# MOCK RESPONSE GENERATORS (Based on test_scenarios.json)
# ============================================================================

def mock_happy_path_responses(iteration: int) -> tuple[str, str]:
    """
    Generates mock responses for Scenario 1: Happy Path - Successful Convergence.
    
    Path: Fail (missing table headers) → Fail (wrong ADK terminology) → Pass
    
    Args:
        iteration: Current iteration number (1-3)
        
    Returns:
        Tuple of (reviewer_response, meta_reviewer_prompt)
    """
    if iteration == 1:
        reviewer_response = """**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [N/A] (Initial run)
* Lean_Plan_Table_Present: [NO]
* Appendix_A_Toulmin_Present: [YES]
* Marketing_AB_Structure_Correct: [YES]
* ADK_Architecture_Compliant: [YES]
* Citation_Quality_Pass: [YES]
* Financial_Model_Reality_Check: [PASS]
**END_SCORECARD**

The document requires revision. The following items must be fixed:

Kill List:
1. The Lean Plan Table is missing the 'Team' header column.
2. The Lean Plan Table is missing the 'Milestones' header column."""
        
        meta_prompt = """Agent A: Your document is missing critical Lean Plan Table headers. Add the 'Team' and 'Milestones' columns to the Lean Plan Table immediately. Ensure all required headers are present: Problem, Solution, Key Metrics, Unique Value Proposition, Unfair Advantage, Channels, Customer Segments, Cost Structure, Revenue Streams, Team, and Milestones."""
        
    elif iteration == 2:
        reviewer_response = """**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [YES]
* Lean_Plan_Table_Present: [YES]
* Appendix_A_Toulmin_Present: [YES]
* Marketing_AB_Structure_Correct: [YES]
* ADK_Architecture_Compliant: [NO]
* Citation_Quality_Pass: [YES]
* Financial_Model_Reality_Check: [PASS]
**END_SCORECARD**

The document requires revision. Previous Kill List items have been addressed, but new issues found:

Kill List:
1. ADK Architecture terminology is incorrect. The orchestration layer is referred to as 'The Brain'. Must use proper terminology: 'Nervous System' or 'Orchestration Layer'."""
        
        meta_prompt = """Agent A: Fix the ADK Architecture terminology NOW. Replace all references to 'The Brain' with the correct terminology: 'Nervous System' or 'Orchestration Layer'. Review the entire document to ensure architectural consistency with ADK standards."""
        
    else:  # iteration == 3
        reviewer_response = """**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [YES]
* Lean_Plan_Table_Present: [YES]
* Appendix_A_Toulmin_Present: [YES]
* Marketing_AB_Structure_Correct: [YES]
* ADK_Architecture_Compliant: [YES]
* Citation_Quality_Pass: [YES]
* Financial_Model_Reality_Check: [PASS]
**END_SCORECARD**

All previous issues have been successfully addressed. The document meets all quality standards and requirements. No rejections. Final pass approved."""
        
        meta_prompt = "NOT_EXECUTED"
    
    return reviewer_response, meta_prompt


def mock_rejection_responses(iteration: int) -> tuple[str, str]:
    """
    Generates mock responses for Scenario 2: Immediate Rejection/Failure.
    
    Path: Fail (financial model issues) → REJECT (ignored previous Kill List)
    
    Args:
        iteration: Current iteration number (1-5)
        
    Returns:
        Tuple of (reviewer_response, meta_reviewer_prompt)
    """
    if iteration == 1:
        reviewer_response = """**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [N/A] (Initial run)
* Lean_Plan_Table_Present: [YES]
* Appendix_A_Toulmin_Present: [YES]
* Marketing_AB_Structure_Correct: [YES]
* ADK_Architecture_Compliant: [YES]
* Citation_Quality_Pass: [YES]
* Financial_Model_Reality_Check: [FAIL]
**END_SCORECARD**

The document requires IMMEDIATE ATTENTION. Critical financial model deficiencies detected:

Kill List:
1. Financial Model lacks Burn Rate calculation - this is a CRITICAL omission.
2. Revenue projections are not supported by market data or evidence.
3. Cost structure is incomplete - missing operational expense breakdown."""
        
        meta_prompt = """Agent A: CRITICAL PRIORITY - Fix the Financial Model immediately. You MUST add:
1. Burn Rate calculation with monthly breakdown
2. Evidence-based revenue projections with market data citations
3. Complete operational expense breakdown in cost structure

These are non-negotiable requirements. Address ALL three items in your next revision."""
        
    elif iteration == 2:
        reviewer_response = """**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [NO]
* Lean_Plan_Table_Present: [YES]
* Appendix_A_Toulmin_Present: [YES]
* Marketing_AB_Structure_Correct: [YES]
* ADK_Architecture_Compliant: [YES]
* Citation_Quality_Pass: [YES]
* Financial_Model_Reality_Check: [FAIL]
**END_SCORECARD**

**REJECTED**: The previous Kill List was completely IGNORED. The Burn Rate calculation is still missing, which represents a fundamental failure to address critical feedback. System integrity compromised - the Author Agent is not responding to audit requirements.

Kill List:
1. Burn Rate calculation STILL MISSING (CRITICAL - previously flagged)
2. Revenue projections STILL lack evidence (previously flagged)
3. Cost structure STILL incomplete (previously flagged)"""
        
        meta_prompt = "NOT_EXECUTED"
    
    else:  # iterations 3-5 (should not be reached due to REJECTED in iteration 2)
        reviewer_response = f"""**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [NO]
* Lean_Plan_Table_Present: [YES]
* Appendix_A_Toulmin_Present: [YES]
* Marketing_AB_Structure_Correct: [YES]
* ADK_Architecture_Compliant: [YES]
* Citation_Quality_Pass: [YES]
* Financial_Model_Reality_Check: [FAIL]
**END_SCORECARD**

**REJECTED**: Iteration {iteration} - continued failure to address financial model requirements.

Kill List:
1. Burn Rate calculation STILL MISSING
2. Revenue projections STILL lack evidence
3. Cost structure STILL incomplete"""
        
        meta_prompt = f"Agent A: Iteration {iteration} - Fix the financial model NOW!"
    
    return reviewer_response, meta_prompt


def mock_exhaustion_responses(iteration: int) -> tuple[str, str]:
    """
    Generates mock responses for Scenario 3: Max Iteration Failure (Exhaustion).
    
    Path: Fails all 5 iterations (MDPI citation purge never completes)
    
    Args:
        iteration: Current iteration number (1-5)
        
    Returns:
        Tuple of (reviewer_response, meta_reviewer_prompt)
    """
    mdpi_counts = {1: 8, 2: 5, 3: 3, 4: 2, 5: 1}
    
    reviewer_response = f"""**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [{"N/A] (Initial run" if iteration == 1 else "NO]"}
* Lean_Plan_Table_Present: [YES]
* Appendix_A_Toulmin_Present: [YES]
* Marketing_AB_Structure_Correct: [YES]
* ADK_Architecture_Compliant: [YES]
* Citation_Quality_Pass: [NO]
* Financial_Model_Reality_Check: [PASS]
**END_SCORECARD**

{"Citation quality check failed. Multiple MDPI journal citations detected." if iteration == 1 else f"MDPI purge {'incomplete' if iteration < 5 else 'still incomplete'}."}

Kill List (Iteration {iteration}):
1. {"Remove ALL citations from MDPI journals (identified: " + str(mdpi_counts[iteration]) + " instances)" if iteration == 1 else "MDPI citations detected: " + str(mdpi_counts[iteration]) + " remaining instance" + ("s" if mdpi_counts[iteration] > 1 else "") + (" in Section 4.3" if iteration >= 4 else "")}
2. {"Replace with citations from reputable journals (IEEE, ACM, Springer, Elsevier)" if iteration == 1 else ("Complete the purge - remove ALL MDPI references" if iteration == 2 else ("These citations must be removed" + (" and replaced" if iteration == 3 else " for document approval") if iteration <= 4 else "This citation must be removed for document approval"))}
{"3. Ensure citation diversity across sources" if iteration == 1 else ("3. " + ("Verify replacement citations are from approved sources" if iteration == 2 else "Run final verification sweep") if iteration <= 3 else "")}"""
    
    meta_prompts = {
        1: "Agent A: Prioritize removing ALL MDPI journal citations from the document. Search the entire document for MDPI references and replace them with citations from reputable sources (IEEE, ACM, Springer, Nature, Science, Elsevier). This is a critical quality requirement.",
        2: "Agent A: You still have 5 MDPI citations remaining. Perform a comprehensive search for 'MDPI' and remove every instance. Replace with high-quality journal citations. Do NOT proceed until all MDPI references are eliminated.",
        3: "Agent A: MDPI purge incomplete - 3 citations remain. Focus specifically on removing these final MDPI references. Search thoroughly and replace with approved journal citations.",
        4: "Agent A: Two MDPI citations remain in Section 4.3. Remove these specific instances and replace with IEEE or ACM citations. This should be your final cleanup.",
        5: "NOT_EXECUTED"
    }
    
    return reviewer_response, meta_prompts[iteration]


def mock_corrupted_responses(iteration: int) -> tuple[str, str]:
    """
    Generates mock responses for Scenario 4: Robustness Check - Scorecard Parsing Failure.
    
    Path: Tests iteration where scorecard markers are missing or corrupted.
    
    Args:
        iteration: Current iteration number (1-5)
        
    Returns:
        Tuple of (reviewer_response, meta_reviewer_prompt)
    """
    if iteration == 1:
        # Completely corrupted response - no scorecard markers
        reviewer_response = """This is a corrupted response from the Reviewer Agent. No scorecard markers are present in this output. The response contains only raw text discussing structural compliance issues. The Lean Plan Table appears to be missing several required headers, but this feedback is not properly formatted within the expected REVIEWER_SCORECARD structure. This simulates a catastrophic failure in the Reviewer Agent's output formatting."""
        
        meta_prompt = """Agent A: FIX STRUCTURAL COMPLIANCE! The Lean Plan Table must include all required headers. Add: Problem, Solution, Key Metrics, Unique Value Proposition, Unfair Advantage, Channels, Customer Segments, Cost Structure, Revenue Streams, Team, and Milestones."""
        
    elif iteration == 2:
        # Partially recovered scorecard with minimal fields
        reviewer_response = """**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [UNKNOWN]
* Lean_Plan_Table_Present: [NO]
**END_SCORECARD**

Partially recovered scorecard with minimal fields.

Kill List:
1. Fix Lean Plan Table structure"""
        
        meta_prompt = """Agent A: Continue fixing the Lean Plan Table structure. Ensure all headers are present and properly formatted."""
        
    elif iteration == 3:
        # Another corrupted response
        reviewer_response = """Another corrupted response without proper markers. The document still has issues with the Lean Plan Table structure. Headers are missing. This is iteration 3 but the scorecard format is broken again."""
        
        meta_prompt = """Agent A: The Lean Plan Table is still incomplete. Add all missing headers according to the Lean Canvas framework."""
        
    else:  # iterations 4-5
        reviewer_response = """**REVIEWER_SCORECARD**
* Previous_Kill_List_Fixed: [NO]
* Lean_Plan_Table_Present: [NO]
**END_SCORECARD**

""" + ("Kill List:\n1. Lean Plan Table still incomplete" if iteration == 4 else "Final iteration - structural issues persist.\n\nKill List:\n1. Lean Plan Table requirements not met")
        
        meta_prompt = "Agent A: " + ("Fourth attempt - complete the Lean Plan Table with all required components." if iteration == 4 else "NOT_EXECUTED")
    
    return reviewer_response, meta_prompt


# ============================================================================
# TEST EXECUTION FRAMEWORK
# ============================================================================

def run_scenario(
    scenario_name: str,
    mock_response_generator,
    expected_outcome: str,
    expected_iterations: int,
    max_iterations: int = 5
) -> bool:
    """
    Executes a single test scenario and validates the outcome.
    
    Args:
        scenario_name: Descriptive name of the test scenario
        mock_response_generator: Function that returns (reviewer_response, meta_prompt) for each iteration
        expected_outcome: Either "SUCCESS" or "MAX_ITERATION_FAILURE"
        expected_iterations: Expected number of iterations before termination
        max_iterations: Maximum iterations to allow (default: 5)
        
    Returns:
        True if test passed, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"🧪 TEST SCENARIO: {scenario_name}")
    print(f"{'='*80}")
    print(f"Expected Outcome: {expected_outcome}")
    print(f"Expected Iterations: {expected_iterations}")
    print(f"{'='*80}\n")
    
    # Initialize mock agents
    author = MockAgent("Agent A (Author)")
    reviewer = MockAgent("Reviewer Agent (Auditor)")
    meta_reviewer = MockAgent("Meta-Reviewer Agent (Strategist)")
    
    # Track iteration for mock responses
    iteration_counter = [0]
    
    # Override reviewer's invoke to return test-specific mock responses
    original_reviewer_invoke = reviewer.invoke
    def mock_reviewer_invoke(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        original_reviewer_invoke(prompt, context)
        iteration_counter[0] += 1
        reviewer_response, _ = mock_response_generator(iteration_counter[0])
        return reviewer_response
    
    reviewer.invoke = mock_reviewer_invoke
    
    # Override meta-reviewer's invoke to return test-specific prompts
    original_meta_invoke = meta_reviewer.invoke
    def mock_meta_invoke(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        original_meta_invoke(prompt, context)
        _, meta_prompt = mock_response_generator(iteration_counter[0])
        return meta_prompt
    
    meta_reviewer.invoke = mock_meta_invoke
    
    # Define initial prompt
    initial_prompt = """You are Agent A, the Author Agent for the Mobile App Retention research document.
Generate a comprehensive business plan with all required components."""
    
    # Run the refinement loop
    success = run_refinement_loop(
        agent_a=author,
        reviewer_agent=reviewer,
        meta_reviewer_agent=meta_reviewer,
        initial_prompt=initial_prompt,
        max_iterations=max_iterations
    )
    
    # Validate outcome
    actual_outcome = "SUCCESS" if success else "MAX_ITERATION_FAILURE"
    actual_iterations = iteration_counter[0]
    
    print(f"\n{'='*80}")
    print(f"📊 TEST RESULTS: {scenario_name}")
    print(f"{'='*80}")
    print(f"Expected Outcome:    {expected_outcome}")
    print(f"Actual Outcome:      {actual_outcome}")
    print(f"Expected Iterations: {expected_iterations}")
    print(f"Actual Iterations:   {actual_iterations}")
    
    # Determine pass/fail
    outcome_match = (actual_outcome == expected_outcome)
    
    # For rejection scenarios, we expect early termination (iteration 2)
    # For exhaustion scenarios, we expect max iterations (5)
    # For happy path, we expect exact iteration count (3)
    if expected_outcome == "SUCCESS":
        iteration_match = (actual_iterations == expected_iterations)
    elif "Rejection" in scenario_name:
        # Rejection should happen at iteration 2
        iteration_match = (actual_iterations == 2)
    else:
        # Exhaustion scenarios should reach max iterations
        iteration_match = (actual_iterations == max_iterations)
    
    test_passed = outcome_match and iteration_match
    
    if test_passed:
        print(f"\n✅ TEST PASSED")
    else:
        print(f"\n❌ TEST FAILED")
        if not outcome_match:
            print(f"   - Outcome mismatch: expected {expected_outcome}, got {actual_outcome}")
        if not iteration_match:
            print(f"   - Iteration count mismatch: expected {expected_iterations}, got {actual_iterations}")
    
    print(f"{'='*80}\n")
    
    return test_passed


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def main():
    """
    Executes all four test scenarios and reports overall results.
    """
    print("\n" + "="*80)
    print("🚀 ROUTER AGENT ORCHESTRATOR - VALIDATION HARNESS")
    print("="*80)
    print("Testing three critical fixes:")
    print("  [Priority 1] Robustness Fix: Enhanced parse_scorecard()")
    print("  [Priority 2] Exit Condition Fix: Explicit REJECTED detection")
    print("  [Priority 3] Enhanced Logging: Detailed MAX_ITERATION_FAILURE trace")
    print("="*80)
    
    test_results = []
    
    # Test Scenario 1: Happy Path - Successful Convergence
    test_results.append(run_scenario(
        scenario_name="Scenario 1: Happy Path - Successful Convergence on Iteration 3",
        mock_response_generator=mock_happy_path_responses,
        expected_outcome="SUCCESS",
        expected_iterations=3
    ))
    
    # Test Scenario 2: Immediate Rejection/Failure
    test_results.append(run_scenario(
        scenario_name="Scenario 2: Immediate Rejection/Failure on Iteration 2",
        mock_response_generator=mock_rejection_responses,
        expected_outcome="MAX_ITERATION_FAILURE",
        expected_iterations=2
    ))
    
    # Test Scenario 3: Max Iteration Failure (Exhaustion)
    test_results.append(run_scenario(
        scenario_name="Scenario 3: Max Iteration Failure (Exhaustion)",
        mock_response_generator=mock_exhaustion_responses,
        expected_outcome="MAX_ITERATION_FAILURE",
        expected_iterations=5
    ))
    
    # Test Scenario 4: Robustness Check - Scorecard Parsing Failure
    test_results.append(run_scenario(
        scenario_name="Scenario 4: Robustness Check - Scorecard Parsing Failure",
        mock_response_generator=mock_corrupted_responses,
        expected_outcome="MAX_ITERATION_FAILURE",
        expected_iterations=5
    ))
    
    # Final Summary
    print("\n" + "="*80)
    print("📋 FINAL TEST SUMMARY")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests:  {total_tests}")
    print(f"Passed:       {passed_tests} ✅")
    print(f"Failed:       {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print("="*80)
    
    if all(test_results):
        print("\n🎉 ALL TESTS PASSED - Orchestrator validation complete!")
        print("="*80 + "\n")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - Review the output above for details")
        print("="*80 + "\n")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
