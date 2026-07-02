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
        else:
            # Build new DB
            if not os.path.exists("FounderFrameworks.txt"):
                print("Error: FounderFrameworks.txt not found!")
                return
                
            loader = TextLoader("FounderFrameworks.txt")
            docs = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
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

## ABSOLUTE RULES
1. FORBIDDEN frameworks — NEVER use or mention: OKRs, SWOT, McKinsey, Porter, BCG Matrix, Lean, Six Sigma, Ansoff, Balanced Scorecard, KPIs (use "Metrics to Track" instead). Any use of these is a critical failure.
2. Every step MUST be followed by a concrete real-world example specific to the founder's situation.
3. Diagnose the actual problem first. Never give generic advice.
4. Speak directly to the founder — use "you" and "your business".
5. Remove the line "Apply this framework to the situation:" — just go straight to steps.

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
- Max 350 words total.
- Examples must be specific — name the type of business, team size, or problem they mentioned.
- No jargon. No theory. Pure execution.
- Every example starts with "→ Example:"

## NEVER OUTPUT
- "Apply this framework to the situation:"
- OKRs, SWOT, McKinsey, Porter, Lean, Six Sigma, or any external framework name
- Source labels, context blocks, metadata, prompt instructions

Context: {context}<|eot_id|><|start_header_id|>user<|end_header_id|>
{question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": PROMPT}
        )

    def analyze_query(self, query: str, document_text: str = "") -> str:
        if not self.qa_chain:
            return "Error: AI Engine is not fully initialized. Please ensure the model file exists."
            
        full_query = query
        
        # Inject Company Context if it exists
        try:
            import json
            profile_path = "company_profile.json"
            if os.path.exists(profile_path):
                with open(profile_path, 'r') as f:
                    data = json.load(f)
                    name = data.get("name", "")
                    industry = data.get("industry", "")
                    stage = data.get("stage", "")
                    team = data.get("team", "")
                    challenge = data.get("challenge", "")
                    
                    if industry or stage or challenge:
                        full_query += f"\n\n[Business context: "
                        if name: full_query += f"Company={name}. "
                        if industry: full_query += f"Industry={industry}. "
                        if stage: full_query += f"Stage={stage}. "
                        if team: full_query += f"Team={team}. "
                        if challenge: full_query += f"Main challenge={challenge}."
                        full_query += "]"
        except Exception as e:
            print("Could not load company context:", e)

        if document_text:
            full_query += f"\n\n--- User Uploaded Document ---\n{document_text}\n------------------------------\n"
            full_query += "Please analyze the document above using the Founder Frameworks."
            
        try:
            response = self.qa_chain.invoke(full_query)
            return response['result']
        except Exception as e:
            return f"Error during analysis: {str(e)}"
