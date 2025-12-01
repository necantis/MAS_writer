# Video Script: Autonomous Scientific Discovery Agent (ASDA)

**Duration**: ~3 Minutes
**Goal**: Demonstrate innovation, architecture, and value to maximize Capstone scoring.

---

## 0:00 - 0:45 | The Problem: Cognitive Overload & The Trust Paradox

**(Visual: Split screen. Left side shows a stressed journalist overwhelmed by 50 open tabs and raw AI data dumps. Right side shows a clean, calm interface.)**

**Narrator**: 
"In high-pressure fields like journalism and research, AI is often deployed as a firehose of information. But for modern knowledge workers, the problem isn't information scarcity—it's **Cognitive Overload**. 

When AI acts as a passive data dump, humans are forced to constantly switch between working and monitoring the AI. This friction creates a 'Trust Paradox' where users reject AI assistance even when it's accurate, simply because it's too mentally taxing to verify.

We asked: How can we transform AI from a noisy assistant into a **Collaborative Partner** that reduces cognitive load while ensuring absolute content integrity?"

---

## 0:45 - 1:30 | The Solution: Collaborative Agent Flywheel

**(Visual: Animated diagram showing the 3-agent loop. Icons for Author, Reviewer, and Meta-Reviewer.)**

**Narrator**:
"Introducing the **Autonomous Scientific Discovery Agent (ASDA)**. Unlike standard chatbots, ASDA is a **Level 3 Multi-Agent System** designed for 'Calm Collaboration'.

Instead of a single 'black box' model, we implemented a rigorous **Iterative Refinement Loop** with three specialized agents:

1.  **The Author Agent**: Drafts the initial content using verified sources.
2.  **The Reviewer Agent**: Acts as an 'LLM-as-a-Judge', auditing the draft against strict policies like the Toulmin Argument Structure and Financial Reality Checks.
3.  **The Meta-Reviewer Agent**: The strategist. It doesn't just fix errors; it refines the *prompt* itself to guide the Author in the next iteration."

**(Visual: Highlight the "Meta-Reviewer" node pulsing and sending a signal back to the "Author" node.)**

**Narrator**:
"This feedback loop ensures that every final article is not just 'generated', but **audited, verified, and strategically refined** before you ever see it."

---

## 1:30 - 2:15 | The Demo: Live Execution

**(Visual: Screen recording of the `live_agent_orchestrator.py` console output running in real-time. Speed up the waiting times.)**

**Narrator**:
"Let's see it in action. We task ASDA with generating a complex Capstone Project on 'Sensor-Based Supply Chain Efficiency'.

**(Visual: Zoom in on Iteration 1 console output showing the 'Audit Failed' message.)**

**Narrator**:
"In Iteration 1, the Author creates a draft. But look—the Reviewer Agent flags a critical issue: the 'Financial Model' lacks evidence-based ROI calculations. The system **rejects** this draft automatically.

**(Visual: Zoom in on Meta-Reviewer output generating a new prompt.)**

**Narrator**:
"The Meta-Reviewer analyzes this failure and constructs a precise new prompt for the Author.

**(Visual: Zoom in on Iteration 2 'SUCCESS' message and the final markdown document.)**

**Narrator**:
"In Iteration 2, the Author corrects the mistake. The Reviewer validates the fix, confirming the 'Previous Kill List' is addressed. The system converges, delivering a production-ready document with a complete Lean Plan Table and verified financial models."

---

## 2:15 - 3:00 | The Build & Conclusion

**(Visual: Quick montage of the code: `live_agent_orchestrator.py`, `prompts.py`, and the `.env` file.)**

**Narrator**:
"We built ASDA using **Python** and the **Gemini 1.5 Flash API** for high-speed, cost-effective reasoning. 

The architecture relies on:
*   **State Management**: Passing the 'Kill List' context between iterations.
*   **Observability**: Detailed logging of every decision phase.
*   **Robustness**: Custom retry logic and error handling for API resilience.

ASDA proves that by separating concerns into specialized agents, we can build AI systems that don't just generate text, but actually **collaborate** to uphold the highest standards of truth and quality."

**(Visual: Project Title Card with GitHub Repository Link)**

**Narrator**:
"Thank you."
