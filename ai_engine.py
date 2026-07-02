import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from huggingface_hub import hf_hub_download

# Define model details
REPO_ID = "TheBloke/phi-2-GGUF"
FILENAME = "phi-2.Q4_K_M.gguf"
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
                max_tokens=1000,
                n_ctx=2048, # Context window suitable for smaller models
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
            
        prompt_template = """Instruct: Act as a combined partner at McKinsey, Bain, BCG, Deloitte, Accenture Strategy, and EY-Parthenon.

Your objective is NOT to answer business questions.
Your objective is to DIAGNOSE business problems.

Use the provided Founder Frameworks playbook context to fuel your hypothesis-driven problem solving.

CRITICAL RULES:
1. NEVER dump framework text or quote book pages.
2. NEVER answer with generic advice.
3. NEVER repeat the user's prompt or context.
4. Diagnosis comes before prescription. If you don't have enough info, focus on diagnostic questions.
5. You MUST format your response EXACTLY using the 7 headers provided below.

Output Format:
**1. Executive Summary**
[1-2 sentences identifying the core business domain and brutal truth of the situation]

**2. Root Cause Analysis**
[Hypothesis-driven breakdown of the underlying issue, not just the symptom]

**3. Immediate Actions / Diagnostic Questions**
[If enough info exists: Bulleted list of immediate triage actions. If NOT enough info exists: Elite diagnostic questions you would ask the CEO]

**4. Metrics to Track**
[3 specific KPIs to measure the turnaround]

**5. 30-Day Plan**
[Actionable week-by-week sprint using a specific Founder Framework]

**6. Risks**
[What could go wrong with this implementation]

**7. Success Criteria**
[How we know the problem is permanently solved]

Context: {context}

User Document / Question: {question}

Output:"""
        
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
