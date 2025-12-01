"""
Agent A: The Author Agent (Research & Drafting Orchestrator)
=============================================================
Manages the complete research and document drafting workflow, integrating
the DS-STAR data science execution engine for hypothesis testing.

Workflow Phases:
1. Research & Grounding (Chain of Verification) - Generate Source Manifest
2. Hypothesis Generation - Extract testable hypotheses from literature
3. Data Science Execution - Call DS-STAR for autonomous analysis
4. Drafting & Formatting - Generate final document with all required artifacts

This agent serves as the "Author" in the Router Agent orchestration loop,
receiving prompts from the Meta-Reviewer and producing documents for audit.
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Import DS-STAR orchestrator
try:
    from ds_star_agent import DSStarOrchestrator
    DS_STAR_AVAILABLE = True
except ImportError:
    print("Warning: DS-STAR module not found. Data science execution will be mocked.")
    DS_STAR_AVAILABLE = False


# --- Configuration Constants ---
OUTPUT_DIR = "./agent_a_output"
SOURCE_MANIFEST_FILE = "source_manifest.json"
HYPOTHESES_FILE = "hypotheses.json"
FINAL_DOCUMENT_FILE = "final_research_document.md"


# --- Mock LLM Interface (Replace with actual LLM API) ---
class MockLLM:
    """
    Simulates an LLM interface for the Author Agent.
    In production, replace with actual LLM API calls (OpenAI, Anthropic, etc.)
    """
    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        
    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a response from the LLM.
        
        Args:
            prompt: The instruction/prompt for the LLM
            context: Additional context variables to inject
            
        Returns:
            The LLM's response as a string
        """
        print(f"\n[LLM Generating ({self.model_name})]")
        print(f"  Prompt preview: {prompt[:150]}...")
        if context:
            print(f"  Context keys: {list(context.keys())}")
        
        # In production, this would be: return openai.ChatCompletion.create(...)
        return f"Mock LLM response for: {prompt[:50]}..."


# --- Author Agent Main Class ---
class AuthorAgent:
    """
    The Author Agent (Agent A) - Orchestrates the complete research and
    drafting workflow with integrated DS-STAR data science execution.
    """
    
    def __init__(
        self, 
        llm: MockLLM,
        output_dir: str = OUTPUT_DIR,
        kaggle_dataset: Optional[str] = None
    ):
        """
        Initializes the Author Agent.
        
        Args:
            llm: The LLM instance for text generation
            output_dir: Directory for saving outputs
            kaggle_dataset: Name of Kaggle dataset for DS-STAR (optional)
        """
        self.llm = llm
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.kaggle_dataset = kaggle_dataset
        
        # State management
        self.source_manifest = []
        self.hypotheses = []
        self.ds_star_results = None
        self.previous_kill_list = ""
        
        print(f"\n{'='*70}")
        print("AUTHOR AGENT (Agent A) - Initialized")
        print(f"{'='*70}")
        print(f"  Output directory: {self.output_dir}")
        print(f"  Kaggle dataset: {self.kaggle_dataset or 'Not specified'}")
        print(f"  LLM model: {self.llm.model_name}")
    
    
    # --- Internal Tool: DS-STAR Integration ---
    def run_ds_star_analysis(
        self, 
        hypotheses: List[str],
        dataset_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Internal tool that wraps the DS-STAR orchestrator for autonomous
        data science execution.
        
        This tool is called during Phase 3 (Data Science Execution) to
        test the generated hypotheses against real data.
        
        Args:
            hypotheses: List of testable hypotheses to validate
            dataset_name: Kaggle dataset name (uses self.kaggle_dataset if None)
            
        Returns:
            Dictionary containing DS-STAR execution results:
            - success: bool
            - output_path: str (path to results)
            - summary: str (analysis summary)
        """
        print(f"\n{'='*70}")
        print("TOOL: run_ds_star_analysis")
        print(f"{'='*70}")
        print(f"  Hypotheses to test: {len(hypotheses)}")
        
        dataset = dataset_name or self.kaggle_dataset
        
        if not dataset:
            print("  ⚠️  Warning: No dataset specified, returning mock results")
            return {
                "success": False,
                "output_path": None,
                "summary": "No dataset specified for analysis",
                "error": "DATASET_NOT_SPECIFIED"
            }
        
        if not DS_STAR_AVAILABLE:
            print("  ⚠️  Warning: DS-STAR module not available, returning mock results")
            return {
                "success": False,
                "output_path": None,
                "summary": "DS-STAR module not available",
                "error": "DS_STAR_NOT_AVAILABLE"
            }
        
        try:
            # Initialize DS-STAR orchestrator
            print(f"\n  Initializing DS-STAR orchestrator...")
            orchestrator = DSStarOrchestrator(
                hypotheses=hypotheses,
                dataset_name=dataset,
                max_iterations=15
            )
            
            # Execute DS-STAR pipeline
            print(f"  Executing DS-STAR pipeline...")
            success = orchestrator.run()
            
            # Collect results
            results = {
                "success": success,
                "output_path": str(orchestrator.finalyzer.output_dir) if success else None,
                "summary": f"DS-STAR execution {'completed' if success else 'incomplete'}",
                "hypotheses_tested": hypotheses,
                "dataset": dataset
            }
            
            print(f"\n  ✓ DS-STAR execution {'completed' if success else 'incomplete'}")
            
            return results
            
        except Exception as e:
            print(f"\n  ✗ DS-STAR execution failed: {e}")
            return {
                "success": False,
                "output_path": None,
                "summary": f"DS-STAR execution failed: {str(e)}",
                "error": str(e)
            }
    
    
    # --- Phase 1: Research & Grounding (Chain of Verification) ---
    def phase_1_research_and_grounding(
        self, 
        research_topic: str,
        previous_kill_list: str = ""
    ) -> List[Dict[str, str]]:
        """
        Phase 1: Research & Grounding using Chain of Verification.
        
        Generates a comprehensive Source Manifest by:
        1. Identifying key research questions
        2. Generating search queries
        3. Simulating literature review
        4. Creating structured source manifest
        
        Args:
            research_topic: The main research topic/question
            previous_kill_list: Feedback from previous audit (if any)
            
        Returns:
            List of source manifest entries (dictionaries)
        """
        print(f"\n{'='*70}")
        print("PHASE 1: RESEARCH & GROUNDING (Chain of Verification)")
        print(f"{'='*70}")
        
        research_prompt = f"""
You are the Author Agent conducting a comprehensive literature review.

Research Topic: {research_topic}

{f"Previous Audit Feedback (Kill List):{chr(10)}{previous_kill_list}" if previous_kill_list else ""}

Your task is to generate a comprehensive Source Manifest using Chain of Verification:

1. Identify 5-7 key research questions related to the topic
2. For each question, generate relevant search queries
3. Simulate finding authoritative sources (academic papers, industry reports)
4. Create a structured Source Manifest

Return a JSON array of source entries, each with:
- source_id: Unique identifier (e.g., "S1", "S2")
- title: Source title
- authors: List of authors
- year: Publication year
- type: "academic_paper", "industry_report", "book", etc.
- key_findings: Brief summary of relevant findings
- relevance_score: 1-10 rating of relevance to research topic
- citation: Proper citation format

Example:
[
  {{
    "source_id": "S1",
    "title": "Mobile App Retention Strategies in 2024",
    "authors": ["Smith, J.", "Johnson, A."],
    "year": 2024,
    "type": "academic_paper",
    "key_findings": "Personalization increases retention by 34%",
    "relevance_score": 9,
    "citation": "Smith, J., & Johnson, A. (2024). Mobile App Retention..."
  }}
]
"""
        
        # Generate source manifest using LLM
        response = self.llm.generate(
            prompt=research_prompt,
            context={"research_topic": research_topic}
        )
        
        # Parse response (in production, parse actual JSON from LLM)
        # Mock implementation - create sample source manifest
        self.source_manifest = [
            {
                "source_id": "S1",
                "title": "Mobile App Retention Strategies in 2024",
                "authors": ["Smith, J.", "Johnson, A."],
                "year": 2024,
                "type": "academic_paper",
                "key_findings": "Personalization increases retention by 34%",
                "relevance_score": 9,
                "citation": "Smith, J., & Johnson, A. (2024). Mobile App Retention Strategies..."
            },
            {
                "source_id": "S2",
                "title": "Data-Driven Product Development",
                "authors": ["Chen, L."],
                "year": 2023,
                "type": "industry_report",
                "key_findings": "A/B testing reduces feature failure rate by 45%",
                "relevance_score": 8,
                "citation": "Chen, L. (2023). Data-Driven Product Development..."
            }
        ]
        
        # Save source manifest
        manifest_path = self.output_dir / SOURCE_MANIFEST_FILE
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.source_manifest, f, indent=2)
        
        print(f"\n✓ Source Manifest generated")
        print(f"  Total sources: {len(self.source_manifest)}")
        print(f"  Saved to: {manifest_path}")
        
        return self.source_manifest
    
    
    # --- Phase 2: Hypothesis Generation ---
    def phase_2_hypothesis_generation(
        self,
        source_manifest: List[Dict[str, str]],
        research_topic: str
    ) -> List[str]:
        """
        Phase 2: Hypothesis Generation based on literature review.
        
        Extracts testable hypotheses from the Source Manifest that can be
        validated through data science analysis.
        
        Args:
            source_manifest: The source manifest from Phase 1
            research_topic: The main research topic
            
        Returns:
            List of testable hypotheses (strings)
        """
        print(f"\n{'='*70}")
        print("PHASE 2: HYPOTHESIS GENERATION")
        print(f"{'='*70}")
        
        hypothesis_prompt = f"""
You are the Author Agent generating testable hypotheses.

Research Topic: {research_topic}

Source Manifest (Literature Review):
{json.dumps(source_manifest, indent=2)}

Based on the literature review, generate 3-5 clear, testable hypotheses that:
1. Are specific and measurable
2. Can be validated through data analysis
3. Are grounded in the literature (cite sources)
4. Follow the format: "H1: [Hypothesis statement]"

Return a JSON array of hypothesis objects, each with:
- hypothesis_id: "H1", "H2", etc.
- statement: The hypothesis statement
- rationale: Why this hypothesis is important (cite sources)
- metrics: List of metrics needed to test this hypothesis
- data_requirements: What data is needed

Example:
[
  {{
    "hypothesis_id": "H1",
    "statement": "User engagement increases with personalized content recommendations",
    "rationale": "Based on Smith & Johnson (2024), personalization drives retention",
    "metrics": ["engagement_rate", "session_duration", "retention_rate"],
    "data_requirements": ["user_behavior_data", "content_interaction_logs"]
  }}
]
"""
        
        # Generate hypotheses using LLM
        response = self.llm.generate(
            prompt=hypothesis_prompt,
            context={"source_manifest": source_manifest}
        )
        
        # Parse response (in production, parse actual JSON from LLM)
        # Mock implementation - create sample hypotheses
        hypothesis_objects = [
            {
                "hypothesis_id": "H1",
                "statement": "User engagement increases with personalized content recommendations",
                "rationale": "Based on Smith & Johnson (2024), personalization drives retention",
                "metrics": ["engagement_rate", "session_duration", "retention_rate"],
                "data_requirements": ["user_behavior_data", "content_interaction_logs"]
            },
            {
                "hypothesis_id": "H2",
                "statement": "Churn rate is negatively correlated with feature adoption rate",
                "rationale": "Chen (2023) shows A/B testing reduces failure rates",
                "metrics": ["churn_rate", "feature_adoption_rate"],
                "data_requirements": ["user_churn_data", "feature_usage_logs"]
            },
            {
                "hypothesis_id": "H3",
                "statement": "Premium users have 2x higher retention than free users",
                "rationale": "Industry standard for SaaS products",
                "metrics": ["retention_rate", "user_tier"],
                "data_requirements": ["subscription_data", "user_activity_logs"]
            }
        ]
        
        # Extract hypothesis statements
        self.hypotheses = [h["statement"] for h in hypothesis_objects]
        
        # Save hypotheses
        hypotheses_path = self.output_dir / HYPOTHESES_FILE
        with open(hypotheses_path, 'w', encoding='utf-8') as f:
            json.dump(hypothesis_objects, f, indent=2)
        
        print(f"\n✓ Hypotheses generated")
        print(f"  Total hypotheses: {len(self.hypotheses)}")
        print(f"  Saved to: {hypotheses_path}")
        
        for h in self.hypotheses:
            print(f"    - {h}")
        
        return self.hypotheses
    
    
    # --- Phase 3: Data Science Execution ---
    def phase_3_data_science_execution(
        self,
        hypotheses: List[str]
    ) -> Dict[str, Any]:
        """
        Phase 3: Data Science Execution using DS-STAR.
        
        Calls the internal DS-STAR tool to execute autonomous data science
        analysis for hypothesis testing.
        
        Args:
            hypotheses: List of hypotheses to test
            
        Returns:
            DS-STAR execution results
        """
        print(f"\n{'='*70}")
        print("PHASE 3: DATA SCIENCE EXECUTION (DS-STAR)")
        print(f"{'='*70}")
        
        # Call internal DS-STAR tool
        self.ds_star_results = self.run_ds_star_analysis(hypotheses)
        
        print(f"\n✓ Data science execution completed")
        print(f"  Success: {self.ds_star_results.get('success', False)}")
        if self.ds_star_results.get('output_path'):
            print(f"  Results path: {self.ds_star_results['output_path']}")
        
        return self.ds_star_results
    
    
    # --- Phase 4: Drafting & Formatting ---
    def phase_4_drafting_and_formatting(
        self,
        research_topic: str,
        source_manifest: List[Dict[str, str]],
        hypotheses: List[str],
        ds_star_results: Dict[str, Any],
        previous_kill_list: str = ""
    ) -> str:
        """
        Phase 4: Drafting & Formatting the final research document.
        
        Generates a comprehensive document with all required artifacts:
        - Lean Plan Table
        - A/B Marketing Plan
        - Executive Summary
        - Appendix A (Toulmin Argument Structure)
        - ADK Architecture Description
        - Financial Model
        - Citations
        
        Args:
            research_topic: The main research topic
            source_manifest: The source manifest from Phase 1
            hypotheses: The hypotheses from Phase 2
            ds_star_results: The DS-STAR results from Phase 3
            previous_kill_list: Feedback from previous audit (if any)
            
        Returns:
            The final document as a markdown string
        """
        print(f"\n{'='*70}")
        print("PHASE 4: DRAFTING & FORMATTING")
        print(f"{'='*70}")
        
        drafting_prompt = f"""
You are the Author Agent drafting the final research document.

Research Topic: {research_topic}

Source Manifest:
{json.dumps(source_manifest, indent=2)}

Hypotheses Tested:
{json.dumps(hypotheses, indent=2)}

DS-STAR Analysis Results:
{json.dumps(ds_star_results, indent=2)}

{f"Previous Audit Feedback (Kill List):{chr(10)}{previous_kill_list}" if previous_kill_list else ""}

Generate a comprehensive business plan document that includes:

1. **Executive Summary**
   - Problem statement
   - Solution overview
   - Key findings from DS-STAR analysis

2. **Lean Plan Table**
   - Problem
   - Solution
   - Key Metrics
   - Unique Value Proposition
   - Unfair Advantage
   - Channels
   - Customer Segments
   - Cost Structure
   - Revenue Streams
   - Team
   - Milestones

3. **Market Analysis & A/B Testing Framework**
   - Target market definition
   - A/B testing strategy for feature validation
   - Expected outcomes

4. **Data Science Findings**
   - Hypothesis testing results from DS-STAR
   - Statistical analysis summary
   - Visualizations and charts (reference PNG files)

5. **ADK Architecture Description**
   - Multi-agent system design
   - Orchestration layer (Router Agent)
   - Agent interactions (Agent A, Reviewer, Meta-Reviewer)
   - DS-STAR integration

6. **Financial Model**
   - Revenue projections (with evidence from DS-STAR)
   - Cost analysis
   - Break-even analysis

7. **Appendix A: Toulmin Argument Structure**
   - Claim
   - Grounds (evidence from DS-STAR)
   - Warrant
   - Backing
   - Qualifier
   - Rebuttal

8. **References**
   - Properly formatted citations from Source Manifest

Format the document in clean Markdown with proper headers, tables, and citations.
"""
        
        # Generate final document using LLM
        final_document = self.llm.generate(
            prompt=drafting_prompt,
            context={
                "source_manifest": source_manifest,
                "hypotheses": hypotheses,
                "ds_star_results": ds_star_results
            }
        )
        
        # In production, this would be the actual LLM-generated document
        # Mock implementation - create sample document structure
        final_document = f"""# {research_topic}

## Executive Summary

This research document presents a comprehensive analysis of {research_topic}, 
integrating literature review, hypothesis testing, and data science validation.

**Key Findings:**
- {len(hypotheses)} hypotheses tested using DS-STAR autonomous analysis
- {len(source_manifest)} authoritative sources reviewed
- Data-driven insights validate the proposed solution

## 1. Lean Plan Table

| Element | Description |
|---------|-------------|
| **Problem** | User retention challenges in mobile applications |
| **Solution** | AI-powered personalization engine with DS-STAR validation |
| **Key Metrics** | Retention rate, engagement score, churn rate |
| **Unique Value Proposition** | Data-driven personalization backed by rigorous hypothesis testing |
| **Unfair Advantage** | Proprietary DS-STAR multi-agent system for continuous optimization |
| **Channels** | Mobile app stores, direct marketing, partnerships |
| **Customer Segments** | SaaS companies, mobile app developers |
| **Cost Structure** | Development, infrastructure, data science team |
| **Revenue Streams** | Subscription model (tiered pricing) |
| **Team** | Engineering, Data Science, Product Management |
| **Milestones** | Q1: MVP, Q2: Beta, Q3: Launch, Q4: Scale |

## 2. Market Analysis & A/B Testing Framework

### Target Market
- Mobile app companies with >10K MAU
- SaaS platforms seeking retention optimization

### A/B Testing Strategy
Based on Chen (2023), our A/B testing framework includes:
- Feature flags for controlled rollout
- Statistical significance testing (p < 0.05)
- Multi-variate testing for optimization

## 3. Data Science Findings (DS-STAR Analysis)

### Hypotheses Tested
{chr(10).join([f"- {h}" for h in hypotheses])}

### Results Summary
DS-STAR execution status: {ds_star_results.get('success', 'Unknown')}
Analysis output: {ds_star_results.get('output_path', 'Not available')}

{ds_star_results.get('summary', 'Analysis in progress')}

## 4. ADK Architecture Description

Our system leverages a multi-agent architecture:

### Router Agent (Orchestrator)
- Manages the Agent A → Reviewer → Meta-Reviewer loop
- Implements termination conditions based on audit feedback
- Ensures quality through iterative refinement

### Agent A (Author Agent)
- Executes 4-phase research workflow
- Integrates DS-STAR for autonomous data science
- Generates comprehensive business plans

### DS-STAR Engine
- 5-step iterative refinement (Analyzer → Planner → Coder → Verifier → Finalyzer)
- LLM-as-a-Judge verification
- Academic-standard output formatting

## 5. Financial Model

### Revenue Projections
Based on DS-STAR analysis showing {hypotheses[0]}:
- Year 1: $500K (100 customers @ $5K/year)
- Year 2: $2M (400 customers, 300% growth)
- Year 3: $5M (1000 customers, 150% growth)

### Cost Structure
- Development: $200K/year
- Infrastructure: $50K/year
- Team: $400K/year
- Total: $650K/year

### Break-even Analysis
Break-even at 130 customers (Month 8 of Year 1)

## 6. Appendix A: Toulmin Argument Structure

**Claim:** Personalized content recommendations increase user retention

**Grounds:** DS-STAR analysis validates hypothesis H1, showing statistically 
significant correlation between personalization and engagement

**Warrant:** Smith & Johnson (2024) demonstrate that personalization increases 
retention by 34% across mobile applications

**Backing:** Industry data from Chen (2023) confirms A/B testing reduces 
feature failure rates by 45%

**Qualifier:** Results apply to mobile applications with >10K MAU

**Rebuttal:** Privacy concerns may limit personalization effectiveness in 
regulated industries

## 7. References

{chr(10).join([f"- {s['citation']}" for s in source_manifest])}

---

**Document Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Author Agent:** Agent A (Autonomous Research & Drafting System)
**DS-STAR Version:** 1.0
"""
        
        # Save final document
        document_path = self.output_dir / FINAL_DOCUMENT_FILE
        with open(document_path, 'w', encoding='utf-8') as f:
            f.write(final_document)
        
        print(f"\n✓ Final document generated")
        print(f"  Length: {len(final_document)} characters")
        print(f"  Saved to: {document_path}")
        
        return final_document
    
    
    # --- Main Workflow Orchestration ---
    def execute_full_workflow(
        self,
        research_topic: str,
        previous_kill_list: str = ""
    ) -> str:
        """
        Executes the complete 4-phase research and drafting workflow.
        
        This is the main entry point called by the Router Agent orchestrator.
        
        Args:
            research_topic: The main research topic/question
            previous_kill_list: Feedback from previous audit iteration
            
        Returns:
            The final document as a string
        """
        print(f"\n{'='*70}")
        print("AUTHOR AGENT - FULL WORKFLOW EXECUTION")
        print(f"{'='*70}")
        print(f"Research Topic: {research_topic}")
        if previous_kill_list:
            print(f"Previous Kill List: {len(previous_kill_list)} chars")
        
        self.previous_kill_list = previous_kill_list
        
        # Phase 1: Research & Grounding
        source_manifest = self.phase_1_research_and_grounding(
            research_topic=research_topic,
            previous_kill_list=previous_kill_list
        )
        
        # Phase 2: Hypothesis Generation
        hypotheses = self.phase_2_hypothesis_generation(
            source_manifest=source_manifest,
            research_topic=research_topic
        )
        
        # Phase 3: Data Science Execution
        ds_star_results = self.phase_3_data_science_execution(
            hypotheses=hypotheses
        )
        
        # Phase 4: Drafting & Formatting
        final_document = self.phase_4_drafting_and_formatting(
            research_topic=research_topic,
            source_manifest=source_manifest,
            hypotheses=hypotheses,
            ds_star_results=ds_star_results,
            previous_kill_list=previous_kill_list
        )
        
        print(f"\n{'='*70}")
        print("✓ FULL WORKFLOW COMPLETED")
        print(f"{'='*70}")
        print(f"  Source Manifest: {len(source_manifest)} sources")
        print(f"  Hypotheses: {len(hypotheses)}")
        print(f"  DS-STAR Success: {ds_star_results.get('success', False)}")
        print(f"  Final Document: {len(final_document)} chars")
        print(f"{'='*70}\n")
        
        return final_document
    
    
    # --- Router Agent Interface ---
    def invoke(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Router Agent interface for invoking the Author Agent.
        
        This method is called by the Router Agent orchestrator during the
        refinement loop.
        
        Args:
            prompt: The system prompt from Meta-Reviewer (or initial prompt)
            context: Context including PREVIOUS_KILL_LIST
            
        Returns:
            The generated document as a string
        """
        print(f"\n{'='*70}")
        print("AUTHOR AGENT - Router Interface Invoked")
        print(f"{'='*70}")
        
        # Extract context
        previous_kill_list = ""
        if context and "PREVIOUS_KILL_LIST" in context:
            previous_kill_list = context["PREVIOUS_KILL_LIST"]
        
        # Extract research topic from prompt (simple parsing)
        # In production, use more sophisticated prompt parsing
        research_topic = "Mobile App Retention Strategy"
        if "research" in prompt.lower() or "topic" in prompt.lower():
            # Extract topic from prompt
            lines = prompt.split('\n')
            for line in lines:
                if "topic" in line.lower() or "research" in line.lower():
                    research_topic = line.split(':')[-1].strip()
                    break
        
        # Execute full workflow
        document = self.execute_full_workflow(
            research_topic=research_topic,
            previous_kill_list=previous_kill_list
        )
        
        return document


# --- Example Usage ---
def main():
    """
    Demonstrates the Author Agent with a complete workflow execution.
    """
    print("\n" + "="*70)
    print("AUTHOR AGENT (Agent A) - DEMONSTRATION")
    print("="*70)
    
    # Initialize LLM (replace with actual LLM API)
    llm = MockLLM(model_name="gpt-4")
    
    # Initialize Author Agent
    agent_a = AuthorAgent(
        llm=llm,
        output_dir="./agent_a_output",
        kaggle_dataset="user-behavior-analytics"
    )
    
    # Define research topic
    research_topic = "Mobile App Retention Strategy Using AI-Powered Personalization"
    
    # Execute full workflow
    final_document = agent_a.execute_full_workflow(
        research_topic=research_topic,
        previous_kill_list=""  # Initial run, no previous feedback
    )
    
    print(f"\n{'='*70}")
    print("DEMONSTRATION COMPLETE")
    print(f"{'='*70}")
    print(f"\nFinal document preview:")
    print(f"{final_document[:500]}...")
    print(f"\nTotal length: {len(final_document)} characters")
    print(f"{'='*70}\n")


# --- Integration Example with Router Agent ---
def integration_example():
    """
    Demonstrates how the Router Agent would invoke the Author Agent.
    """
    print("\n" + "="*70)
    print("INTEGRATION EXAMPLE: Router Agent → Author Agent")
    print("="*70)
    
    # Initialize Author Agent
    llm = MockLLM(model_name="gpt-4")
    agent_a = AuthorAgent(llm=llm, kaggle_dataset="user-behavior-analytics")
    
    # Simulate Router Agent invocation
    initial_prompt = """
You are Agent A, the Author Agent for the Mobile App Retention research document.

Your mission is to generate a comprehensive business plan that includes:
1. A Lean Plan Table with all required headers
2. Appendix A with Toulmin argument structure
3. Marketing section with A/B testing framework
4. ADK Architecture description using correct terminology
5. Financial model with evidence-based projections
6. Proper citations throughout

Research Topic: Mobile App Retention Strategy Using AI-Powered Personalization

Begin by generating the Source Manifest and then proceed with the full document.
"""
    
    # Invoke Author Agent (as Router Agent would)
    document = agent_a.invoke(
        prompt=initial_prompt,
        context={"PREVIOUS_KILL_LIST": ""}
    )
    
    print(f"\n{'='*70}")
    print("INTEGRATION EXAMPLE COMPLETE")
    print(f"{'='*70}")
    print(f"\nDocument generated: {len(document)} characters")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    # Run demonstration
    main()
    
    # Run integration example
    # integration_example()
