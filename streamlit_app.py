import streamlit as st
import requests
import pandas as pd
import time
import random
from collections import defaultdict

st.set_page_config(page_title="Google AutoSuggest Raktažodžių Scraper", layout="wide")

# Nustatome puslapio stilių
st.markdown("""
<style>
    .title {
        font-size: 36px;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
    }
    .modifier-header {
        font-size: 24px;
        font-weight: bold;
        margin-top: 20px;
        color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Google AutoSuggest Raktažodžių Scraper</div>', unsafe_allow_html=True)
st.markdown("Įrankis raktažodžių idėjoms surinkti su grupuotais rezultatais")

# Funkcija Google pasiūlymams gauti
def get_google_suggestions(keyword, country_code="lt", language="lt"):
    """Gauti Google autosuggest rezultatus raktažodžiui."""
    base_url = "https://suggestqueries.google.com/complete/search"
    params = {
        "client": "firefox",  # Firefox klientas JSON atsakymui gauti
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
            st.warning(f"Klaida gaunant pasiūlymus. Statusas: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Klaida: {str(e)}")
        return []

# Šoninė juosta su nustatymais
st.sidebar.header("Nustatymai")

# Pagrindinio raktažodžio įvedimas
seed_keyword = st.sidebar.text_input("Įveskite pagrindinį raktažodį:", "kava")

# Papildomos parinktys
with st.sidebar.expander("Papildomi nustatymai", expanded=False):
    use_letters = st.checkbox("Naudoti raides (a-z)", value=True)
    use_numbers = st.checkbox("Naudoti skaičius (0-9)", value=True)
    use_questions = st.checkbox("Naudoti klausimų žodžius", value=True)
    
    position = st.radio("Pridėti modifikatorius:", ["po", "prieš"], index=0)
    
    country_code = st.selectbox(
        "Šalis:",
        ["lt", "us", "uk", "de", "fr", "es"],
        index=0
    )
    
    language = st.selectbox(
        "Kalba:",
        ["lt", "en", "es", "fr", "de"],
        index=0
    )

# Pagrindinis veiksmas
if st.sidebar.button("Pradėti paiešką"):
    if not seed_keyword:
        st.error("Prašome įvesti pagrindinį raktažodį")
    else:
        st.info(f"Pradedama paieška raktažodžiui: {seed_keyword}")
        
        # Saugome visus rezultatus žodyne, kur raktas yra modifikatorius
        modifier_results = defaultdict(list)
        all_modifiers = []
        
        # Raides pridedame, jei pasirinkta
        if use_letters:
            all_modifiers.extend(list('abcdefghijklmnopqrstuvwxyz'))
        
        # Skaičius pridedame, jei pasirinkta
        if use_numbers:
            all_modifiers.extend([str(i) for i in range(10)])
        
        # Klausimų žodžius pridedame, jei pasirinkta
        if use_questions:
            question_words = ['kodėl', 'kaip', 'ar', 'kur', 'kada', 'kas', 'kiek']
            all_modifiers.extend(question_words)
        
        # Įtraukiame ir pagrindinį raktažodį be modifikatorių
        modifier_results[""] = get_google_suggestions(seed_keyword, country_code, language)
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Ieškome pasiūlymų kiekvienam modifikatoriui
        for i, modifier in enumerate(all_modifiers):
            status_text.text(f"Ieškoma pasiūlymų modifikatoriui: '{modifier}'")
            
            if position == "po":
                query = f"{seed_keyword} {modifier}"
            else:  # "prieš"
                query = f"{modifier} {seed_keyword}"
            
            suggestions = get_google_suggestions(query, country_code, language)
            modifier_results[modifier] = suggestions
            
            # Atnaujiname progress bar
            progress_bar.progress((i + 1) / len(all_modifiers))
            
            # Trumpa pauzė, kad išvengtume blokavimo
            time.sleep(random.uniform(0.5, 1.0))
        
        # Žymime, kad paieška baigta
        status_text.text("Paieška baigta!")
        progress_bar.progress(1.0)
        
        # Kuriame DataFrame su visais rezultatais
        all_data = []
        
        # Pirma pridedame pagrindinį raktažodį be modifikatorių
        for suggestion in modifier_results[""]:
            all_data.append({
                "Modifikatorius": "(nėra)",
                "Užklausa": seed_keyword,
                "Pasiūlymas": suggestion
            })
        
        # Tada pridedame visus modifikuotus rezultatus abėcėlės tvarka
        for modifier in sorted(all_modifiers):
            for suggestion in modifier_results[modifier]:
                if position == "po":
                    query = f"{seed_keyword} {modifier}"
                else:
                    query = f"{modifier} {seed_keyword}"
                    
                all_data.append({
                    "Modifikatorius": modifier,
                    "Užklausa": query,
                    "Pasiūlymas": suggestion
                })
        
        # Konvertuojame į DataFrame
        df = pd.DataFrame(all_data)
        
        # Saugome duomenis į sesiją
        st.session_state.results_df = df
        
        # Rodome rezultatus pagal modifikatorių grupės
        st.subheader("Rezultatai pagal modifikatorius")
        
        # Pirma rodome pagrindinį raktažodį be modifikatorių
        st.markdown(f'<div class="modifier-header">Pagrindinis raktažodis: {seed_keyword}</div>', unsafe_allow_html=True)
        
        base_results = [item for item in all_data if item["Modifikatorius"] == "(nėra)"]
        base_df = pd.DataFrame(base_results)
        if not base_df.empty:
            st.table(base_df[["Pasiūlymas"]])
        else:
            st.write("Nerasta pasiūlymų.")
        
        # Tada rodome rezultatus pagal kiekvieną modifikatorių
        for modifier in sorted(all_modifiers):
            if modifier in modifier_results and modifier_results[modifier]:
                if position == "po":
                    query = f"{seed_keyword} {modifier}"
                else:
                    query = f"{modifier} {seed_keyword}"
                
                st.markdown(f'<div class="modifier-header">Modifikatorius: "{modifier}" (Užklausa: {query})</div>', unsafe_allow_html=True)
                
                modifier_data = [item for item in all_data if item["Modifikatorius"] == modifier]
                mod_df = pd.DataFrame(modifier_data)
                if not mod_df.empty:
                    st.table(mod_df[["Pasiūlymas"]])
                else:
                    st.write("Nerasta pasiūlymų.")
        
        # Rodome atsisiuntimo galimybę visam rezultatų rinkiniui
        st.subheader("Atsisiųsti visus rezultatus")
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Atsisiųsti CSV",
            data=csv,
            file_name=f"{seed_keyword}_pasiulymai.csv",
            mime="text/csv"
        )
        
        # Rodome statistiką
        st.subheader("Statistika")
        st.write(f"Iš viso unikali_ų pasiūlymų: {len(df['Pasiūlymas'].unique())}")
        st.write(f"Iš viso modifikatorių: {len(all_modifiers) + 1}")  # +1 for base keyword

else:
    st.write("Įveskite pagrindinį raktažodį kairėje pusėje ir paspauskite 'Pradėti paiešką'")
    
    # Pavyzdys ir instrukcijos
    st.subheader("Kaip naudotis įrankiu")
    st.write("""
    1. Įveskite pagrindinį raktažodį (pvz., "kava", "telefonas", "dviratis")
    2. Pasirinkite papildomus nustatymus, jei reikia:
       - Raides (a-z) - prideda raides prie jūsų raktažodžio
       - Skaičius (0-9) - prideda skaičius
       - Klausimų žodžius - prideda "kodėl", "kaip", "ar", ir t.t.
    3. Nustatykite, kur pridėti modifikatorius (prieš ar po raktažodžio)
    4. Spauskite "Pradėti paiešką" mygtuką
    5. Rezultatai bus sugrupuoti pagal modifikatorius
    6. Atsisiųskite visus rezultatus CSV formatu analizei
    
    **Pastaba**: Šį įrankį reikia paleisti lokaliai jūsų kompiuteryje, nes naršyklės saugumo apribojimai neleidžia tiesiogiai kreiptis į Google API iš Streamlit serverio.
    """)
