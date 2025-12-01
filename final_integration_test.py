"""
End-to-End Integration Test for Autonomous Scientific Discovery Agent
======================================================================

This test validates the complete multi-agent system by running the orchestrator
and verifying that the final output document meets all structural requirements.

Test Objectives:
----------------
1. Verify successful convergence of the iterative refinement loop
2. Validate presence of all required document components
3. Confirm ADK architecture compliance
4. Check citation quality and evidence standards

Success Criteria:
-----------------
- Loop terminates with success=True (Kill List Fixed + Not Rejected)
- Final document contains all required structural markers
- All agents execute without errors
"""

import sys
import re
from typing import List, Tuple


def test_orchestrator_convergence():
    """
    Test 1: Verify that the orchestrator successfully converges.
    
    Expected: run_refinement_loop returns True within max iterations.
    """
    print("\n" + "="*70)
    print("TEST 1: ORCHESTRATOR CONVERGENCE")
    print("="*70)
    
    # Import and run the main orchestrator
    from main_capstone_orchestrator import main
    
    print("\nRunning main orchestrator...")
    success = main()
    
    assert success is True, "Orchestrator failed to converge successfully"
    print("\n✓ TEST 1 PASSED: Orchestrator converged successfully")
    
    return success


def test_document_structural_compliance():
    """
    Test 2: Verify that the final document contains all required components.
    
    Expected: Final document includes markers for all required sections.
    """
    print("\n" + "="*70)
    print("TEST 2: DOCUMENT STRUCTURAL COMPLIANCE")
    print("="*70)
    
    # Get the final document from Agent A
    from main_capstone_orchestrator import AgentA
    
    agent_a = AgentA()
    
    # Simulate the final iteration (3rd call)
    agent_a.invoke("Generate final document", {})
    agent_a.invoke("Generate final document", {})
    final_document = agent_a.invoke("Generate final document", {})
    
    print(f"\nFinal document length: {len(final_document)} characters")
    
    # Define required structural markers
    required_markers = [
        ("Lean Business Plan Table", r"Lean Business Plan Table"),
        ("ADK Architecture", r"ADK Architecture"),
        ("Toulmin", r"Toulmin"),
        ("Orchestration Layer", r"Orchestration Layer"),
        ("MCP", r"MCP"),
        ("References", r"References"),
        ("A/B Testing", r"A/B Testing"),
        ("Financial Model", r"Financial Model"),
    ]
    
    print("\nChecking for required structural markers:")
    all_present = True
    
    for marker_name, marker_pattern in required_markers:
        if re.search(marker_pattern, final_document, re.IGNORECASE):
            print(f"  ✓ {marker_name}: FOUND")
        else:
            print(f"  ✗ {marker_name}: MISSING")
            all_present = False
    
    assert all_present, "Final document is missing required structural components"
    print("\n✓ TEST 2 PASSED: All required components present")
    
    return final_document


def test_lean_plan_table_headers():
    """
    Test 3: Verify that the Lean Plan Table contains all 11 required headers.
    
    Expected: Table includes Problem, Solution, Key Metrics, UVP, Unfair Advantage,
              Channels, Customer Segments, Cost Structure, Revenue Streams, Team, Milestones.
    """
    print("\n" + "="*70)
    print("TEST 3: LEAN PLAN TABLE COMPLETENESS")
    print("="*70)
    
    from main_capstone_orchestrator import AgentA
    
    agent_a = AgentA()
    agent_a.invoke("", {})
    agent_a.invoke("", {})
    final_document = agent_a.invoke("", {})
    
    # Required headers for Lean Plan Table
    required_headers = [
        "Problem",
        "Solution",
        "Key Metrics",
        "Unique Value Proposition",
        "Unfair Advantage",
        "Channels",
        "Customer Segments",
        "Cost Structure",
        "Revenue Streams",
        "Team",
        "Milestones",
    ]
    
    print(f"\nChecking for {len(required_headers)} required table headers:")
    all_headers_present = True
    
    for header in required_headers:
        if header in final_document:
            print(f"  ✓ {header}: FOUND")
        else:
            print(f"  ✗ {header}: MISSING")
            all_headers_present = False
    
    assert all_headers_present, "Lean Plan Table is missing required headers"
    print("\n✓ TEST 3 PASSED: All 11 table headers present")


def test_toulmin_argument_completeness():
    """
    Test 4: Verify that Appendix A contains all 6 Toulmin components.
    
    Expected: Claim, Grounds, Warrant, Backing, Qualifier, Rebuttal all present.
    """
    print("\n" + "="*70)
    print("TEST 4: TOULMIN ARGUMENT COMPLETENESS")
    print("="*70)
    
    from main_capstone_orchestrator import AgentA
    
    agent_a = AgentA()
    agent_a.invoke("", {})
    agent_a.invoke("", {})
    final_document = agent_a.invoke("", {})
    
    # Required Toulmin components
    toulmin_components = [
        "Claim",
        "Grounds",
        "Warrant",
        "Backing",
        "Qualifier",
        "Rebuttal",
    ]
    
    print(f"\nChecking for {len(toulmin_components)} Toulmin components:")
    all_components_present = True
    
    for component in toulmin_components:
        if component in final_document:
            print(f"  ✓ {component}: FOUND")
        else:
            print(f"  ✗ {component}: MISSING")
            all_components_present = False
    
    assert all_components_present, "Toulmin argument is missing required components"
    print("\n✓ TEST 4 PASSED: All 6 Toulmin components present")


def test_citation_count():
    """
    Test 5: Verify that the document contains at least 5 citations.
    
    Expected: Minimum 5 references in the References section.
    """
    print("\n" + "="*70)
    print("TEST 5: CITATION QUALITY")
    print("="*70)
    
    from main_capstone_orchestrator import AgentA
    
    agent_a = AgentA()
    agent_a.invoke("", {})
    agent_a.invoke("", {})
    final_document = agent_a.invoke("", {})
    
    # Count citations (looking for [1], [2], etc. or numbered list items)
    citation_pattern = r'\[\d+\]'
    citations = re.findall(citation_pattern, final_document)
    unique_citations = set(citations)
    
    print(f"\nCitation count: {len(unique_citations)}")
    print(f"Citations found: {sorted(unique_citations)}")
    
    assert len(unique_citations) >= 5, f"Insufficient citations: {len(unique_citations)} < 5"
    print("\n✓ TEST 5 PASSED: Minimum citation requirement met")


def test_adk_architecture_compliance():
    """
    Test 6: Verify ADK architecture terminology and MCP compliance.
    
    Expected: Uses "Orchestration Layer" (not "The Brain"), mentions MCP.
    """
    print("\n" + "="*70)
    print("TEST 6: ADK ARCHITECTURE COMPLIANCE")
    print("="*70)
    
    from main_capstone_orchestrator import AgentA
    
    agent_a = AgentA()
    agent_a.invoke("", {})
    agent_a.invoke("", {})
    final_document = agent_a.invoke("", {})
    
    print("\nChecking ADK compliance:")
    
    # Check for correct terminology
    has_orchestration_layer = "Orchestration Layer" in final_document
    has_mcp = "MCP" in final_document
    has_wrong_term = "The Brain" in final_document
    
    print(f"  {'✓' if has_orchestration_layer else '✗'} Orchestration Layer: {'FOUND' if has_orchestration_layer else 'MISSING'}")
    print(f"  {'✓' if has_mcp else '✗'} MCP Compliance: {'FOUND' if has_mcp else 'MISSING'}")
    print(f"  {'✓' if not has_wrong_term else '✗'} No deprecated terms: {'PASS' if not has_wrong_term else 'FAIL (found The Brain)'}")
    
    assert has_orchestration_layer, "Missing 'Orchestration Layer' terminology"
    assert has_mcp, "Missing MCP compliance statement"
    assert not has_wrong_term, "Document uses deprecated term 'The Brain'"
    
    print("\n✓ TEST 6 PASSED: ADK architecture compliance verified")


def run_all_tests():
    """
    Runs all integration tests and reports results.
    """
    print("\n" + "="*70)
    print("AUTONOMOUS SCIENTIFIC DISCOVERY AGENT")
    print("END-TO-END INTEGRATION TEST SUITE")
    print("="*70)
    
    tests = [
        ("Orchestrator Convergence", test_orchestrator_convergence),
        ("Document Structural Compliance", test_document_structural_compliance),
        ("Lean Plan Table Completeness", test_lean_plan_table_headers),
        ("Toulmin Argument Completeness", test_toulmin_argument_completeness),
        ("Citation Quality", test_citation_count),
        ("ADK Architecture Compliance", test_adk_architecture_compliance),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ TEST FAILED: {test_name}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ TEST ERROR: {test_name}")
            print(f"  Unexpected error: {e}")
            failed += 1
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"\nTotal Tests: {len(tests)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"\nSuccess Rate: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - System is ready for production!")
        print("="*70)
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED - Review errors above")
        print("="*70)
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
