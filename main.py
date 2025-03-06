import os
import streamlit as st
import pandas as pd
from document_processor import extract_text
from analyzer import analyze_document
from utils import download_results, create_docx_results

# Add logging at startup
print("Starting Streamlit application...")
print(f"Environment PORT: {os.environ.get('PORT', 'Not set')}")
print(f"Current working directory: {os.getcwd()}")

# Set Streamlit configuration - must be first Streamlit command
st.set_page_config(
    page_title="Аналізатор Юридичних Документів",
    page_icon="⚖️",
    layout="wide"
)

def main():
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E3D59;
            text-align: center;
            padding: 1rem;
            margin-bottom: 2rem;
            background: linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%);
            border-radius: 10px;
        }
        .sub-header {
            color: #2E5077;
            font-size: 1.5rem;
            margin-top: 2rem;
            padding: 0.5rem;
            border-bottom: 2px solid #eee;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            background-color: #1E3D59;
            color: white;
        }
        .upload-section {
            background-color: #f8f9fa;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .analysis-options {
            background-color: #f8f9fa;
            padding: 2rem;
            border-radius: 10px;
            margin: 2rem 0;
        }
        .results-section {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 10px;
            border: 1px solid #eee;
            margin-top: 2rem;
        }
        .download-buttons {
            margin-top: 2rem;
            padding: 1rem;
            background-color: #f8f9fa;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Заголовок
    st.markdown('<h1 class="main-header">📄 Аналізатор Юридичних Документів</h1>', unsafe_allow_html=True)

    # Секція завантаження
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">Завантаження Документа</h2>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Завантажте документ формату .doc, .docx або .pdf", type=['doc', 'docx', 'pdf'])
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file:
        try:
            with st.spinner("⏳ Обробка документу..."):
                doc_text = extract_text(uploaded_file)
                st.success("✅ Документ успішно завантажено")

            # Секція налаштувань аналізу
            st.markdown('<div class="analysis-options">', unsafe_allow_html=True)
            st.markdown('<h2 class="sub-header">Налаштування Аналізу</h2>', unsafe_allow_html=True)

            # Введення запиту користувача (обов'язкове)
            query = st.text_area(
                "Введіть ваш запит для аналізу (обов'язково):",
                help="Введіть конкретні питання або аспекти, які ви хочете проаналізувати в документі.",
                height=100
            )

            # Вибір режиму аналізу
            analysis_mode = st.radio(
                "Оберіть режим аналізу:",
                ["Аналізувати тільки за запитом", "Аналізувати за запитом та категоріями"],
                key="analysis_mode"
            )

            selected_types = None
            if analysis_mode == "Аналізувати за запитом та категоріями":
                st.markdown('<h3 class="sub-header">Оберіть категорії аналізу</h3>', unsafe_allow_html=True)

                # Чекбокси для вибору типів аналізу
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    analyze_risks = st.checkbox("🔍 Аналіз Ризиків")
                with col2:
                    analyze_responsibility = st.checkbox("⚖️ Аналіз Відповідальності")
                with col3:
                    analyze_obligations = st.checkbox("📋 Договірні Зобов'язання")
                with col4:
                    analyze_compliance = st.checkbox("📜 Відповідність законодавству")
                with col5:
                    analyze_financial = st.checkbox("💰 Фінансові умови")

                # Створюємо список вибраних типів аналізу
                selected_types = []
                if analyze_risks:
                    selected_types.append("risks")
                if analyze_responsibility:
                    selected_types.append("responsibility")
                if analyze_obligations:
                    selected_types.append("obligations")
                if analyze_compliance:
                    selected_types.append("compliance")
                if analyze_financial:
                    selected_types.append("financial")

            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("🚀 Аналізувати Документ", type="primary"):
                if not query:
                    st.error("❌ Будь ласка, введіть запит для аналізу")
                    return

                if analysis_mode == "Аналізувати за запитом та категоріями" and not selected_types:
                    st.error("❌ Будь ласка, оберіть хоча б одну категорію аналізу")
                    return

                progress_placeholder = st.empty()
                progress_bar = progress_placeholder.progress(0)
                status_text = st.empty()
                error_placeholder = st.empty()

                def update_progress(progress, message):
                    try:
                        progress_bar.progress(progress)
                        status_text.text(f"⏳ {message}")
                        if "Помилка" in message:
                            error_placeholder.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"Помилка оновлення прогресу: {str(e)}")

                try:
                    analysis_results = analyze_document(
                        doc_text,
                        query,
                        selected_types,
                        progress_callback=update_progress
                    )

                    if "error" in analysis_results:
                        st.error(analysis_results["error"])
                        return

                    # Відображення результатів
                    st.markdown('<div class="results-section">', unsafe_allow_html=True)
                    st.markdown('<h2 class="sub-header">📊 Результати Аналізу</h2>', unsafe_allow_html=True)

                    if analysis_mode == "Аналізувати тільки за запитом":
                        st.markdown('<h3>📝 Загальний Аналіз</h3>', unsafe_allow_html=True)
                        st.write(analysis_results["general"])
                    else:
                        headers = {
                            "risks": "⚠️ Аналіз Ризиків",
                            "responsibility": "⚖️ Аналіз Відповідальності",
                            "obligations": "📋 Аналіз Договірних Зобов'язань",
                            "compliance": "📜 Аналіз Відповідності Законодавству",
                            "financial": "💰 Аналіз Фінансових Умов"
                        }

                        for analysis_type in selected_types:
                            st.markdown(f'<h3>{headers[analysis_type]}</h3>', unsafe_allow_html=True)
                            st.write(analysis_results[analysis_type])

                    st.markdown('</div>', unsafe_allow_html=True)

                    # Кнопки завантаження
                    st.markdown('<div class="download-buttons">', unsafe_allow_html=True)
                    col1, col2 = st.columns(2)

                    with col1:
                        st.download_button(
                            label="📄 Завантажити у форматі TXT",
                            data=download_results(analysis_results, selected_types),
                            file_name="результати_аналізу.txt",
                            mime="text/plain"
                        )

                    with col2:
                        docx_bytes = create_docx_results(analysis_results, selected_types).getvalue()
                        st.download_button(
                            label="📑 Завантажити у форматі DOCX",
                            data=docx_bytes,
                            file_name="результати_аналізу.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    st.markdown('</div>', unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Критична помилка під час аналізу: {str(e)}")
                finally:
                    progress_placeholder.empty()
                    status_text.empty()

        except Exception as e:
            st.error(f"❌ Помилка при обробці файлу: {str(e)}")

    else:
        st.info("ℹ️ Будь ласка, завантажте документ формату .doc, .docx або .pdf для початку аналізу.")
        st.markdown("""
        ### 📌 Як користуватися аналізатором:
        1. 📁 Завантажте ваш юридичний документ (формат .doc, .docx або .pdf)
        2. ✍️ Введіть ваш специфічний запит для аналізу (обов'язково)
        3. 🔄 Оберіть режим аналізу:
           - Аналіз тільки за запитом
           - Аналіз за запитом та категоріями
        4. ☑️ Якщо потрібно, оберіть категорії для аналізу
        5. 🚀 Натисніть 'Аналізувати Документ' для початку аналізу
        6. 💾 Завантажте результати у зручному форматі (TXT або DOCX)
        """)

if __name__ == "__main__":
    try:
        print("Initializing application...")
        main()
        print("Application started successfully")
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        raise