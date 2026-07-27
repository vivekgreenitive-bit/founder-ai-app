class KnowledgeRetrievalAgent:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore

    def run(self, query: str, framework_name: str) -> str:
        search_query = f"{framework_name} framework context to solve: {query}"
        try:
            docs = self.vectorstore.similarity_search(search_query, k=6)
            context = "\n\n".join([doc.page_content for doc in docs])
            return context
        except Exception as e:
            print(f"Error in KnowledgeRetrievalAgent: {e}")
            return ""
