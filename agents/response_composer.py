import re
from typing import Any

WHY_THIS_FRAMEWORK_MAP = {
    "ECG KISS": "The ECG KISS framework provides a structured lens to evaluate your core end goals, isolate your immediate constraints, and simulate options before committing resources.",
    "SLR CAMERAS": "The SLR CAMERAS framework helps accelerate customer acquisition, launching product-market tests quickly, and structuring repeat loops to maximize retention.",
    "MC BEERS": "The MC BEERS framework breaks down yearly plans into concrete quarterly objectives, defining target metrics, and tracking team execution progress.",
    "PC PEERS": "The PC PEERS framework is designed for monthly strategic reviews, optimizing operational routines, and maintaining growth momentum.",
    "PS ERP": "The PS ERP framework structures weekly sprints, assigning clear ownership of tasks, and organizing resource allocation.",
    "DC ERPRS": "The DC ERPRS framework guides daily execution standups, tracking progress metrics, and immediately identifying project roadblocks.",
    "OKS REC SME": "The OKS REC SME framework is suited for designing high-level business systems, clarifying operational modules, and defining team roles.",
    "PFA SAAS SME": "The PFA SAAS SME framework maps internal business processes, streamlining handoffs, and identifying efficiency bottlenecks.",
    "RSS FEED SME": "The RSS FEED SME framework outlines standard operating procedures (SOPs), defining instructions, and standardizing task delivery.",
    "RPM REAP ER": "The RPM REAP ER framework manages execution pushback, aligning team incentives, and overcoming operational inertia.",
    "RUN DCMS ER": "The RUN DCMS ER framework focuses resources on revenue-generating actions, optimizing sales campaigns, and maximizing margins.",
    "ERM FABS ER": "The ERM FABS ER framework provides performance metrics, reviewing execution outcomes, and adjusting strategic milestones.",
    "ADMINS ER": "The ADMINS ER framework establishes crisis protocols, resolving administrative bottlenecks, and securing critical business assets."
}

QUESTIONS_MAP = {
    "ECG KISS": [
        "1. How can we define the primary metric for the End Goal (E)?",
        "2. What are the key variables to track during the Simulation (S) phase?"
    ],
    "SLR CAMERAS": [
        "1. What is the most cost-effective channel to Launch (L) our test ads?",
        "2. How do we set up the first Repeat (R) email loop for past buyers?"
    ],
    "MC BEERS": [
        "1. How do we divide our annual targets into Quarterly (Q) milestones?",
        "2. What metrics should we use to measure Execution (E) velocity?"
    ],
    "PC PEERS": [
        "1. What is the biggest operational bottleneck in our monthly routine?",
        "2. How do we calculate and review our monthly growth rate?"
    ],
    "PS ERP": [
        "1. How do we scope weekly sprint tasks to prevent rollover?",
        "2. Who should own the core sprint tracking metrics?"
    ],
    "DC ERPRS": [
        "1. How can we keep daily standups under 15 minutes?",
        "2. What format should we use to flag execution blockers daily?"
    ],
    "OKS REC SME": [
        "1. How do we map our current team structure to the system modules?",
        "2. What are the key responsibilities for the core operational roles?"
    ],
    "PFA SAAS SME": [
        "1. Which business process has the highest turnaround time today?",
        "2. How do we document handoffs between marketing and sales?"
    ],
    "RSS FEED SME": [
        "1. What format makes SOPs easiest for new hires to follow?",
        "2. How often should we audit and update our active checklists?"
    ],
    "RPM REAP ER": [
        "1. What is the main source of team resistance to new procedures?",
        "2. How do we design an incentive structure that rewards execution?"
    ],
    "RUN DCMS ER": [
        "1. Which marketing activities drive 80% of our current revenue?",
        "2. How do we calculate and optimize our customer acquisition margins?"
    ],
    "ERM FABS ER": [
        "1. What are the primary KPIs for evaluating our current strategy?",
        "2. How often should we run formal performance reviews?"
    ],
    "ADMINS ER": [
        "1. What are the critical risks we need to cover in our crisis protocol?",
        "2. How do we set up emergency backups for administrative credentials?"
    ]
}

class ResponseComposer:
    def __init__(self, llm: Any = None):
        self.llm = llm

    def run(self, framework_name: str, strategy: dict, execution: dict) -> str:
        # Extract raw sections
        raw_scenario = strategy.get('scenario', '').strip()
        raw_applied = strategy.get('applied_sections', '').strip()
        raw_dreamer = strategy.get('dreamer', '').strip()
        raw_guardian = strategy.get('guardian', '').strip()
        
        raw_recommendation = execution.get('recommendation', '').strip()
        raw_priority = execution.get('priority_action', '').strip()
        raw_athlete = execution.get('athlete', '').strip()

        # 1. Framework Selected
        why_fw = WHY_THIS_FRAMEWORK_MAP.get(
            framework_name, 
            f"The {framework_name} framework is the optimal playbook methodology to analyze and systematically resolve this operational challenge."
        )
        fw_selected = f"{framework_name}\n- {why_fw}"

        # 2. Executive Summary
        # Cap to approx 120 words
        words = raw_scenario.split()
        if len(words) > 120:
            exec_summary = " ".join(words[:120]) + "..."
        else:
            exec_summary = raw_scenario

        # 3. Framework Analysis
        fw_analysis = raw_applied

        # 4. Recommendation
        recommendation = raw_recommendation

        # 5. Priority Actions
        priority_actions = raw_priority

        # 6. Next 24 Hours
        next_24_hours = raw_athlete

        # 7. Risks and Missing Information
        risks_missing = raw_guardian

        # 8. Suggested Follow-up Questions
        questions = QUESTIONS_MAP.get(
            framework_name,
            [
                "1. What are the key metrics to track for this framework?",
                "2. How do we roll out the priority actions to the team?"
            ]
        )
        suggested_questions = "\n".join(questions)

        # Assemble into the 8-part contract
        template = f"""## 1. Framework Selected
{fw_selected}

## 2. Executive Summary
{exec_summary}

## 3. Framework Analysis
{fw_analysis}

## 4. Recommendation
{recommendation}

## 5. Priority Actions
{priority_actions}

## 6. Next 24 Hours
{next_24_hours}

## 7. Risks and Missing Information
{risks_missing}

## 8. Suggested Follow-up Questions
{suggested_questions}"""

        return template
