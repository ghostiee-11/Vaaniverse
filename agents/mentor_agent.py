from .base_agent import AgentRunner

class MentorAgent(AgentRunner):
    """
    An advanced, multilingual mentor agent that uses query expansion for better matching
    and an honest, professional persona.
    """
    def run(self, original_query: str, translated_query: str, chat_history: list, lang_code: str, user_profile: dict):
        # Use query expansion on the translated query for better RAG results
        query_expansion_prompt = f"A user wants a mentor for '{translated_query}'. List 5 related technical skills a good mentor might have."
        expanded_query = self.llm.invoke(query_expansion_prompt).content
        
        context_docs = self.vector_store.similarity_search(expanded_query, k=1)
        context = "\n".join([doc.page_content for doc in context_docs])

        prompt = self.prompt_template.format(
            system_prompt=self.prompt_template.input_variables[0],
            chat_history=chat_history,
            mentor_context=context,
            query=original_query,
            lang_code=lang_code
        )
        return self.llm.invoke(prompt).content