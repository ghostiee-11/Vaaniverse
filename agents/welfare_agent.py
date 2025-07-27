from .base_agent import AgentRunner

class WelfareAgent(AgentRunner):
    def run(self, original_query, translated_query, chat_history, lang_code, user_profile):
        internal_docs = self.vector_store.similarity_search(translated_query, k=3)
        internal_context = "\n".join([doc.page_content for doc in internal_docs])
        web_context = self.web_search_tool.invoke(translated_query)
        
        # --- THE FIX: Prepare simple variables for the template ---
        prompt = self.prompt_template.format(
            system_prompt=self.prompt_template.input_variables[0],
            chat_history=chat_history,
            internal_context=internal_context,
            web_context=web_context,
            query=original_query,
            lang_code=lang_code,
            # Extract values from the profile dictionary
            user_goals=user_profile.get("goals", "not specified")
        )
        return self.llm.invoke(prompt).content