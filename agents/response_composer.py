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
        "2. What are the key variables to track during the Simulation (S) phase?",
        "3. How do we distinguish core Pain Points (C) from surface symptoms?"
    ],
    "SLR CAMERAS": [
        "1. What is the most cost-effective channel to Launch (L) our test ads?",
        "2. How do we set up the first Repeat (R) email loop for past buyers?",
        "3. Which specific customer segment should we Select (S) as our niche?"
    ],
    "MC BEERS": [
        "1. How do we divide our annual targets into Quarterly (Q) milestones?",
        "2. What metrics should we use to measure Execution (E) velocity?",
        "3. How can we align team members behind these new indicators?"
    ],
    "PC PEERS": [
        "1. What is the biggest operational bottleneck in our monthly routine?",
        "2. How do we calculate and review our monthly growth rate?",
        "3. How do we keep team members aligned during rapid monthly shifts?"
    ],
    "PS ERP": [
        "1. How do we scope weekly sprint tasks to prevent rollover?",
        "2. Who should own the core sprint tracking metrics?",
        "3. How do we resolve resource bottlenecks mid-sprint?"
    ],
    "DC ERPRS": [
        "1. How can we keep daily standups under 15 minutes?",
        "2. What format should we use to flag execution blockers daily?",
        "3. How do we log and resolve daily performance gaps?"
    ],
    "OKS REC SME": [
        "1. How do we map our current team structure to the system modules?",
        "2. What are the key responsibilities for the core operational roles?",
        "3. How do we design standard interfaces between different team roles?"
    ],
    "PFA SAAS SME": [
        "1. Which business process has the highest turnaround time today?",
        "2. How do we document handoffs between marketing and sales?",
        "3. What tools can we use to automate repeat manual tasks?"
    ],
    "RSS FEED SME": [
        "1. What format makes SOPs easiest for new hires to follow?",
        "2. How often should we audit and update our active checklists?",
        "3. Where is the best centralized location to store team procedures?"
    ],
    "RPM REAP ER": [
        "1. What is the main source of team resistance to new procedures?",
        "2. How do we design an incentive structure that rewards execution?",
        "3. How do we rebuild momentum after a failed initiative?"
    ],
    "RUN DCMS ER": [
        "1. Which marketing activities drive 80% of our current revenue?",
        "2. How do we calculate and optimize our customer acquisition margins?",
        "3. What is the fastest campaign we can launch to boost cash flow?"
    ],
    "ERM FABS ER": [
        "1. What are the primary KPIs for evaluating our current strategy?",
        "2. How often should we run formal performance reviews?",
        "3. How do we translate performance insights into next planning cycles?"
    ],
    "ADMINS ER": [
        "1. What are the critical risks we need to cover in our crisis protocol?",
        "2. How do we set up emergency backups for administrative credentials?",
        "3. Who is the primary point of contact for resolving blockers?"
    ]
}

class ResponseComposer:
    def __init__(self, llm: Any = None):
        self.llm = llm

    def run(self, framework_name: str, strategy: dict, execution: dict) -> str:
        # Extract raw sections
        raw_scenario = strategy.get('scenario', '').strip()
        raw_applied = strategy.get('applied_sections', '').strip()
        raw_priority = execution.get('priority_action', '').strip()
        raw_dreamer = strategy.get('dreamer', '').strip()
        raw_guardian = strategy.get('guardian', '').strip()
        raw_athlete = execution.get('athlete', '').strip()

        # 1. Framework Selected
        fw_selected = framework_name

        # 2. Executive Summary
        exec_summary = raw_scenario

        # 3. Why This Framework
        why_fw = WHY_THIS_FRAMEWORK_MAP.get(
            framework_name, 
            f"The {framework_name} framework is selected because it is the optimal playbook methodology to analyze and systematically resolve this operational challenge."
        )

        # 4. Framework Analysis
        fw_analysis = raw_applied

        # 5. Strategic Recommendation
        strat_recommendation = f"Leverage growth opportunities (Dreamer perspective):\n{raw_dreamer}\n\nEstablish operational safeguards (Guardian perspective):\n{raw_guardian}"

        # 6. Priority Actions
        priority_actions = raw_priority

        # 7. Your Next 24 Hours
        # Extract the first bullet/number item from Athlete plan
        athlete_lines = [line.strip() for line in raw_athlete.split("\n") if line.strip()]
        first_step = "Identify the primary bottleneck in your business operations and block 1 hour tomorrow to address it."
        for line in athlete_lines:
            match = re.match(r'^(?:\d+\.|\-|\*)\s*(.+)', line)
            if match:
                first_step = match.group(1).strip()
                break
        next_24_hours = f"Complete the first critical step of your execution plan: {first_step}"

        # 8. Risks and Watchouts
        # Format the Guardian guidelines as operational risks
        guardian_lines = [line.strip() for line in raw_guardian.split("\n") if line.strip()]
        risks_list = []
        for line in guardian_lines:
            match = re.match(r'^(?:\d+\.|\-|\*)\s*(.+)', line)
            if match:
                risks_list.append(match.group(1).strip())
        
        if len(risks_list) >= 2:
            risks_watchouts = f"### Operational Risk 1: Plan Divergence\n{risks_list[0]}\n\n### Operational Risk 2: Strategy Drift\n{risks_list[1]}"
        elif len(risks_list) == 1:
            risks_watchouts = f"### Operational Risk 1: Plan Divergence\n{risks_list[0]}\n\n### Operational Risk 2: Lack of operational safeguards."
        else:
            risks_watchouts = "### Operational Risk 1: Plan Divergence\nEnsure tight alignment of metrics and prevent scope creep.\n\n### Operational Risk 2: System Complexity\nAvoid building overly complex workflows before validating baseline assumptions."

        # 9. Suggested Follow-Up Questions
        questions = QUESTIONS_MAP.get(
            framework_name,
            [
                f"1. What are the key metrics to track for {framework_name}?",
                f"2. How do we roll out the priority actions to the team?",
                f"3. What is the fallback plan if we encounter execution friction?"
            ]
        )
        suggested_questions = "\n".join(questions)

        # Assemble into the 9-part contract
        template = f"""## 1. Framework Selected
{fw_selected}

## 2. Executive Summary
{exec_summary}

## 3. Why This Framework
{why_fw}

## 4. Framework Analysis
{fw_analysis}

## 5. Strategic Recommendation
{strat_recommendation}

## 6. Priority Actions
{priority_actions}

## 7. Your Next 24 Hours
{next_24_hours}

## 8. Risks and Watchouts
{risks_watchouts}

## 9. Suggested Follow-Up Questions
{suggested_questions}"""

        return template
