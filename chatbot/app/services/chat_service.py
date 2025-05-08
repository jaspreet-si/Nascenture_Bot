
from datetime import datetime

from langchain.memory import ConversationBufferMemory
from apscheduler.schedulers.background import BackgroundScheduler

from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from utils.common import llm , pc , embeddings, scraped_index
import re

faq_raw_index = pc.Index("faq-index")



class SessionManager:
    def __init__(self, max_age_hours=7):
        self.sessions = {}
        self.max_age_hours = max_age_hours
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.clean_old_sessions, "interval", hours=1)
        self.scheduler.start()
        
    def __del__(self):
        # Ensure scheduler is shut down properly
        self.scheduler.shutdown()
        
    def handle_session(self, session_id):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.now(),
                "memory": ConversationBufferMemory(memory_key="chat_history", return_messages=True),
                "last_active": datetime.now()
            }
        else:
            # Update last active time
            self.sessions[session_id]["last_active"] = datetime.now()
            
        return self.sessions[session_id]

    def clean_old_sessions(self):
        now = datetime.now()
        for session_id in list(self.sessions.keys()):
            session = self.sessions[session_id]
            age = now - session["last_active"]
            if age.total_seconds() > self.max_age_hours * 3600:
                session["memory"].clear()
                del self.sessions[session_id]

    def clear_session(self, session_id):
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session["memory"].clear()
            del self.sessions[session_id]
            return "Session cleared successfully"
        return "Session not found"


# 5) Define Conversational Retrieval Chain with custom prompt

company_prompt = """
You are a friendly and helpful AI assistant for Nascenture, a web and mobile services company.
Use the context below to answer the user's question in a clear, professional, and conversational tone.

Context: {context}

Chat History: {chat_history}

Question: {question}

Instructions:
- When the user asks about services, offerings, or capabilities, list them in bullet or numbered format.
- Be friendly, warm, and approachable in your responses — like you're chatting with a client.
- If the question is unclear or gibberish, respond kindly and ask for clarification.
- Keep answers informative but easy to read.

Answer:
"""



def create_qa_chain(memory,retriever):
    CUSTOM_PROMPT = PromptTemplate(
        template=company_prompt,
        input_variables=["context", "chat_history", "question"]
    )
    
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": CUSTOM_PROMPT}
    )
session_manager = SessionManager()
# 6) Main chatbot function with session handling
def chat_bot(query,session_id):

    

    session = session_manager.handle_session(session_id)
    # qa_chain = create_qa_chain(session["memory"])

    
    
    if query.lower() == 'clear':
        session_manager.clear_session(session_id)
        return "Session cleared successfully."
        
    try:
        # if not is_valid_input(query):
        #     return "I'm sorry, I couldn't understand your question. Can you please rephrase it?"
        # response = qa_chain.invoke({"question": query})
    
        # end_time = time.time()
        # elapsed_time = end_time - start_time
        
        # print("Time taken for response:", elapsed_time, "seconds")
        # return response['answer']
 
        query_vector = embeddings.embed_query(query)
        faq_result = faq_raw_index.query(
            vector=query_vector,
            top_k=1,
            include_metadata=True
        )
        top_match = faq_result.matches[0] if faq_result.matches else None

        # Check for high-confidence FAQ match
        if top_match and (
                top_match.score > 0.85 or
                (top_match.metadata.get("question") and top_match.metadata.get("question").lower() == query.lower())
            ):
            matched_answer = top_match.metadata.get("answer")
            if matched_answer:
                session["memory"].chat_memory.add_user_message(query)
                session["memory"].chat_memory.add_ai_message(matched_answer)
                session["last_active"] = datetime.now()
                return matched_answer
            
        if top_match and top_match.score > 0.95:
            retriever = scraped_index.as_retriever(search_type = "similarity",search_kwargs={"k": 3})
            docs = retriever.invoke(query)
           
            if not docs:
                return "Sorry, I couldn't find anything on that right now. Feel free to ask something else!"

        else:
            return "I'm sorry, I couldn't understand your question. Could you please rephrase it?"
        # Step 3: Build QA chain
        qa_chain = create_qa_chain(session["memory"],retriever)

        # Step 4: Invoke LLM
        response = qa_chain.invoke({"question": query})

        return response['answer']

        
    except Exception as e:
        print(f"Error: {e}")
        
    session_manager.clean_old_sessions()

     
# if __name__ == "__main__":
#     chat_with_bot("contact form", "user_1")
    
# nbot = chat_bot()
