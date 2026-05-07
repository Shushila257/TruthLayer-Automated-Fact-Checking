
TruthLayer: Automated Fact-Checking Agent

TruthLayer is an automated fact-checking web application designed to act as a "Truth Layer" for marketing documents. It ingests a PDF, uses an LLM to extract falsifiable claims (statistics, dates, financial figures), and cross-references those claims against live web data to flag inaccuracies or hallucination Features

*   PDF Extraction: Parses uploaded marketing PDFs to identify core claims.
*   Agentic Reasoning: Uses Google Gemini 2.5 Flash to isolate specific, verifiable facts rather than generic statements.
*   Live Web Verification: Bypasses LLM knowledge cutoffs by querying the live web using the Tavily Search API.
*   Automated Auditing: Reports the status of each claim as `Verified`, `Inaccurate`, or `False`, providing explanations and correct data when applicable.
*   User-Friendly Interface: Built with Streamlit for a clean, accessible frontend.

 Tech Stack

*   Language: Python
*   Frontend: Streamlit
*   LLM Engine: Google Gemini (via `google-generativeai`)
*   Web Search Engine: Tavily Search API
*   PDF Parsing: `pypdf`
*   Data Handling: `pandas`
