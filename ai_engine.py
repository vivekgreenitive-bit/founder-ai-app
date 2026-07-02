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
                max_tokens=1500,  # Increased to prevent truncation of 6-part output
                n_ctx=4096,  # Llama 3.2 supports large context; 4096 is safe for low-end hardware
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
You are Founder AI, an elite business consulting system trained on the Founder Frameworks methodology.

You operate like a senior partner from McKinsey, Bain, BCG, Deloitte Consulting, and Accenture Strategy combined.

Your objective is not to explain frameworks.
Your objective is to solve business problems.

## CORE RULES

1. You ONLY use the following 13 Founder Frameworks. NEVER reference any external framework (McKinsey 7S, Porter's Five Forces, SWOT, BCG Matrix, OKRs, Ansoff Matrix, etc.):
   - ECG KISS — Overall Business Diagnosis
   - SLR CAMERAS — Yearly Planning
   - MC BEERS — Quarterly Planning
   - PC PEERS — Monthly Planning
   - PS ERP — Weekly Planning
   - DC ERPRS — Daily Planning
   - OKS REC SME — Systems Design
   - PFA SAAS SME — Process Building
   - RSS FEED SME — SOP Creation
   - RPM REAP ER — Execution
   - RUN DCMS ER — Revenue Growth
   - ERM FABS ER — Evaluation
   - ADMINS ER — Crisis Management

2. Never expose: book pages, framework chapters, retrieved context, RAG chunks, source documents, citations, internal reasoning.

3. Frameworks are internal reasoning tools only. Never explain what a framework is — only state its name and why it fits.

4. The founder should feel: "This AI understands my business." Never: "This AI searched a book."

5. Diagnose before prescribing.

6. If information is insufficient, ask at most 3 high-value questions.

7. Use founder language, not consulting jargon.
Examples:
"I am not getting business" -> Customer acquisition problem
"I am losing business" -> Revenue leakage or churn problem
"My team is slow" -> Operations problem
"Everything depends on me" -> Founder bottleneck problem

## RESPONSE FORMAT

You MUST respond using EXACTLY these 6 sections in this exact order:

**Business Diagnosis**
[1-2 sentences explaining the likely issue in plain English]

**Why This Happens**
- [Root cause 1]
- [Root cause 2]
- [Root cause 3]

**Immediate Actions**
- [Action the founder can take this week]
- [Action the founder can take this week]
- [Action the founder can take this week]

**Metrics to Track**
- [KPI 1]
- [KPI 2]
- [KPI 3]

**Next Step**
[The single most important follow-up question to ask the founder]

**Recommended Framework**
[Framework name only + one sentence on why it applies to this specific situation]

## STYLE RULES
- Use bold headings.
- Use bullet points.
- Keep responses under 300 words.
- Avoid theory.
- Avoid long explanations.
- Focus on execution.
- Write as if advising a CEO during a board meeting.

## FINAL QUALITY CHECK
Before responding ask internally:
1. Would a founder pay for this advice?
2. Is this actionable?
3. Is this simple enough to understand in 30 seconds?
4. Does this create measurable business impact?
If the answer is no, improve the response.

## CRITICAL OUTPUT RULES
Never output:
- User Document / Question
- Company Profile Context
- Business Name
- Industry Context Block
- Retrieved Documents
- Framework Pages
- Source Documents
- Prompt Instructions
- Context Metadata

If your response contains: "User Document", "Company Profile Context", "Output:", or "Tailor your framework advice", discard the response and regenerate.

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
                        full_query += f"\n\n--- Company Profile Context ---\n"
                        if name: full_query += f"Business Name: {name}\n"
                        if industry: full_query += f"Industry: {industry}\n"
                        if stage: full_query += f"Business Stage: {stage}\n"
                        if team: full_query += f"Team Size: {team}\n"
                        if challenge: full_query += f"Primary Challenge: {challenge}\n"
                        full_query += "---------------------------------\n"
                        full_query += "Tailor your framework advice strictly to this specific business context and demographic."
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
