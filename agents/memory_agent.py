class MemoryAgent:
    def __init__(self):
        self.history = []

    def add_record(self, query: str, framework: str, response: str):
        self.history.append({
            "query": query,
            "framework": framework,
            "response": response
        })

    def get_context(self) -> str:
        if not self.history:
            return "No previous query history in this session."
        context = "Previous Session History:\n"
        for idx, record in enumerate(self.history[-3:]):
            context += f"- Run {idx+1}: Solved '{record['query']}' using {record['framework']}\n"
        return context
