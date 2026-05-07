import streamlit as st
import pypdf
import google.generativeai as genai
from tavily import TavilyClient
import json
import pandas as pd
import time
from google.api_core.exceptions import ResourceExhausted

# --- INITIAL CONFIG ---
st.set_page_config(page_title="TruthLayer: AI Fact-Checker", page_icon="⚖️", layout="wide")

# Sidebar for API Keys
with st.sidebar:
    st.title("Settings")
    google_api_key = st.text_input("Gemini API Key", type="password")
    tavily_api_key = st.text_input("Tavily API Key", type="password")
    st.info("Get a Gemini key at Google AI Studio and Tavily at Tavily.com")

# Initialize Clients
if google_api_key and tavily_api_key:
    genai.configure(api_key=google_api_key)
    # Using 2.5 Flash as it is the most stable for free-tier rapid processing
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

# The @st.cache_data decorator prevents Streamlit from re-running this API call
# if the exact same PDF text is passed in.
@st.cache_data
def get_claims(text):
    prompt = f"""
    Extract the 5 most significant factual claims from the following text. 
    Focus on statistics, dates, financial figures, or technical specs.
    Format the output as a JSON list of strings.
    Text: {text}
    """
    try:
        response = model.generate_content(prompt)
        cleaned_res = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_res)
    except ResourceExhausted:
        st.error("🚨 Gemini API Free Tier Limit Hit during Extraction. Please wait 60 seconds and refresh the page.")
        st.stop()
    except Exception as e:
        st.error(f"Failed to parse claims: {str(e)}")
        st.stop()

def verify_claim(claim):
    try:
        search_result = tavily.search(query=claim, search_depth="advanced")
        context = "\n".join([r['content'] for r in search_result['results']])
        
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

    except ResourceExhausted:
        return {
            "status": "Rate Limited",
            "explanation": "Google's free tier limit reached during this check. We skipped it to protect your app.",
            "correct_data": "N/A"
        }
    except Exception as e:
        return {
            "status": "Error",
            "explanation": f"An unexpected error occurred: {str(e)}",
            "correct_data": None
        }

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
            with st.spinner("Verifying against live web data... (Pacing to respect API limits)"):
                
                # The crucial 10-second pause to prevent 429 crashes in the loop
                time.sleep(10)
                
                analysis = verify_claim(claim)
                
                # Visual Feedback
                if analysis['status'] == "Verified":
                    st.success(f"**Status:** {analysis['status']}")
                elif analysis['status'] == "Inaccurate":
                    st.warning(f"**Status:** {analysis['status']}")
                elif analysis['status'] in ["Rate Limited", "Error"]:
                    st.info(f"**Status:** {analysis['status']}")
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
