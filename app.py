import streamlit as st  # type: ignore[import]
import pypdf
import google.generativeai as genai
from tavily import TavilyClient
import json
import pandas as pd


# --- INITIAL CONFIG ---
st.set_page_config(page_title="TruthLayer: AI Fact-Checker", page_icon="⚖️", layout="wide")

# Sidebar for API Keys
with st.sidebar:
    st.title("Settings")
    google_api_key = st.text_input("Gemini API Key", type="password")
    tavily_api_key = st.text_input("Tavily API Key", type="password")
    st.info("Get a Gemini key at [Google AI Studio](https://aistudio.google.com/) and Tavily at [Tavily.com](https://tavily.com/)")

# Initialize Clients
if google_api_key and tavily_api_key:
    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    tavily = TavilyClient(api_key=tavily_api_key)
else:
    st.warning("Please enter both API keys in the sidebar to begin.")

# --- CORE FUNCTIONS ---

def extract_text_from_pdf(uploaded_file):
    reader = pypdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def get_claims(text):
    prompt = f"""
    Extract the 5 most significant factual claims from the following text. 
    Focus on statistics, dates, financial figures, or technical specs.
    Format the output as a JSON list of strings.
    Text: {text}
    """
    response = model.generate_content(prompt)
    # Clean JSON response
    cleaned_res = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(cleaned_res)

def verify_claim(claim):
    # 1. Search the live web
    search_result = tavily.search(query=claim, search_depth="advanced")
    context = "\n".join([r['content'] for r in search_result['results']])
    
    # 2. Compare and Verify
    verify_prompt = f"""
    Claim: "{claim}"
    Live Web Evidence: {context}
    
    Verify the claim based on the evidence. 
    Return a JSON object with:
    - "status": "Verified", "Inaccurate", or "False"
    - "explanation": A brief reason why
    - "correct_data": The actual fact if the claim is wrong
    """
    response = model.generate_content(verify_prompt)
    cleaned_res = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(cleaned_res)

# --- UI LAYOUT ---

st.title("⚖️ TruthLayer: Automated Fact-Checking")
st.markdown("Upload a PDF to audit its claims against live real-world data.")

uploaded_file = st.file_uploader("Upload Marketing PDF", type="pdf")

if uploaded_file and google_api_key and tavily_api_key:
    with st.spinner("Reading PDF and extracting claims..."):
        pdf_text = extract_text_from_pdf(uploaded_file)
        claims = get_claims(pdf_text)
    
    st.subheader("Extracted Claims & Verification")
    
    results = []
    for claim in claims:
        with st.expander(f"Checking: {claim}"):
            with st.spinner("Verifying against live web data..."):
                analysis = verify_claim(claim)
                
                # Visual Feedback
                if analysis['status'] == "Verified":
                    st.success(f"**Status:** {analysis['status']}")
                elif analysis['status'] == "Inaccurate":
                    st.warning(f"**Status:** {analysis['status']}")
                else:
                    st.error(f"**Status:** {analysis['status']}")
                
                st.write(f"**Analysis:** {analysis['explanation']}")
                if analysis['correct_data']:
                    st.info(f"**Correct Fact:** {analysis['correct_data']}")
                
                results.append({
                    "Claim": claim,
                    "Status": analysis['status'],
                    "Correct Data": analysis['correct_data']
                })

    # Summary Table
    if results:
        st.divider()
        st.subheader("Audit Summary")
        df = pd.DataFrame(results)
        st.table(df)
