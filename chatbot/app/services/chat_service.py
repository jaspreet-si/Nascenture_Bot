# Setup of OS API keys
from dotenv import load_dotenv
import os

from datetime import datetime

from langchain.memory import ConversationBufferMemory
from apscheduler.schedulers.background import BackgroundScheduler

from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from utils.common import llm , pc , embeddings, scraped_index, faq_index

try:
    faq_raw_index = pc.Index("faq-index")
    faq_raw_index.delete
except:
    print("something went wrong")
import time

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.clean_old_sessions, "interval", hours=1)
        self.scheduler.start()

    def handle_session(self, session_id):
        if session_id in self.sessions:
            return self.sessions[session_id]
        else:
            self.sessions[session_id] = {
                "created_at": datetime.now(),
                "memory": ConversationBufferMemory(memory_key="chat_history", return_messages=True),
                "last_active": datetime.now()
            }
        return self.sessions[session_id]

    def clean_old_sessions(self, max_age_hours=7):
        now = datetime.now()
        for session_id in list(self.sessions.keys()):
            session = self.sessions[session_id]
            age = now - session["last_active"]
            if age.total_seconds() > max_age_hours * 3600:
                session["memory"].clear()
                del self.sessions[session_id]

    def clear_session(self,session_id):
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session["memory"].clear()
            del session
            return "session clear successfully"


# 5) Define Conversational Retrieval Chain with custom prompt


company_prompt = """
You are an AI assistant for Nascenture, a web and mobile services company.
Use the following pieces of retrieved context to answer the user's question.
If a match is found, return the original answer from the context as-is.
Do not summarize or rephrase unless absolutely necessary.
Only say "I don't know" if there is absolutely no related information.
Special instructions:
    - If user asks for a link/page/URL, provide the relevant URL from the context
    - If contact synonyms appear in the input, include "SHOW_CONTACT_FORM" in your response
    - Otherwise, don't mention contacting the company
    
Context: {context}

Chat History: {chat_history}

Question: {question}


Remember: If the user refers to "the company" or similar phrases, they are talking about Nascenture.
Be helpful, concise, and professional in your responses.

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

# 6) Main chatbot function with session handling
def chat_bot(query,session_id):
    start_time = time.time()
    session_manager = SessionManager()

    session = session_manager.handle_session(session_id)
    # qa_chain = create_qa_chain(session["memory"])

    
    
    if query.lower() == 'clear':
        session_manager.clear_session(session_id)
        return "Session cleared successfully."
        
    try:
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
        
        # Check for high-confidence FAQ match
        if faq_result.matches and len(faq_result.matches) > 0:
            top_match = faq_result.matches[0]
            score = top_match.score
            print(f"[FAQ Match Score: {score}]")
            
            if score > 0.77:  # High confidence match
                matched_answer = top_match.metadata.get("answer", "")
                if matched_answer:
                    # Add to memory for conversation history
                    session["memory"].chat_memory.add_user_message(query)
                    session["memory"].chat_memory.add_ai_message(matched_answer)
                    session["last_active"] = datetime.now()
                    return matched_answer
        
        # Step 2: If no direct FAQ match, try retrieval-based approach
        # First determine which retriever to use
        # if faq_result.matches and len(faq_result.matches) > 0 and top_match.score > 0.75:
        #     # Good but not perfect match - use FAQ retriever
        #     selected_retriever = faq_index.as_retriever(search_type="similarity", search_kwargs={"k": 2})
        # else:
        #     # Use scraped content retriever
        selected_retriever = scraped_index.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        
        # Get documents from selected retriever
        docs = selected_retriever.get_relevant_documents(query)
        
        # Handle case where no documents are found
        if not docs:
            return "I don't have information about it right now. Please try again later."
        # Step 3: Build QA chain
        qa_chain = create_qa_chain(session["memory"], selected_retriever)

        # Step 4: Invoke LLM
        response = qa_chain.invoke({"question": query})
        end_time = time.time()
        print("Time taken for response:", round(end_time - start_time, 2), "seconds")
        return response['answer']


    except Exception as e:
        print(f"Error: {e}")
        
    session_manager.clean_old_sessions()
     
# if __name__ == "__main__":
#     chat_with_bot("contact form", "user_1")
    
# nbot = chat_bot()