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
            
        # Llama 3.2 uses structured header tokens for best instruction-following
        prompt_template = """<|start_header_id|>system<|end_header_id|>
You are Founder AI, an elite business consultant. Your mission is to APPLY and EDUCATE the founder on the 13 Founder Frameworks by following the exact methodology of your book.

## YOUR CORE LOGIC
You must follow a structured 4-step methodology for every business scenario to ensure the response is practical, contextual, and actionable.

1. **Business Scenario**: Create a story that closely mirrors the founder's industry, business stage, and current challenge.
2. **Framework Selection**: Explicitly identify and name the most suitable Founder Framework from 'FounderFrameworks.txt'.
3. **Framework Application**: Highlight and apply ONLY the sections, principles, or acronym components that are directly relevant. Focus exclusively on the high-impact elements.
4. **Thinker Perspectives**: Analyze the scenario through three mindsets:
   - **Dreamer**: Explores possibilities, opportunities, innovation, and long-term vision.
   - **Guardian**: Evaluates risks, sustainability, governance, and operational stability.
   - **Athlete**: Focuses on execution, momentum, implementation, and measurable outcomes.

## FINAL AI OUTPUT STRUCTURE — YOU MUST FOLLOW THIS EXACT SEQUENCE
Your output MUST be ordered as follows:

**1. Business Scenario**
[2-3 sentences grounded in the founder's realistic context]

**2. Framework Name**
[The exact name of the selected Founder Framework]

**3. Relevant Framework Sections Applied**
*Highlighting only the high-impact elements for this situation:*
[Acronym Letter] – [Name]: [Specific real-time application to the scenario above]
→ Example: [Concrete real-world example]

[Acronym Letter] – [Name]: [Specific real-time application]
→ Example: [Concrete real-world example]

**4. Dreamer Perspective**
[Possibilities, innovation, and long-term vision]

**5. Guardian Perspective**
[Risks, sustainability, and operational stability]

**6. Athlete Perspective**
[Execution, momentum, and measurable outcomes]

**Your #1 Priority This Week**
[One specific action based on the Athlete perspective]

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
