from datetime import datetime
import re
import random

from langchain.memory import ConversationBufferMemory
from apscheduler.schedulers.background import BackgroundScheduler
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from utils.common import llm, pc, embeddings, scraped_index

# Initialize FAQ index
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
            return "Session cleared successfully! How can I help you today?"
        return "Session not found. How can I help you today?"

# Enhanced company prompt with improved structure, tone, and personality
company_prompt = """
You are a friendly and helpful AI assistant for Nascenture, a web and mobile services company.
Use the context below to answer the user's question in a clear, professional, conversational, and warm tone.

Context: {context}

Chat History: {chat_history}

Question: {question}

Instructions:
1. When discussing services, break them down into clear categories with examples:
   - Web Design: Describe custom web designs tailored to business needs
   - Custom Software Development: Explain how you build software that addresses specific business challenges
   - Ongoing Support & Maintenance: Detail regular updates, bug fixes, and system monitoring

2. Always use a friendly, warm tone:
   - Start responses with greetings like "Hey there!" or "Great question!"
   - End with encouraging phrases like "Feel free to ask if you need more details!"

3. For unclear inputs:
   - Respond with empathy and humor: "Oops! I didn't quite catch that."
   - Guide users back to relevant topics

4. Always suggest follow-up questions or next steps after answering

5. Structure information in digestible chunks with examples for each point

Answer in a conversational, helpful tone:
"""

# Dictionary of friendly greetings and closings for randomization
friendly_greetings = [
    "Hey there! ",
    "Hi! ",
    "Great question! ",
    "Thanks for asking! ",
    "I'd be happy to help! "
]

friendly_closings = [
    "Feel free to ask if you need more details! I'm here to help.",
    "Is there anything specific about this you'd like to know more about?",
    "Let me know if you have any other questions!",
    "Would you like to know more about any of our other services?",
    "Anything else I can help you with today?"
]

# Responses for unclear or gibberish inputs
unclear_responses = [
    "Oops! Looks like I didn't quite catch that. Could you clarify? I'm here to help!",
    "I'm not sure what that means, but I'm here to help you with anything related to web or app development. Let me know what you need!",
    "Hmm, I didn't understand that. Want to know about our services instead? I'd be happy to explain!",
    "I think I missed something there. Could you rephrase? I can help with web design, software development, or support services."
]

# Service descriptions with examples for when asked about services
service_descriptions = """
Hey there! Here's what Nascenture can do for you:

• Web Design: Custom web designs tailored to your business needs. Example: We created a responsive e-commerce site for a local boutique that increased their online sales by 45%.

• Custom Software Development: We build software that addresses specific business challenges. Example: Developing an inventory management system for a manufacturing client that streamlined their operations and reduced errors by 60%.

• Ongoing Support & Maintenance: Regular updates, bug fixes, and system monitoring. Example: Providing 24/7 support for mission-critical applications, ensuring 99.9% uptime for our clients.

Would you like more details about any of these services? Or would you like to discuss how we can help with your specific project?
"""

def create_qa_chain(memory, retriever):
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

def is_gibberish(query):
    """Check if input might be gibberish or unclear"""
    # Create a whitelist of common greetings
    common_greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy"]
    
    # If the input is a common greeting, it's not gibberish
    if query.lower().strip() in common_greetings:
        return False
    
    # Check for very short inputs that aren't greetings
    if len(query) < 2:
        return True
    
    # Check for inputs with unusual character distributions
    letter_ratio = sum(c.isalpha() for c in query) / len(query) if query else 0
    if letter_ratio < 0.5 and len(query) > 3:
        return True
    
    # Check for keyboard mashing patterns
    if re.search(r'([qwerty]+|[asdfgh]+|[zxcvb]+){2,}', query.lower()):
        return True
        
    return False

def enhance_response(response):
    """Add friendly greeting and closing to responses"""
    greeting = random.choice(friendly_greetings)
    closing = random.choice(friendly_closings)
    
    # Avoid adding greeting if response already has one
    if any(response.startswith(g.strip()) for g in friendly_greetings):
        return f"{response}\n\n{closing}"
    
    return f"{greeting}{response}\n\n{closing}"

session_manager = SessionManager()

def chat_bot(query, session_id):
    session = session_manager.handle_session(session_id)
    
    if query.lower() == 'clear':
        return session_manager.clear_session(session_id)
    
    # First check for matches in the Pinecone database for all queries
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
            (top_match.metadata.get("question") and 
             top_match.metadata.get("question").lower() == query.lower())
        ):
        matched_answer = top_match.metadata.get("answer")
        if matched_answer:
            enhanced_matched_answer = enhance_response(matched_answer)
            session["memory"].chat_memory.add_user_message(query)
            session["memory"].chat_memory.add_ai_message(enhanced_matched_answer)
            session["last_active"] = datetime.now()
            return enhanced_matched_answer
   
    # If no match in Pinecone, then handle greetings
    common_greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy"]
    if query.lower().strip() in common_greetings:
        greeting_responses = [
            "Hey there! Thanks for reaching out to Nascenture. How can I help you today? I can tell you about our web design, software development, or support services.",
            "Hello! I'm Nascenture's virtual assistant. I'd be happy to help you with information about our services or answer any questions you might have.",
            "Hi there! Welcome to Nascenture. I'm here to assist with your web and mobile service needs. What can I help you with today?",
            "Greetings! Thanks for connecting with Nascenture. Would you like to know about our services or discuss a specific project?"
        ]
        response = random.choice(greeting_responses)
        session["memory"].chat_memory.add_user_message(query)
        session["memory"].chat_memory.add_ai_message(response)
        return response

    # Special handling for "what services do you provide?" type questions
    if re.search(r'services|offer|provide|do you (do|make)|capabilities', query.lower()):
        session["memory"].chat_memory.add_user_message(query)
        session["memory"].chat_memory.add_ai_message(service_descriptions)
        return service_descriptions
        
    # Handle gibberish or unclear inputs
    if is_gibberish(query):
        response = random.choice(unclear_responses)
        session["memory"].chat_memory.add_user_message(query)
        session["memory"].chat_memory.add_ai_message(response)
        return response
        
    try:
        # Pinecone check already done above, so we move straight to retrieval
       
        # No FAQ match, use retrieval
        retriever = scraped_index.as_retriever(search_type="similarity", search_kwargs={"k": 3})
        docs = retriever.invoke(query)
       
        if not docs:
            fallback_response = "I don't have specific information on that right now. Would you like to know about our services instead, or perhaps I can help you get in touch with our team?"
            enhanced_fallback = enhance_response(fallback_response)
            return enhanced_fallback

        # Build QA chain with retriever and get response
        qa_chain = create_qa_chain(session["memory"], retriever)
        response = qa_chain.invoke({"question": query})
        
        # Enhance the response with friendly tone
        enhanced_response = enhance_response(response['answer'])
        return enhanced_response

    except Exception as e:
        print(f"Error: {e}")
        error_response = "Sorry, I'm having a bit of trouble processing that request. Would you like to know about our services or how we can help with your project instead?"
        return enhance_response(error_response)
        
    finally:
        session_manager.clean_old_sessions()
