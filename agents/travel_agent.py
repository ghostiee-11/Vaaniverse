from .base_agent import AgentRunner

class TravelAgent(AgentRunner):
    def run(self, original_query, translated_query, chat_history, lang_code, user_profile):
        city_extraction_prompt = f"History: {chat_history}\nQuery: '{translated_query}'. What city is the subject? Respond with ONLY the city name, or 'None'."
        city_name = self.llm.invoke(city_extraction_prompt).content.strip().lower()

        internal_context = ""
        if "none" not in city_name:
            search_kwargs = {'filter': {'city': city_name}}
            internal_docs = self.vector_store.similarity_search(translated_query, k=2, search_kwargs=search_kwargs)
            internal_context = "\n".join([doc.page_content for doc in internal_docs])

        web_context = self.web_search_tool.invoke(f"Travel guide for {city_name or ''}: {translated_query}")

        # --- THE FIX: Prepare simple variables for the template ---
        prompt = self.prompt_template.format(
            system_prompt=self.prompt_template.input_variables[0],
            chat_history=chat_history,
            internal_context=internal_context,
            web_context=web_context,
            query=original_query,
            lang_code=lang_code,
            # Extract values from the profile dictionary
            mood=user_profile.get("mood", "curious"),
            location=user_profile.get("location", "unknown")
        )
        return self.llm.invoke(prompt).content