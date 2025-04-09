import streamlit as st
import requests
import pandas as pd
import time
import random
from itertools import chain
import csv
import io

st.set_page_config(page_title="Google AutoSuggest Keyword Scraper", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .title {
        font-size: 42px;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 20px;
    }
    .subtitle {
        font-size: 24px;
        color: #424242;
        margin-bottom: 30px;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stProgress > div > div {
        background-color: #1E88E5;
    }
    .keyword-count {
        font-size: 20px;
        font-weight: bold;
        color: #1E88E5;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown('<div class="title">Google AutoSuggest Keyword Scraper</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Extract keyword ideas using the "Alphabet Soup" method</div>', unsafe_allow_html=True)

# Function to get Google autosuggest results
def get_google_suggestions(keyword, country_code="us", language="en"):
    """Get Google autosuggest results for a keyword."""
    base_url = "https://suggestqueries.google.com/complete/search"
    params = {
        "client": "firefox",  # Using firefox client to get JSON response
        "q": keyword,
        "hl": language,
        "gl": country_code
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code == 200:
            suggestions = response.json()[1]
            return suggestions
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching suggestions: {e}")
        return []

# Function to scrape keywords using the alphabet soup method
def scrape_keywords(base_keyword, use_letters=True, use_numbers=True, use_questions=True, 
                    position="after", country_code="us", language="en"):
    """
    Scrape Google AutoSuggest keywords using the alphabet soup method.
    
    Args:
        base_keyword: The seed keyword
        use_letters: Whether to append letters a-z
        use_numbers: Whether to append numbers 0-9
        use_questions: Whether to append question words
        position: Where to append the modifiers ("before" or "after")
        country_code: Country code for Google search
        language: Language code for Google search
    
    Returns:
        List of unique keyword suggestions
    """
    all_suggestions = []
    prefixes = []
    
    # Add letters if selected
    if use_letters:
        prefixes.extend(list('abcdefghijklmnopqrstuvwxyz'))
    
    # Add numbers if selected
    if use_numbers:
        prefixes.extend([str(i) for i in range(10)])
    
    # Add question words if selected
    if use_questions:
        question_words = ['why', 'what', 'where', 'when', 'how', 'which', 'who', 'is', 'can', 'does', 'do', 'are', 'will']
        prefixes.extend(question_words)
    
    total_queries = len(prefixes) + 1  # +1 for the base keyword itself
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # First get suggestions for the base keyword itself
    status_text.text(f"Fetching suggestions for: {base_keyword}")
    base_suggestions = get_google_suggestions(base_keyword, country_code, language)
    all_suggestions.extend(base_suggestions)
    progress_bar.progress(1/total_queries)
    
    # Then for each prefix
    for i, prefix in enumerate(prefixes, 1):
        if position == "before":
            query = f"{prefix} {base_keyword}"
        else:  # "after"
            query = f"{base_keyword} {prefix}"
        
        status_text.text(f"Fetching suggestions for: {query}")
        suggestions = get_google_suggestions(query, country_code, language)
        all_suggestions.extend(suggestions)
        
        # Update progress
        progress_bar.progress((i + 1)/total_queries)
        
        # Add a small random delay to avoid rate limiting
        time.sleep(random.uniform(0.5, 1.5))
    
    # Also get suggestions for the base keyword with a space at the end
    status_text.text(f"Fetching suggestions for: {base_keyword} ")
    space_suggestions = get_google_suggestions(f"{base_keyword} ", country_code, language)
    all_suggestions.extend(space_suggestions)
    
    # Return unique suggestions
    unique_suggestions = list(set(all_suggestions))
    status_text.text("Completed!")
    progress_bar.progress(1.0)
    
    return unique_suggestions

# Function to convert keyword suggestions to CSV
def get_csv_download_link(df):
    """Generate a link to download the dataframe as CSV."""
    csv = df.to_csv(index=False)
    b64 = base64_csv_conversion(csv)
    return f'<a href="data:file/csv;base64,{b64}" download="keyword_suggestions.csv">Download CSV file</a>'

def base64_csv_conversion(csv_string):
    """Convert CSV string to base64 for download."""
    import base64
    return base64.b64encode(csv_string.encode()).decode()

# Sidebar options
st.sidebar.header("Settings")

# User inputs
seed_keyword = st.sidebar.text_input("Enter your seed keyword:", "coffee")

# Advanced options
with st.sidebar.expander("Advanced Options", expanded=False):
    use_letters = st.checkbox("Use letters (a-z)", value=True)
    use_numbers = st.checkbox("Use numbers (0-9)", value=True)
    use_questions = st.checkbox("Use question words", value=True)
    
    position = st.radio("Add modifiers:", ["after", "before"], index=0)
    
    country_code = st.selectbox(
        "Country:",
        ["us", "uk", "ca", "au", "de", "fr", "es", "it", "jp", "br", "in"],
        index=0
    )
    
    language = st.selectbox(
        "Language:",
        ["en", "es", "fr", "de", "it", "pt", "ja", "zh", "hi", "ar"],
        index=0
    )

# Main area
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Run Scraper")
    if st.button("Start Scraping"):
        if not seed_keyword:
            st.error("Please enter a seed keyword")
        else:
            with st.spinner("Scraping keywords..."):
                suggestions = scrape_keywords(
                    seed_keyword, 
                    use_letters, 
                    use_numbers, 
                    use_questions, 
                    position,
                    country_code,
                    language
                )
                
                # Create DataFrame
                df = pd.DataFrame(suggestions, columns=["Keyword Suggestion"])
                
                # Add seed keyword column
                df["Seed Keyword"] = seed_keyword
                
                # Reorder columns
                df = df[["Seed Keyword", "Keyword Suggestion"]]
                
                # Store in session state
                st.session_state.suggestions_df = df
                st.session_state.suggestions_count = len(suggestions)

with col2:
    st.subheader("Results")
    
    # Display results if available
    if 'suggestions_df' in st.session_state:
        st.markdown(f'<div class="keyword-count">Found {st.session_state.suggestions_count} keyword suggestions</div>', unsafe_allow_html=True)
        
        # Display dataframe
        st.dataframe(st.session_state.suggestions_df, height=400)
        
        # Download button
        csv = st.session_state.suggestions_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="keyword_suggestions.csv",
            mime="text/csv"
        )

# Add information about the tool
with st.expander("About this tool"):
    st.markdown("""
    ### How it works:
    1. **Seed Keyword**: Enter your main keyword that you want to research
    2. **Alphabet Soup Method**: The tool appends letters (a-z), numbers (0-9), and question words to your seed keyword
    3. **Google AutoSuggest**: For each variation, the tool queries Google's AutoSuggest API
    4. **Results**: All unique keyword suggestions are collected and can be downloaded as a CSV
    
    ### Use Cases:
    - SEO research and content planning
    - PPC keyword research
    - Understanding user search intent
    - Finding long-tail keyword opportunities
    """)
