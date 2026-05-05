import streamlit as st
import requests
import json
import uuid

# --- UI Configuration ---
st.set_page_config(
    page_title="Academic Advisor AI",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a modern look
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
    }
    .stChatInput {
        border-radius: 15px;
    }
    .main-title {
        text-align: center;
        background: -webkit-linear-gradient(45deg, #FF4B2B, #FF416C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🎓 Multi-Agent Academic Advisor</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>An industrial-grade LangGraph architecture powered by Google Gemini.</p>", unsafe_allow_html=True)
st.divider()

# --- Sidebar Demo Questions ---
with st.sidebar:
    st.header("💡 Demo Questions")
    st.markdown("Copy and paste these during your Viva:")
    
    st.markdown("**1. RAG + Tools (Handoff)**")
    st.code("I got an A in CS101, an A- in MT101, and a C in EE101 (all 3 credits). First, search the handbook to see how many grade points an A- is worth, and then use your calculator tool to compute my overall GPA.")
    
    st.markdown("**2. Checkpointer Memory**")
    st.code("If I retake EE101 and improve that C to a B+, what will my new GPA be?")
    
    st.markdown("**3. Policy Verification**")
    st.code("My current GPA is 1.8. According to the university handbook, what is my academic standing? Am I allowed to register for 16 credit hours?")
    
    st.markdown("**4. Exact Tool Execution**")
    st.code("Can you check the final exam schedule for AI301 and CS201?")

# --- State Management ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Render Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- User Input & Streaming Logic ---
if prompt := st.chat_input("Ask about your degree plan, GPA, or university policies..."):
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Agent Response
    with st.chat_message("assistant"):
        # Create a status expander for "thinking" (tool calls)
        status_container = st.status("Agent is thinking...", expanded=True)
        message_placeholder = st.empty()
        
        full_response = ""
        url = "http://127.0.0.1:8000/chat"
        payload = {
            "query": prompt,
            "thread_id": st.session_state.thread_id
        }
        
        try:
            # Stream the response from FastAPI
            with requests.post(url, json=payload, stream=True) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            data = decoded_line[6:] # Strip 'data: ' prefix
                            
                            if data == "[DONE]":
                                status_container.update(label="Response generated!", state="complete", expanded=False)
                                break
                                
                            if data.startswith("[ERROR]"):
                                st.error(f"Backend Error: {data}")
                                status_container.update(label="Error!", state="error")
                                break
                                
                            try:
                                event = json.loads(data)
                                node_name = event.get('node', 'unknown').upper()
                                
                                # Handle Tool Calls
                                if event['type'] == 'tool_call':
                                    status_container.write(f"⚙️ **[{node_name}]**: {event['content']}")
                                
                                # Handle Final Text Output
                                elif event['type'] == 'message':
                                    # We format the node name nicely (e.g. [ADVISOR])
                                    chunk_text = f"**[{node_name}]**: {event['content']}\n\n"
                                    full_response += chunk_text
                                    message_placeholder.markdown(full_response + "▌")
                                    
                            except json.JSONDecodeError:
                                pass
                                
            # Final output cleanup (remove cursor)
            message_placeholder.markdown(full_response)
            
            # Save to history
            if full_response.strip():
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to the FastAPI backend! Please ensure it is running (`uvicorn mcp_project.main:app`).")
            status_container.update(label="Connection Failed", state="error")
