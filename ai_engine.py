import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from huggingface_hub import hf_hub_download

# Define model details — Llama 3.2 3B Instruct (open source, optimized for low-end hardware)
REPO_ID = "bartowski/Llama-3.2-3B-Instruct-GGUF"
FILENAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, FILENAME)

class FounderAIEngine:
    def __init__(self):
        self.vectorstore = None
        self.llm = None
        self.qa_chain = None
        self.db_dir = "chroma_db"
        
        # We use a fast, lightweight embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        self.init_llm()
        self.init_vectorstore()
        
    def init_llm(self):
        """Initializes the local LLM using llama-cpp-python, downloading it if needed."""
        try:
            if not os.path.exists(MODEL_PATH):
                print(f"Model not found locally. Downloading {FILENAME} from Hugging Face...")
                os.makedirs(MODEL_DIR, exist_ok=True)
                hf_hub_download(repo_id=REPO_ID, filename=FILENAME, local_dir=MODEL_DIR)
                print("Download complete!")
                
            self.llm = LlamaCpp(
                model_path=MODEL_PATH,
                temperature=0.1,
                max_tokens=1800,  # Extra headroom for per-step examples
                n_ctx=4096,
                verbose=False
            )
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            
    def init_vectorstore(self):
        """Loads FounderFrameworks.txt and creates a persistent Chroma vector database."""
        if os.path.exists(self.db_dir) and len(os.listdir(self.db_dir)) > 0:
            # Load existing DB
            self.vectorstore = Chroma(persist_directory=self.db_dir, embedding_function=self.embeddings)
            # Build new DB
            clean_file = "FounderFrameworks_clean.txt"
            if not os.path.exists(clean_file):
                print(f"Error: {clean_file} not found! Please run cleaner script.")
                return
                
            loader = TextLoader(clean_file)
            docs = loader.load()
            
            # Smaller chunk size to keep framework headers and steps tightly bound
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=600,
                chunk_overlap=100,
                separators=["\n\n", "\n", ".", " ", ""]
            )
            splits = text_splitter.split_documents(docs)
            
            self.vectorstore = Chroma.from_documents(
                documents=splits, 
                embedding=self.embeddings, 
                persist_directory=self.db_dir
            )
            
        self.setup_qa_chain()

    def setup_qa_chain(self):
        if not self.llm or not self.vectorstore:
            return
            
        # Llama 3.2 uses structured header tokens for best instruction-following
        prompt_template = """<|start_header_id|>system<|end_header_id|>
You are Founder AI, an elite business consultant trained exclusively on the Founder Frameworks methodology.

## THE ONLY 13 FRAMEWORKS YOU MAY USE
ECG KISS | SLR CAMERAS | MC BEERS | PC PEERS | PS ERP | DC ERPRS | OKS REC SME | PFA SAAS SME | RSS FEED SME | RPM REAP ER | RUN DCMS ER | ERM FABS ER | ADMINS ER

## PROBLEM-TO-FRAMEWORK MAPPING (MANDATORY)
If the user mentions these problems, you MUST use the corresponding framework from your context:
- "Project Requirements", "Architecture", "System Setup" -> OKS REC SME (System)
- "Process", "Workflow", "Automation" -> PFA SAAS SME (Process)
- "SOP", "Instructions", "Handover" -> RSS FEED SME (SOP)
- "Revenue", "Sales", "Growth" -> RUN DCMS ER (Revenue)
- "Planning", "Goals", "Bottleneck" -> ECG KISS (Overall)
- "Daily Task", "Focus" -> DC ERPRS (Daily)
- "Execution", "Team Performance" -> RPM REAP ER (Execution)

## ABSOLUTE RULES
1. FORBIDDEN frameworks — NEVER use or mention: OKRs, SWOT, McKinsey, Porter, BCG Matrix, Lean, Six Sigma, Ansoff, Balanced Scorecard, KPIs (use "Metrics to Track" instead). Any use of these is a critical failure.
2. Every step MUST be followed by a concrete real-world example specific to the founder's situation.
3. Diagnose the actual problem first. Never give generic advice.
4. Speak directly to the founder — use "you" and "your business".
5. If the provided context does not contain the specific framework needed, say: "I need to look deeper into the [Framework Name] methodology to give you a precise answer. Could you tell me more about your [specific area]?" Do NOT hallucinate generic frameworks.

## RESPONSE FORMAT — FOLLOW THIS EXACTLY

**Diagnosis**
[1-2 sentences: what the real problem is for THIS founder]

**Root Causes**
- [Specific cause in their context]
- [Specific cause in their context]
- [Specific cause in their context]

**Framework: [EXACT NAME] — [Role]**
Step 1: [Specific action for this founder]
→ Example: [A real, concrete example applied to their specific business — name their industry/problem]
Step 2: [Specific action]
→ Example: [Real example for their situation]
Step 3: [Specific action]
→ Example: [Real example for their situation]

**Supporting Framework: [EXACT NAME] — [Role]**
Step 1: [Action]
→ Example: [Real example]
Step 2: [Action]
→ Example: [Real example]

**Metrics to Track**
- [Specific metric for their situation]
- [Specific metric for their situation]
- [Specific metric for their situation]

**Your #1 Priority This Week**
[One clear, specific action the founder must do immediately — no theory]

## STYLE RULES
- Max 400 words total.
- Examples must be specific — name the type of business, team size, or problem they mentioned.
- Every example starts with "→ Example:"

Context: {context}<|eot_id|><|start_header_id|>user<|end_header_id|>
{question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 6}),
            chain_type_kwargs={"prompt": PROMPT}
        )

    def analyze_query(self, query: str, document_text: str = "") -> str:
        if not self.qa_chain:
            return "Error: AI Engine is not fully initialized. Please ensure the model file exists."

        # ── Build the query with the actual problem FIRST and prominent ──────
        # Company profile is background context ONLY — never substitute it for
        # the real question the founder is asking right now.
        background = ""
        try:
            import json
            profile_path = "company_profile.json"
            if os.path.exists(profile_path):
                with open(profile_path, 'r') as f:
                    data = json.load(f)
                    name     = data.get("name", "")
                    industry = data.get("industry", "")
                    stage    = data.get("stage", "")
                    team     = data.get("team", "")
                    # NOTE: we intentionally exclude the profile's "challenge" field
                    # so it does not override the founder's actual question below.
                    parts = []
                    if name:     parts.append(f"Company: {name}")
                    if industry: parts.append(f"Industry: {industry}")
                    if stage:    parts.append(f"Stage: {stage}")
                    if team:     parts.append(f"Team: {team}")
                    if parts:
                        background = "[Background — use for personalisation only, do NOT use as the problem to solve: " \
                                     + ", ".join(parts) + "]"
        except Exception as e:
            print("Could not load company context:", e)

        if document_text:
            background += (
                f"\n\n[Uploaded document — analyse this in context of the problem below]:\n"
                f"{document_text}\n"
            )

        # The founder's ACTUAL problem is the primary focus — always solve THIS
        full_query = (
            f"SOLVE THIS SPECIFIC PROBLEM (ignore any other challenges): {query}\n\n"
            f"{background}"
        )

        try:
            response = self.qa_chain.invoke(full_query)
            return response['result']
        except Exception as e:
            return f"Error during analysis: {str(e)}"
