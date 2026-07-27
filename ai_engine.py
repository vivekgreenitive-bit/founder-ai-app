import os
from dotenv import load_dotenv
load_dotenv()

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from huggingface_hub import hf_hub_download

# Define model details — Llama 3.2 3B Instruct (open source, optimized for low-end hardware)
REPO_ID = os.getenv("LLM_REPO_ID", "bartowski/Llama-3.2-3B-Instruct-GGUF")
FILENAME = os.getenv("LLM_FILENAME", "Llama-3.2-3B-Instruct-Q4_K_M.gguf")
MODEL_DIR = os.getenv("MODEL_DIR", "models")
MODEL_PATH = os.path.join(MODEL_DIR, FILENAME)

from typing import Any, Optional

class FounderAIEngine:
    vectorstore: Optional[Any]
    llm: Optional[Any]
    qa_chain: Optional[Any]
    db_dir: str
    embeddings: HuggingFaceEmbeddings

    def __init__(self) -> None:
        self.vectorstore = None
        self.llm = None
        self.qa_chain = None
        self.db_dir = os.getenv("CHROMA_DB_DIR", "chroma_db")
        
        # We use a fast, lightweight embedding model
        emb_model = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        self.embeddings = HuggingFaceEmbeddings(model_name=emb_model)
        
        self.init_llm()
        self.init_vectorstore()
        
    def init_llm(self):
        """Initializes the local LLM using llama-cpp-python, checking for custom models first."""
        try:
            os.makedirs(MODEL_DIR, exist_ok=True)
            
            # Prioritize custom fine-tuned models if present in the models directory
            custom_models = ["unsloth.Q8_0.gguf", "unsloth.Q4_K_M.gguf", "founder-ai-3b-q8.gguf"]
            active_model_path = MODEL_PATH
            
            for custom_name in custom_models:
                p = os.path.join(MODEL_DIR, custom_name)
                if os.path.exists(p):
                    active_model_path = p
                    print(f"Found custom fine-tuned model: {custom_name}")
                    break
            
            if active_model_path == MODEL_PATH and not os.path.exists(MODEL_PATH):
                print(f"Model not found locally. Downloading default {FILENAME} from Hugging Face...")
                hf_hub_download(repo_id=REPO_ID, filename=FILENAME, local_dir=MODEL_DIR)
                print("Download complete!")
                
            print(f"Loading LLM from: {active_model_path}")
            temp = float(os.getenv("LLM_TEMPERATURE", "0.1"))
            max_tok = int(os.getenv("LLM_MAX_TOKENS", "1000"))
            ctx_size = int(os.getenv("LLM_N_CTX", "4096"))
            
            self.llm = LlamaCpp(
                model_path=active_model_path,
                temperature=temp,
                max_tokens=max_tok,
                n_ctx=ctx_size,
                stop=["<|eot_id|>", "Context:", "Question:"],
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
            
        from agents.orchestrator import OrchestratorAgent
        self.orchestrator = OrchestratorAgent(self.llm, self.vectorstore)

    def analyze_query(self, query: str, document_text: str = "", status_callback=None) -> str:
        if not self.orchestrator:
            return "Error: AI Engine is not fully initialized. Please ensure the model file exists."

        # Extract manual framework choice if combined in query string
        user_framework = None
        for trigger in ["Please apply the framework:", "Apply the framework:"]:
            if trigger in query:
                parts = query.split(trigger)
                query = parts[0].strip()
                user_framework = parts[1].strip()
                break

        profile_data = {}
        try:
            import json
            profile_path = "company_profile.json"
            if os.path.exists(profile_path):
                with open(profile_path, 'r') as f:
                    profile_data = json.load(f)
        except Exception as e:
            print("Could not load company context:", e)

        try:
            response = self.orchestrator.run(
                query=query,
                document_text=document_text,
                profile_data=profile_data,
                user_framework=user_framework,
                status_callback=status_callback
            )
            return response
        except Exception as e:
            return f"Error during analysis: {str(e)}"
