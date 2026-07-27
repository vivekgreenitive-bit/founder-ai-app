import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    llm_repo_id: str = Field(default="bartowski/Llama-3.2-3B-Instruct-GGUF")
    llm_filename: str = Field(default="Llama-3.2-3B-Instruct-Q4_K_M.gguf")
    model_dir: str = Field(default="models")
    chroma_db_dir: str = Field(default="chroma_db")
    embedding_model_name: str = Field(default="all-MiniLM-L6-v2")
    llm_temperature: float = Field(default=0.1)
    llm_max_tokens: int = Field(default=1000)
    llm_n_ctx: int = Field(default=4096)

    @property
    def model_path(self) -> str:
        return os.path.join(self.model_dir, self.llm_filename)

# Parse environment variables safely with defaults
settings = Settings(
    llm_repo_id=os.getenv("LLM_REPO_ID", "bartowski/Llama-3.2-3B-Instruct-GGUF"),
    llm_filename=os.getenv("LLM_FILENAME", "Llama-3.2-3B-Instruct-Q4_K_M.gguf"),
    model_dir=os.getenv("MODEL_DIR", "models"),
    chroma_db_dir=os.getenv("CHROMA_DB_DIR", "chroma_db"),
    embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"),
    llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
    llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
    llm_n_ctx=int(os.getenv("LLM_N_CTX", "4096"))
)
