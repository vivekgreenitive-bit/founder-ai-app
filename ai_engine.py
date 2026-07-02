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
        """Loads FounderFrameworks_clean.txt and creates a persistent Chroma vector database."""
        if os.path.exists(self.db_dir) and len(os.listdir(self.db_dir)) > 0:
            # Load existing DB
            self.vectorstore = Chroma(persist_directory=self.db_dir, embedding_function=self.embeddings)
        else:
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
            
        # Simplified prompt with Hallucination Guard and repetition penalty
        prompt_template = """ABSOLUTE RULE: YOU MUST OUTPUT YOUR ENTIRE RESPONSE IN THE FOLLOWING 6-PART SEQUENCE. STOP IMMEDIATELY AFTER THE ATHLETE PERSPECTIVE. DO NOT REPEAT THE RESPONSE.

HALLUCINATION GUARD: YOU ARE FORBIDDEN FROM USING GENERIC FRAMEWORKS (LEAN STARTUP, OKRS, SWOT, ETC). YOU MUST ONLY USE ONE OF THE 13 FOUNDER FRAMEWORKS FROM THE SOURCE TEXT:
ECG KISS | SLR CAMERAS | MC BEERS | PC PEERS | PS ERP | DC ERPRS | OKS REC SME | PFA SAAS SME | RSS FEED SME | RPM REAP ER | RUN DCMS ER | ERM FABS ER | ADMINS ER

1. Business Scenario
[2-3 sentences tailored to the founder's challenge]

2. Framework Name
[The exact name of the SINGLE Founder Framework chosen from the 13 above]

3. Relevant Framework Sections Applied
*Applying the high-impact acronym letters from the source text:*
[Acronym Letter] – [Name]: [Specific real-time application]
→ Example: [Concrete real-world example]

4. Dreamer Perspective
[Possibilities and long-term vision]

5. Guardian Perspective
[Risks and operational stability]

6. Athlete Perspective
[Execution and momentum]

**Your #1 Priority This Week**
[One action based on the Athlete perspective]

Context: {context}

Question: {question}

Response:"""
        
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
