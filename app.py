import streamlit as st
import pdfplumber
import spacy
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="Analizador de CVs", page_icon="📄")

@st.cache_resource
def load_nlp():
    return spacy.load("es_core_news_md")

nlp = load_nlp()

def extract_text_from_pdf(file):
    try:
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
            if not text.strip():
                st.warning("El PDF parece estar vacío o ser una imagen.")
                return None
            return text.strip()
    except Exception as e:
        st.error(f"Error al leer el PDF: {e}")
        return None

def calculate_match(text_cv, text_job):
    try:
        content = [text_cv, text_job]
        cv = CountVectorizer()
        count_matrix = cv.fit_transform(content)
        similarity_matrix = cosine_similarity(count_matrix)
        return similarity_matrix[0][1] * 100
    except Exception as e:
        return 0

def get_clean_keywords(doc):
    return set([
        token.lemma_.lower() 
        for token in doc 
        if token.pos_ in ["NOUN", "PROPN"] 
        and not token.is_stop 
        and len(token.text) > 2
    ])

def lemmas_to_words(lemmas_set, doc):
    words = []
    for lemma in lemmas_set:
        for token in doc:
            if token.lemma_.lower() == lemma:
                words.append(token.text.lower())
                break
    return sorted(list(set(words)))

st.title("Analizador Inteligente de CVs")
st.markdown("""
Esta herramienta utiliza **Procesamiento de Lenguaje Natural (NLP)** para comparar tu perfil con una oferta laboral.
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Tu Curriculum (PDF)")
    uploaded_file = st.file_uploader("Sube tu CV", type=["pdf"])

with col2:
    st.subheader("2. Descripción de la Oferta")
    job_description = st.text_area("Pega aquí los requisitos del puesto", height=200, placeholder="Ej: Buscamos un desarrollador con experiencia en Python, SQL...")

if st.button("Iniciar Análisis"):
    if uploaded_file and job_description.strip():
        with st.spinner("Analizando semántica y keywords..."):
            cv_text = extract_text_from_pdf(uploaded_file)
            
            if cv_text:
                doc_cv = nlp(cv_text.lower())
                doc_job = nlp(job_description.lower())
                
                score = calculate_match(cv_text.lower(), job_description.lower())
                
                st.divider()
                st.header(f"Match Score: {score:.2f}%")
                st.progress(score / 100)
                
                if score > 70:
                    st.success("Coincidencia alta. Tu perfil se ajusta bien a esta oferta.")
                elif score > 40:
                    st.warning("Coincidencia media. Considera optimizar tus keywords.")
                else:
                    st.error("Coincidencia baja. Tu CV podría ser descartado por sistemas automáticos (ATS).")

                keywords_job_lemmas = get_clean_keywords(doc_job)
                keywords_cv_lemmas = get_clean_keywords(doc_cv)
                
                missing_lemmas = keywords_job_lemmas - keywords_cv_lemmas
                found_lemmas = keywords_job_lemmas & keywords_cv_lemmas
                
                display_found = lemmas_to_words(found_lemmas, doc_job)
                display_missing = lemmas_to_words(missing_lemmas, doc_job)
                
                st.divider()
                res_col1, res_col2 = st.columns(2)
                
                with res_col1:
                    st.subheader("Keywords encontradas")
                    if display_found:
                        st.write(", ".join(display_found))
                    else:
                        st.write("No se detectaron coincidencias claras.")

                with res_col2:
                    st.subheader("Keywords faltantes")
                    if display_missing:
                        st.info("Considera incluir algunos de estos términos en tu CV:")
                        st.write(", ".join(display_missing))
                    else:
                        st.success("Tu CV cubre todas las palabras clave de la oferta.")
    else:

        st.error("Por favor, asegúrate de haber subido el PDF y pegado la descripción.")
