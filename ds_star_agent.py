"""
DS-STAR: Data Science Execution Engine (Multi-Agent System)
============================================================
Implements the 5-step iterative refinement methodology (Nam et al., 2025)
for autonomous data science hypothesis testing.

Pipeline: Analyzer → Planner → Coder → Verifier/Router Loop → Finalyzer

This engine executes a validated data science plan to produce final analytical
output by iteratively refining code through LLM-as-a-Judge verification.

Reference Architecture:
- Analyzer: Data file analysis and description generation
- Planner: Granular execution step planning
- Coder: Python script implementation
- Verifier: LLM-as-a-Judge for sufficiency evaluation
- Router: Refinement decision (Add/Correct/Remove steps)
- Finalyzer: Academic-standard output formatting
"""

import os
import json
import re
import subprocess
import sys
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import tempfile


# --- Configuration Constants ---
MAX_ITERATIONS = 15
KAGGLE_DATASET_DIR = "./kaggle_datasets"
OUTPUT_DIR = "./ds_star_output"
TEMP_SCRIPT_DIR = "./ds_star_temp_scripts"


# --- Mock Agent Interface (Replace with actual LLM API calls) ---
class MockLLMAgent:
    """
    Simulates an LLM agent interface for the DS-STAR pipeline.
    In production, replace with actual LLM API calls (OpenAI, Anthropic, etc.)
    """
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        
    def invoke(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Simulates invoking an LLM agent and getting a response.
        
        Args:
            prompt: The instruction/prompt for the agent
            context: Additional context variables to inject
            
        Returns:
            The agent's response as a string
        """
        print(f"\n[{self.name} Invoking...]")
        print(f"  Role: {self.role}")
        print(f"  Prompt preview: {prompt[:150]}...")
        if context:
            print(f"  Context keys: {list(context.keys())}")
        
        # In production, this would be: return llm_api.generate(prompt, context=context)
        return f"Mock response from {self.name}"


# --- Step 1: Analyzer Agent (Data File Analysis) ---
class AnalyzerAgent:
    """
    Analyzes all files in the downloaded dataset folder and generates
    concise Data Descriptions (d_i) for each file.
    """
    def __init__(self, llm_agent: MockLLMAgent):
        self.llm_agent = llm_agent
        
    def analyze_dataset(self, dataset_path: str) -> Dict[str, str]:
        """
        Analyzes all files in the dataset directory.
        
        Args:
            dataset_path: Path to the downloaded Kaggle dataset
            
        Returns:
            Dictionary mapping filename to data description (d_i)
        """
        print(f"\n{'='*70}")
        print("STEP 1: ANALYZER AGENT - Data File Analysis")
        print(f"{'='*70}")
        
        dataset_dir = Path(dataset_path)
        if not dataset_dir.exists():
            raise FileNotFoundError(f"Dataset directory not found: {dataset_path}")
        
        data_descriptions = {}
        
        # Find all data files (CSV, JSON, TXT, etc.)
        data_files = list(dataset_dir.glob("*.csv")) + \
                     list(dataset_dir.glob("*.json")) + \
                     list(dataset_dir.glob("*.txt")) + \
                     list(dataset_dir.glob("*.xlsx"))
        
        print(f"\nFound {len(data_files)} data file(s) to analyze")
        
        for file_path in data_files:
            print(f"\n  Analyzing: {file_path.name}")
            
            # Read file preview (first 1000 characters)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_preview = f.read(1000)
            except Exception as e:
                print(f"    Warning: Could not read file - {e}")
                continue
            
            # Generate data description using LLM
            analysis_prompt = f"""
You are the Analyzer Agent. Analyze the following data file and generate a concise 
Data Description (d_i) that includes:
1. File structure (columns, data types, format)
2. Key statistical properties (if applicable)
3. Potential use cases for hypothesis testing

File: {file_path.name}
Preview (first 1000 chars):
{file_preview}

Generate a structured Data Description in JSON format with keys:
- structure
- statistics
- use_cases
"""
            
            description = self.llm_agent.invoke(
                prompt=analysis_prompt,
                context={"file_name": file_path.name}
            )
            
            data_descriptions[file_path.name] = description
            print(f"    ✓ Description generated ({len(description)} chars)")
        
        # Print all data descriptions
        print(f"\n{'='*70}")
        print("DATA DESCRIPTIONS (d_i) - FULL OUTPUT:")
        print(f"{'='*70}")
        for filename, description in data_descriptions.items():
            print(f"\n📄 {filename}:")
            print(f"{description}\n")
        
        return data_descriptions


# --- Step 2: Planner Agent (Initial Step Generation) ---
class PlannerAgent:
    """
    Generates granular execution steps (p_k) for hypothesis testing.
    Starts with a simple initial step (p_0) and refines based on Router feedback.
    """
    def __init__(self, llm_agent: MockLLMAgent):
        self.llm_agent = llm_agent
        self.current_plan = []
        
    def generate_initial_step(
        self, 
        hypotheses: List[str], 
        data_descriptions: Dict[str, str]
    ) -> str:
        """
        Generates the initial execution step (p_0) to begin hypothesis testing.
        
        Args:
            hypotheses: List of theoretical hypotheses to test
            data_descriptions: Data descriptions from Analyzer Agent
            
        Returns:
            Initial execution step (p_0) as a string
        """
        print(f"\n{'='*70}")
        print("STEP 2: PLANNER AGENT - Initial Step Generation")
        print(f"{'='*70}")
        
        planning_prompt = f"""
You are the Planner Agent. Generate a simple, single initial execution step (p_0) 
to begin testing the first hypothesis.

Hypotheses to test:
{json.dumps(hypotheses, indent=2)}

Available data files:
{json.dumps(list(data_descriptions.keys()), indent=2)}

Generate a highly granular initial step that:
1. Focuses on loading and exploring the most relevant data file
2. Performs basic data validation
3. Sets up the foundation for hypothesis testing

Return the step as a JSON object with keys:
- step_number: 0
- description: Brief description of what this step does
- actions: List of specific actions to perform
"""
        
        initial_step = self.llm_agent.invoke(
            prompt=planning_prompt,
            context={
                "hypotheses": hypotheses,
                "data_files": list(data_descriptions.keys())
            }
        )
        
        self.current_plan.append(initial_step)
        print(f"\n✓ Initial step (p_0) generated")
        print(f"  Plan length: {len(self.current_plan)} step(s)")
        
        return initial_step
    
    def add_step(self, router_feedback: str) -> str:
        """
        Adds a new step to the plan based on Router feedback.
        
        Args:
            router_feedback: Feedback from Router Agent
            
        Returns:
            New execution step as a string
        """
        print(f"\n[PLANNER: Adding new step based on Router feedback]")
        
        planning_prompt = f"""
You are the Planner Agent. Based on the Router's feedback, generate the next 
execution step to address the identified shortcoming.

Current plan has {len(self.current_plan)} step(s).

Router feedback:
{router_feedback}

Generate the next step as a JSON object with keys:
- step_number: {len(self.current_plan)}
- description: Brief description of what this step does
- actions: List of specific actions to perform
"""
        
        new_step = self.llm_agent.invoke(
            prompt=planning_prompt,
            context={"router_feedback": router_feedback}
        )
        
        self.current_plan.append(new_step)
        print(f"  ✓ New step added (total: {len(self.current_plan)} steps)")
        
        return new_step
    
    def correct_step(self, step_index: int, router_feedback: str) -> str:
        """
        Corrects an existing step based on Router feedback.
        
        Args:
            step_index: Index of the step to correct
            router_feedback: Feedback from Router Agent
            
        Returns:
            Corrected execution step as a string
        """
        print(f"\n[PLANNER: Correcting step {step_index} based on Router feedback]")
        
        if step_index >= len(self.current_plan):
            print(f"  Warning: Step {step_index} does not exist, adding new step instead")
            return self.add_step(router_feedback)
        
        planning_prompt = f"""
You are the Planner Agent. Based on the Router's feedback, correct the existing 
execution step to address the identified issue.

Current step to correct:
{self.current_plan[step_index]}

Router feedback:
{router_feedback}

Generate the corrected step as a JSON object with keys:
- step_number: {step_index}
- description: Brief description of what this step does
- actions: List of specific actions to perform
"""
        
        corrected_step = self.llm_agent.invoke(
            prompt=planning_prompt,
            context={"router_feedback": router_feedback}
        )
        
        self.current_plan[step_index] = corrected_step
        print(f"  ✓ Step {step_index} corrected")
        
        return corrected_step
    
    def get_full_plan(self) -> str:
        """Returns the complete accumulated plan as a formatted string."""
        return "\n\n".join([f"Step {i}:\n{step}" for i, step in enumerate(self.current_plan)])


# --- Step 3: Coder Agent (Implementation) ---
class CoderAgent:
    """
    Implements the current plan (p_k) into a self-contained Python script (s_k).
    """
    def __init__(self, llm_agent: MockLLMAgent):
        self.llm_agent = llm_agent
        
    def generate_code(
        self, 
        current_step: str, 
        accumulated_plan: str,
        data_descriptions: Dict[str, str],
        previous_code: Optional[str] = None
    ) -> str:
        """
        Generates a self-contained Python script for the current step.
        
        Args:
            current_step: The current execution step to implement
            accumulated_plan: The full accumulated plan so far
            data_descriptions: Data descriptions from Analyzer Agent
            previous_code: Previous code (if correcting/extending)
            
        Returns:
            Python script (s_k) as a string
        """
        print(f"\n{'='*70}")
        print("STEP 3: CODER AGENT - Implementation")
        print(f"{'='*70}")
        
        coding_prompt = f"""
You are the Coder Agent. Implement the current execution step into a self-contained 
Python script that can be executed independently.

Current step to implement:
{current_step}

Full accumulated plan context:
{accumulated_plan}

Available data files and descriptions:
{json.dumps(data_descriptions, indent=2)}

{"Previous code (for reference/extension):" if previous_code else ""}
{previous_code if previous_code else ""}

Generate a complete, runnable Python script that:
1. Imports all necessary libraries
2. Implements the current step's actions
3. Prints intermediate results for verification
4. Handles errors gracefully
5. Saves any outputs to files (if applicable)

Return ONLY the Python code, no explanations.
"""
        
        generated_code = self.llm_agent.invoke(
            prompt=coding_prompt,
            context={
                "current_step": current_step,
                "data_files": list(data_descriptions.keys())
            }
        )
        
        print(f"\n✓ Code generated ({len(generated_code)} chars)")
        
        return generated_code


# --- Step 4: Execution & Verification Loop ---
class ExecutionEngine:
    """
    Executes generated scripts and captures results for verification.
    """
    def __init__(self, temp_dir: str):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def execute_script(self, script_code: str, iteration: int) -> Tuple[bool, str]:
        """
        Executes a Python script and captures the output.
        
        Args:
            script_code: Python code to execute
            iteration: Current iteration number (for naming)
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        print(f"\n[EXECUTION ENGINE: Running script for iteration {iteration}]")
        
        # Save script to temporary file
        script_path = self.temp_dir / f"script_iter_{iteration}.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_code)
        
        print(f"  Script saved to: {script_path}")
        
        # Execute script and capture output
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                cwd=str(self.temp_dir.parent)
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            if success:
                print(f"  ✓ Execution successful")
            else:
                print(f"  ✗ Execution failed (return code: {result.returncode})")
            
            print(f"  Output preview: {output[:200]}...")
            
            return success, output
            
        except subprocess.TimeoutExpired:
            print(f"  ✗ Execution timed out (>60s)")
            return False, "ERROR: Script execution timed out"
        except Exception as e:
            print(f"  ✗ Execution error: {e}")
            return False, f"ERROR: {str(e)}"


class VerifierAgent:
    """
    LLM-as-a-Judge: Evaluates if the current plan/code/result is sufficient
    to solve the overall hypothesis testing task.
    """
    def __init__(self, llm_agent: MockLLMAgent):
        self.llm_agent = llm_agent
        
    def evaluate_sufficiency(
        self,
        hypotheses: List[str],
        accumulated_plan: str,
        current_code: str,
        execution_result: str,
        execution_success: bool
    ) -> Tuple[str, str]:
        """
        Evaluates if the current state is sufficient to complete the task.
        
        Args:
            hypotheses: Original hypotheses to test
            accumulated_plan: Full accumulated plan
            current_code: Current generated code
            execution_result: Output from script execution
            execution_success: Whether execution was successful
            
        Returns:
            Tuple of (verdict: "SUFFICIENT" or "INSUFFICIENT", reasoning: str)
        """
        print(f"\n{'='*70}")
        print("STEP 4: VERIFIER AGENT - Sufficiency Evaluation")
        print(f"{'='*70}")
        
        verification_prompt = f"""
You are the Verifier Agent (LLM-as-a-Judge). Evaluate whether the current plan, 
code, and results are SUFFICIENT to complete the hypothesis testing task.

Original hypotheses to test:
{json.dumps(hypotheses, indent=2)}

Accumulated plan:
{accumulated_plan}

Current code:
{current_code[:1000]}...

Execution success: {execution_success}
Execution result:
{execution_result[:1000]}...

Evaluate and return a JSON object with keys:
- verdict: "SUFFICIENT" or "INSUFFICIENT"
- reasoning: Detailed explanation of your decision
- missing_elements: List of what's missing (if INSUFFICIENT)
"""
        
        evaluation = self.llm_agent.invoke(
            prompt=verification_prompt,
            context={
                "hypotheses": hypotheses,
                "execution_success": execution_success
            }
        )
        
        # Parse verdict (mock implementation - in production, parse JSON)
        verdict = "INSUFFICIENT"  # Default to continue iteration
        reasoning = evaluation
        
        # Simple keyword detection (replace with proper JSON parsing)
        if "SUFFICIENT" in evaluation.upper() and "INSUFFICIENT" not in evaluation.upper():
            verdict = "SUFFICIENT"
        
        print(f"\n  Verdict: {verdict}")
        print(f"  Reasoning preview: {reasoning[:200]}...")
        
        return verdict, reasoning


class RouterAgent:
    """
    Decides the next refinement action based on Verifier feedback.
    Options: Add Step, Correct Step, Remove Step
    """
    def __init__(self, llm_agent: MockLLMAgent):
        self.llm_agent = llm_agent
        
    def decide_action(
        self,
        verifier_reasoning: str,
        accumulated_plan: str,
        execution_success: bool
    ) -> Tuple[str, Optional[int], str]:
        """
        Decides the refinement action to take.
        
        Args:
            verifier_reasoning: Reasoning from Verifier Agent
            accumulated_plan: Current accumulated plan
            execution_success: Whether the last execution succeeded
            
        Returns:
            Tuple of (action: str, step_index: Optional[int], feedback: str)
            Actions: "ADD_STEP", "CORRECT_STEP", "REMOVE_STEP"
        """
        print(f"\n{'='*70}")
        print("STEP 4: ROUTER AGENT - Refinement Decision")
        print(f"{'='*70}")
        
        routing_prompt = f"""
You are the Router Agent. Based on the Verifier's feedback, decide the next 
refinement action to improve the plan.

Verifier reasoning:
{verifier_reasoning}

Current plan:
{accumulated_plan}

Execution success: {execution_success}

Decide the action and return a JSON object with keys:
- action: "ADD_STEP", "CORRECT_STEP", or "REMOVE_STEP"
- step_index: Index of step to correct/remove (null if ADD_STEP)
- feedback: Detailed feedback for the Planner on what to do
"""
        
        decision = self.llm_agent.invoke(
            prompt=routing_prompt,
            context={
                "verifier_reasoning": verifier_reasoning,
                "execution_success": execution_success
            }
        )
        
        # Parse decision (mock implementation - in production, parse JSON)
        action = "ADD_STEP"  # Default action
        step_index = None
        feedback = decision
        
        # Simple keyword detection (replace with proper JSON parsing)
        if "CORRECT" in decision.upper():
            action = "CORRECT_STEP"
            step_index = 0  # Mock - should parse from JSON
        elif "REMOVE" in decision.upper():
            action = "REMOVE_STEP"
            step_index = 0  # Mock - should parse from JSON
        
        print(f"\n  Action: {action}")
        if step_index is not None:
            print(f"  Target step: {step_index}")
        print(f"  Feedback preview: {feedback[:200]}...")
        
        return action, step_index, feedback


# --- Step 5: Finalyzer Agent (Output Formatting) ---
class FinalyzerAgent:
    """
    Formats the final validated code according to academic standards.
    Ensures outputs are saved in clean CSV format and charts as PNG.
    """
    def __init__(self, llm_agent: MockLLMAgent, output_dir: str):
        self.llm_agent = llm_agent
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def finalize_output(
        self,
        final_code: str,
        hypotheses: List[str],
        accumulated_plan: str
    ) -> str:
        """
        Formats the final output according to academic standards.
        
        Args:
            final_code: The final validated code
            hypotheses: Original hypotheses tested
            accumulated_plan: Full accumulated plan
            
        Returns:
            Path to the finalized output directory
        """
        print(f"\n{'='*70}")
        print("STEP 5: FINALYZER AGENT - Output Formatting")
        print(f"{'='*70}")
        
        finalization_prompt = f"""
You are the Finalyzer Agent. Format the final validated code according to 
academic standards.

Final code:
{final_code}

Hypotheses tested:
{json.dumps(hypotheses, indent=2)}

Full plan executed:
{accumulated_plan}

Generate a finalized version that:
1. Saves all results to clean CSV files
2. Saves all charts as PNG files
3. Includes a summary report in Markdown format
4. Follows academic formatting guidelines

Return the enhanced final code with proper output formatting.
"""
        
        finalized_code = self.llm_agent.invoke(
            prompt=finalization_prompt,
            context={"hypotheses": hypotheses}
        )
        
        # Save finalized code
        final_script_path = self.output_dir / "final_analysis.py"
        with open(final_script_path, 'w', encoding='utf-8') as f:
            f.write(finalized_code)
        
        print(f"\n✓ Finalized code saved to: {final_script_path}")
        print(f"✓ Output directory: {self.output_dir}")
        
        return str(self.output_dir)


# --- Main DS-STAR Orchestrator ---
class DSStarOrchestrator:
    """
    Main orchestrator for the DS-STAR 5-step iterative refinement pipeline.
    """
    def __init__(
        self,
        hypotheses: List[str],
        dataset_name: str,
        max_iterations: int = MAX_ITERATIONS
    ):
        self.hypotheses = hypotheses
        self.dataset_name = dataset_name
        self.max_iterations = max_iterations
        
        # Initialize agents (replace MockLLMAgent with actual LLM API)
        self.analyzer = AnalyzerAgent(MockLLMAgent("Analyzer", "Data Analysis"))
        self.planner = PlannerAgent(MockLLMAgent("Planner", "Step Planning"))
        self.coder = CoderAgent(MockLLMAgent("Coder", "Code Generation"))
        self.verifier = VerifierAgent(MockLLMAgent("Verifier", "LLM-as-a-Judge"))
        self.router = RouterAgent(MockLLMAgent("Router", "Refinement Routing"))
        self.finalyzer = FinalyzerAgent(MockLLMAgent("Finalyzer", "Output Formatting"), OUTPUT_DIR)
        
        self.execution_engine = ExecutionEngine(TEMP_SCRIPT_DIR)
        
    def run(self) -> bool:
        """
        Executes the full DS-STAR pipeline.
        
        Returns:
            True if hypothesis testing completed successfully, False otherwise
        """
        print(f"\n{'='*70}")
        print("DS-STAR EXECUTION ENGINE - STARTING")
        print(f"{'='*70}")
        print(f"Hypotheses: {len(self.hypotheses)}")
        print(f"Dataset: {self.dataset_name}")
        print(f"Max iterations: {self.max_iterations}")
        
        # Step 1: Analyze dataset
        dataset_path = os.path.join(KAGGLE_DATASET_DIR, self.dataset_name)
        data_descriptions = self.analyzer.analyze_dataset(dataset_path)
        
        # Step 2: Generate initial plan
        current_step = self.planner.generate_initial_step(self.hypotheses, data_descriptions)
        
        # Steps 3-4: Iterative refinement loop
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n{'='*70}")
            print(f"ITERATION {iteration}/{self.max_iterations}")
            print(f"{'='*70}")
            
            # Step 3: Generate code
            accumulated_plan = self.planner.get_full_plan()
            current_code = self.coder.generate_code(
                current_step=current_step,
                accumulated_plan=accumulated_plan,
                data_descriptions=data_descriptions
            )
            
            # Execute code
            execution_success, execution_result = self.execution_engine.execute_script(
                current_code, iteration
            )
            
            # Step 4a: Verify sufficiency
            verdict, reasoning = self.verifier.evaluate_sufficiency(
                hypotheses=self.hypotheses,
                accumulated_plan=accumulated_plan,
                current_code=current_code,
                execution_result=execution_result,
                execution_success=execution_success
            )
            
            # Check if sufficient
            if verdict == "SUFFICIENT":
                print(f"\n{'='*70}")
                print("🎉 VERIFICATION PASSED - Plan is SUFFICIENT")
                print(f"{'='*70}")
                
                # Step 5: Finalize output
                output_path = self.finalyzer.finalize_output(
                    final_code=current_code,
                    hypotheses=self.hypotheses,
                    accumulated_plan=accumulated_plan
                )
                
                print(f"\n{'='*70}")
                print(f"✓ DS-STAR EXECUTION COMPLETE")
                print(f"  Final output: {output_path}")
                print(f"  Total iterations: {iteration}")
                print(f"{'='*70}")
                
                return True
            
            # Step 4b: Route refinement
            action, step_index, feedback = self.router.decide_action(
                verifier_reasoning=reasoning,
                accumulated_plan=accumulated_plan,
                execution_success=execution_success
            )
            
            # Apply refinement action
            if action == "ADD_STEP":
                current_step = self.planner.add_step(feedback)
            elif action == "CORRECT_STEP":
                current_step = self.planner.correct_step(step_index or 0, feedback)
            elif action == "REMOVE_STEP":
                # Not implemented in this version - would require plan management
                print(f"  Warning: REMOVE_STEP not implemented, adding step instead")
                current_step = self.planner.add_step(feedback)
        
        # Max iterations reached
        print(f"\n{'='*70}")
        print(f"🛑 MAX ITERATIONS REACHED ({self.max_iterations})")
        print(f"{'='*70}")
        print(f"  Hypothesis testing incomplete")
        print(f"  Final plan had {len(self.planner.current_plan)} steps")
        print(f"{'='*70}")
        
        return False


# --- Example Usage ---
def main():
    """
    Demonstrates the DS-STAR execution engine with example hypotheses.
    """
    print("\n" + "="*70)
    print("DS-STAR EXECUTION ENGINE - DEMONSTRATION")
    print("="*70)
    
    # Example hypotheses
    hypotheses = [
        "H1: User engagement increases with personalized content recommendations",
        "H2: Churn rate is negatively correlated with feature adoption rate",
        "H3: Premium users have 2x higher retention than free users"
    ]
    
    # Example Kaggle dataset name
    dataset_name = "user-behavior-analytics"
    
    # Initialize and run DS-STAR
    orchestrator = DSStarOrchestrator(
        hypotheses=hypotheses,
        dataset_name=dataset_name,
        max_iterations=15
    )
    
    success = orchestrator.run()
    
    print(f"\n{'='*70}")
    print(f"FINAL RESULT: {'SUCCESS' if success else 'INCOMPLETE'}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
