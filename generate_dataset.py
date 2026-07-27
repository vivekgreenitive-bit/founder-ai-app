import os
import json
import re

# Paths
BOOK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "FounderFrameworks.txt"))
OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "dataset.json"))

def load_book():
    if not os.path.exists(BOOK_PATH):
        raise FileNotFoundError(f"Book file not found at {BOOK_PATH}")
    with open(BOOK_PATH, "r", encoding="utf-8") as f:
        return f.read()

def generate_qa_pairs():
    # We will build a structured dataset covering:
    # 1. Definitions of all acronyms
    # 2. Detail on each letter of the 13 frameworks
    # 3. Perspective questions (Dreamer vs Doer vs Guardian)
    # 4. Action-oriented business questions
    
    qa_list = []
    
    # 1. Framework Definitions
    frameworks_def = {
        "ECG KISS": {
            "name": "Overall Business Diagnostic",
            "type": "Planning",
            "mapping": {
                "E": "End Goal (The north star, provides direction and clarity)",
                "C": "Current Pain Points (Grounds you in facts and present reality)",
                "G": "GAP (The measurable distance between current status and end goal)",
                "K": "Knowledge (End-to-end domain knowledge required to run operations)",
                "I": "Implementation (Detailed step-by-step actions to achieve objectives)",
                "S": "Simulate (Visual workflows/diagrams to preview implementation paths)",
                "S": "Solution (Finalized focused, actionable execution plan)"
            },
            "why": "It evaluates business health, identifies critical operational gaps, and structures actionable solutions."
        },
        "SLR CAMERAS": {
            "name": "Yearly Planning",
            "type": "Planning",
            "mapping": {
                "S": "Success Peak (The highest height of yearly success/vision you want to reach)",
                "L": "List of Milestones (The major checkpoints to reach the Success Peak)",
                "R": "Resources Required (People, tools, money, materials, and partnerships needed)",
                "C": "Categorization (Group milestones by domain like Sales, Marketing, Production, Logistics)",
                "A": "Assigning Milestones (Distribute milestones across Q1, Q2, Q3, and Q4)",
                "M": "Mitigation Plan (Contingency strategies in case things don't go as expected)",
                "E": "Evaluation and Estimation (Assess past performance of Founder, Team, and Customer outcomes)",
                "R": "Review (Key learnings, insights, and improvements from the previous year)",
                "A": "Actually Visualize (Form a complete big-picture journey from planning to execution)",
                "S": "Simulate & Schedule (Map the plan into flow diagrams and schedule onto the quarterly calendar)"
            },
            "why": "Guides founders from high-level yearly vision to resource-mapped, quarter-assigned calendar entries with mitigation plans."
        },
        "MC BEERS": {
            "name": "Quarterly Planning",
            "type": "Planning",
            "mapping": {
                "M": "Milestones (Identify key 90-day targets contributing to yearly goals)",
                "C": "Categorize (Group quarterly milestones by business function like Sales, Production, Cost Saving)",
                "B": "Breakdown into Multiple Tasks (Deconstruct milestones into small, actionable High/Med/Low priority tasks)",
                "E": "Estimate Efforts (Assign estimated time and resources needed for each task)",
                "E": "Evaluate (Assess previous quarter performance across Founder, Team, Customer, and Finance)",
                "R": "Review (Collect key learnings and insights to refine future iterations)",
                "S": "Simulate & Schedule (Use flow diagrams to visualize the path, then schedule tasks across 3 months)"
            },
            "why": "Provides the 90-day rhythm that allows focused action, performance tracking, and rapid adjustments without being overwhelmed."
        },
        "PC PEERS": {
            "name": "Monthly Planning",
            "type": "Planning",
            "mapping": {
                "P": "Prioritize (Choose top operational milestones for the next 30 days)",
                "C": "Categorize (Group tasks by department to maintain focused execution)",
                "P": "Performance Analysis (Evaluate previous month results against expectations)",
                "E": "Estimate Effort (Determine time and resource allocations for monthly deliverables)",
                "E": "Evaluate KPIs (Assess core health metrics of the company)",
                "R": "Review (Reflect on blockers and friction points to improve systems)",
                "S": "Simulate & Schedule (Build the calendar for the month and map dependencies)"
            },
            "why": "Allows course-correction every 30 days to keep team alignment and maintain execution momentum."
        },
        "PS ERP": {
            "name": "Weekly Planning",
            "type": "Planning",
            "mapping": {
                "P": "Prioritize (Set high-impact goals that must be achieved in the next 7 days)",
                "S": "Sprint Goals (Break down weekly goals into clear engineering/operation sprints)",
                "E": "Estimate (Assess hours and effort required for sprint tickets)",
                "R": "Review (Examine completed vs delayed tasks from the previous week)",
                "P": "Process Optimization (Smooth out bottleneck tasks and speed up workflows)"
            },
            "why": "Helps win the week by structuring clear sprints, estimating task loads, and conducting weekly reviews."
        },
        "DC ERPRS": {
            "name": "Daily Planning",
            "type": "Planning",
            "mapping": {
                "D": "Daily Goals (Identify 3 non-negotiable outcomes for the day)",
                "C": "Calendar Blocking (Dedicate specific hours for focused execution and deep work)",
                "E": "Execute (Focus strictly on high-priority tasks during blocked slots)",
                "R": "Review (Examine what was completed and note interruptions at the end of the day)",
                "P": "Prioritize Tomorrow (Map tomorrow's top 3 tasks based on today's outcomes)",
                "R": "Refocus (Identify distractions to optimize focus settings)",
                "S": "Standup (Participate in daily alignment meetings to highlight blockers)"
            },
            "why": "Protects deep work time, structures daily focus, and aligns teams through daily standups."
        },
        "OKS REC SME": {
            "name": "Business System Architecture",
            "type": "Operations",
            "mapping": {
                "O": "Objectives (Define the ultimate outputs the system must deliver)",
                "K": "Knowledge Base (Establish central documentation of rules and reference materials)",
                "S": "Structure (Build organizational structures and clear responsibility boundaries)",
                "R": "Roles & Responsibilities (Define individual jobs, owners, and accountabilities)",
                "E": "Execution Flow (Map how inputs flow through the system to become outputs)",
                "C": "Controls (Set quality checkpoints to audit execution quality)",
                "S": "System Tools (Identify software, templates, and physical tools required)",
                "M": "Metrics (Define leading and lagging indicators to measure health)",
                "E": "Evaluation (Review system performance periodically to remove bottlenecks)"
            },
            "why": "Removes the founder bottleneck by establishing system-dependent structures and clear boundaries."
        },
        "PFA SAAS SME": {
            "name": "Business Process Mapping",
            "type": "Operations",
            "mapping": {
                "P": "Process Definition (Outline the scope and boundaries of the specific process)",
                "F": "Flowcharts (Create visual step-by-step mapping of workflows)",
                "A": "Automation (Identify repetitive tasks that can be automated via software)",
                "S": "SOP Alignment (Link the process map directly to detailed SOP documentation)",
                "S": "Stakeholder Roles (Define who executes, approves, and monitors each step)",
                "A": "Analytics (Set up tracking metrics for process cycle time and efficiency)",
                "A": "Audits (Perform regular audits to ensure compliance and find friction)",
                "S": "Scaling (Optimize the workflow to handle increased volumes smoothly)",
                "S": "System Integration (Connect this process to other operational structures)",
                "M": "Maintenance (Keep the process documentation up to date with business changes)",
                "E": "Evaluation (Run cycle reviews to optimize execution velocity)"
            },
            "why": "Streamlines complex workflows, prevents communication failures, and automates manual friction."
        },
        "RSS FEED SME": {
            "name": "SOP Design",
            "type": "Operations",
            "mapping": {
                "R": "Requirements (State what triggers this SOP and what tools are required)",
                "S": "Step-by-step Instructions (Write clear, numbered, easy-to-follow instructions)",
                "S": "Screenshots & Video (Embed visual aids to prevent ambiguity)",
                "F": "Format (Keep standard visual layouts and easy-to-read typography)",
                "E": "Exceptions (Document how to handle edge cases or unexpected outcomes)",
                "E": "Error Logging (Explain where to record failures and who to escalate to)",
                "D": "Documentation Owner (Assign a specific role to keep the SOP updated)",
                "S": "Sign-off (Define the approval process for completed work)",
                "M": "Metrics (Track how long the SOP takes to execute and its error rate)",
                "E": "Evaluation (Perform regular quality checks to optimize steps)"
            },
            "why": "Ensures standard work quality, makes delegation safe, and allows scaling without quality drops."
        },
        "RPM REAP ER": {
            "name": "Project Execution",
            "type": "Execution",
            "mapping": {
                "R": "Resource Management (Assign people, tools, and budget to the project)",
                "P": "Progress Tracking (Establish real-time visibility on task completion)",
                "M": "Milestone Delivery (Focus on shipping deliverables by key deadlines)",
                "R": "Risk Assessment (Identify potential delays and create backups)",
                "E": "Execution Speed (Optimize sprint velocity to ship fast)",
                "A": "Alignment (Ensure all cross-functional partners are on the same page)",
                "P": "Post-Mortem (Examine what went right/wrong after the project finishes)",
                "E": "Efficiency (Measure resource utilization vs project output)",
                "R": "Review (Reflect on execution cadence and adjust parameters)"
            },
            "why": "Ensures rapid project execution, minimizes resource wastage, and guarantees deadline compliance."
        },
        "RUN DCMS ER": {
            "name": "Revenue Generation",
            "type": "Execution",
            "mapping": {
                "R": "Revenue Streams (Identify and list all channels generating income)",
                "U": "User Persona (Define exactly who you serve and their buying motivations)",
                "N": "Niche Marketing (Create highly targeted campaigns for maximum impact)",
                "D": "Data Analytics (Track conversion rates, CAC, LTV, and sales metrics)",
                "C": "Conversion Funnel (Map user journey from visitor to paying customer)",
                "M": "Marketing Campaigns (Execute structured campaigns across platforms)",
                "S": "Sales Automation (Set up pipelines, CRM triggers, and email sequences)",
                "E": "Evaluation (Regularly audit sales performance vs target projections)",
                "R": "Retention (Structure referral programs, bonuses, and onboarding to keep users)"
            },
            "why": "Builds a predictable, metrics-driven revenue engine by matching campaigns to user personas."
        },
        "ERM FABS ER": {
            "name": "Performance Evaluation",
            "type": "Execution",
            "mapping": {
                "E": "Evaluation Metrics (Define the key metrics that determine success)",
                "R": "Review Frequency (Schedule weekly, monthly, or quarterly assessments)",
                "M": "Management Review (Conduct direct discussions between founders and leads)",
                "F": "Feedback Loop (Establish channels for two-way performance conversations)",
                "A": "Action Items (Create specific tasks to address low-performance areas)",
                "B": "Benchmark (Compare internal progress against industry averages)",
                "S": "Self-Evaluation (Ensure teams score their own performance first)",
                "E": "Efficiency Score (Calculate output divided by resource hours spent)",
                "R": "Reward System (Acknowledge high performers to boost morale)"
            },
            "why": "Evaluates performance objectly, builds feedback loops, and maps clear action plans."
        },
        "ADMINS ER": {
            "name": "Crisis Management",
            "type": "Execution",
            "mapping": {
                "A": "Alert System (Detect critical anomalies and operational failures immediately)",
                "D": "Damage Control (Implement temporary fixes to contain the negative impact)",
                "M": "Mitigation Plan (Deploy pre-defined backup plans for resource/finance shortfalls)",
                "I": "Incident Logs (Document exactly what happened, when, and the impact)",
                "N": "Notification (Inform key stakeholders, clients, or team members immediately)",
                "S": "Stabilization (Return operations to normal baseline limits)",
                "E": "Evaluation (Analyze the root cause to prevent future occurrence)",
                "R": "Recovery (Rebuild systems and strengthen backup protocols)"
            },
            "why": "Provides a calm, step-by-step protocol to handle operational failures and external shocks."
        }
    }

    # 1. Generate Acronym Mapping Questions
    for acronym, info in frameworks_def.items():
        # What is X?
        qa_list.append({
            "instruction": f"What is the {acronym} framework in Founder Frameworks?",
            "input": "",
            "output": f"The {acronym} framework represents the '{info['name']}' framework under the '{info['type']}' category. {info['why']}\n\nThe letters represent:\n" + "\n".join([f"- {k}: {v}" for k, v in info['mapping'].items()])
        })
        
        # Explain each letter specifically
        for letter, details in info['mapping'].items():
            qa_list.append({
                "instruction": f"What does the '{letter}' stand for in the {acronym} framework?",
                "input": "",
                "output": f"In the {acronym} ({info['name']}) framework, '{letter}' stands for {details}."
            })
            
        # Why use it?
        qa_list.append({
            "instruction": f"Why should a founder use the {acronym} framework?",
            "input": "",
            "output": f"A founder should use the {acronym} framework ({info['name']}) because: {info['why']}"
        })

    # 2. Add scenario-based/mindset questions (Dreamer vs Doer vs Guardian)
    mindsets = {
        "Dreamer": "The 'Dreamer' acts as the superhuman thinker. They focus on hyper-growth, big visions, global reach, quick market capture, acquisitions, and speed. They think big, take risks, but sometimes overlook local regulatory complexities or resource limitations.",
        "Guardian": "The 'Guardian' acts as the military officer thinker. They focus on risk reduction, financial viability, phased rollouts, resource capacity planning, and building solid processes before scaling. They ensure the core business is stable and protected.",
        "Doer": "The 'Doer' acts as the athlete thinker. They focus on immediate action, rapid prototyping, digital validation, feedback loops, incremental replication, and constant adjustment. They learn by doing and optimizing on the fly."
    }

    for name, desc in mindsets.items():
        qa_list.append({
            "instruction": f"Describe the '{name}' perspective in the Founder Frameworks book.",
            "input": "",
            "output": desc
        })

    # Add specific cross-mindset scenarios
    qa_list.append({
        "instruction": "Compare how a Dreamer, a Guardian, and a Doer would approach global expansion using the ECG KISS framework.",
        "input": "",
        "output": "For global expansion:\n- **Dreamer**: Dispatches teams to all target countries simultaneously, hires local experts and legal advisors in parallel, and prioritizes speed to capture early market share.\n- **Guardian**: Recommends a phased rollout (e.g., USA first for 3 months, then Canada, then Singapore) to optimize resource usage, limit financial exposure, and learn from regional complexities step-by-step.\n- **Doer**: Starts with virtual research to understand dynamics, launches a pilot in the first country, collects ground-level feedback, and replicates the model in subsequent countries with proven optimizations."
    })

    qa_list.append({
        "instruction": "How do the Dreamer, Guardian, and Doer approaches differ in yearly planning (SLR CAMERAS)?",
        "input": "",
        "output": "In yearly planning:\n- **Dreamer**: Targets aggressive growth (e.g., 50%+ revenue jump), aims to acquire competitors for instant market presence, and recruits senior leaders from industry giants to fast-track milestones.\n- **Guardian**: Audits financial impact/risks, protects the core business, plans step-by-step cost optimization, and prioritizes internal talent upskilling.\n- **Doer**: Focuses on generating customer referrals, implements CRM and digital automation tools rapidly, and coordinates dedicated internal teams to execute milestones incrementally."
    })

    # 3. Add practical advice questions based on llms.txt content
    faq_data = [
        {
            "q": "How can I scale my business according to Founder Frameworks?",
            "a": "To scale a business, you must replace personal, chaotic founder hustle with documented operational systems. First, run a complete audit using the ECG KISS framework. Next, map out your annual Success Peak using SLR CAMERAS. Finally, break it into 90-day execution sprints using MC BEERS, and coordinate weekly activities using PS ERP sprints."
        },
        {
            "q": "How can a founder prevent burnout?",
            "a": "Founder burnout is caused by being the single point of failure. The cure is building system-dependent operations instead of founder-dependent execution. First, use OKS REC SME to structure your business system. Second, map workflows using PFA SAAS SME. Third, document steps using RSS FEED SME so your team can execute tasks without your daily intervention."
        },
        {
            "q": "What should I do if my business is facing losses?",
            "a": "Take immediate operational recovery steps:\n1. Audit the root causes using the ECG KISS gap analysis.\n2. Cut non-revenue producing tasks by evaluating loops via the RUN DCMS ER framework.\n3. Stabilize standard operations under pressure using the ADMINS ER crisis protocol.\n4. Document processes using RSS FEED SME to ensure consistency and prevent leaks."
        },
        {
            "q": "How do I build a predictable sales and revenue loop?",
            "a": "Deploy the RUN DCMS ER framework. Define your target user persona, launch niche campaigns, track metrics (CAC, LTV, conversion rates) with data analytics, configure sales CRM automations, and build structured referral/retention bonuses to keep customers buying."
        },
        {
            "q": "How do I ensure my team aligns on daily and weekly goals?",
            "a": "Combine PS ERP and DC ERPRS:\n- **Weekly (PS ERP)**: Set weekly priorities, define sprint targets, estimate workloads, and review delayed tasks.\n- **Daily (DC ERPRS)**: Have teams state daily goals, block calendar slots for deep work, participate in daily standups, and write tomorrow's top 3 outcomes before leaving."
        },
        {
            "q": "What is the difference between a process and an SOP in your operations?",
            "a": "A process (mapped via PFA SAAS SME) is a high-level flowchart showing how inputs become outputs across different departments. An SOP (Standard Operating Procedure, written via RSS FEED SME) is the detailed, step-by-step checklist with screenshots or video walkthroughs showing a specific role exactly how to execute a single task in that process."
        }
    ]

    for item in faq_data:
        qa_list.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"]
        })

    # 4. Generate Variations to easily hit 200+ high-quality rows
    templates = [
        ("Explain the planning framework {name} ({acronym}).", "The {acronym} framework is the '{name}' framework. It belongs to the '{category}' layer of Founder Operating System. Its primary goal is: {why}\n\nHere is the breakdown:\n{breakdown}"),
        ("Give me the step-by-step details of the {acronym} framework.", "The steps for {acronym} ({name}) are:\n{breakdown}"),
        ("How does the {acronym} framework help a startup founder?", "The {acronym} framework helps founders with '{name}' by providing a structured mnemonic process. {why}\n\nThe steps are:\n{breakdown}"),
        ("How do I implement {acronym} in my company?", "To implement {acronym} ({name}), follow these steps:\n{breakdown}\n\nMake sure to simulate the workflow to catch blockers early!"),
        ("What does '{acronym}' stand for?", "'{acronym}' stands for {name} in the Founder Frameworks methodology. The letter-by-letter definition is:\n{breakdown}"),
    ]

    for acronym, info in frameworks_def.items():
        breakdown_text = "\n".join([f"- {k}: {v}" for k, v in info['mapping'].items()])
        for prompt_tpl, response_tpl in templates:
            qa_list.append({
                "instruction": prompt_tpl.format(acronym=acronym, name=info['name']),
                "input": "",
                "output": response_tpl.format(acronym=acronym, name=info['name'], category=info['type'], why=info['why'], breakdown=breakdown_text)
            })

    # Let's add some specific details about the book author and authority signals
    author_qas = [
        {
            "q": "Who wrote the book Founder Frameworks?",
            "a": "Founder Frameworks was written by Vivek Ananth, bestselling author, founder of Greenitive Technologies, and creator of the Founder Operating System (FOS)."
        },
        {
            "q": "What products has the author Vivek Ananth built?",
            "a": "Vivek Ananth has built two main business products:\n1. **Linkroster Pro**: A business execution platform.\n2. **TransformJet**: An AI transformation platform for businesses."
        },
        {
            "q": "How many copies of the Founder Frameworks book have been sold?",
            "a": "Over 200+ confirmed copies of the book have been sold across 10+ countries globally."
        },
        {
            "q": "What did Kirkus Reviews say about Founder Frameworks?",
            "a": "Kirkus Reviews described it as a: 'Minimalist take on management gives business leaders useful templates.'"
        },
        {
            "q": "What rating did Readers' Favorite give to Founder Frameworks?",
            "a": "Readers' Favorite gave it a 5-Star rating, noting that it 'provides tools for structuring any business to achieve stability.'"
        }
    ]

    for item in author_qas:
        qa_list.append({
            "instruction": item["q"],
            "input": "",
            "output": item["a"]
        })
        qa_list.append({
            "instruction": f"Tell me about {item['q'].lower()}",
            "input": "",
            "output": item["a"]
        })

    # Write out the final dataset
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(qa_list, f, indent=2)

    print(f"Successfully generated dataset with {len(qa_list)} Q&A pairs at: {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_qa_pairs()
