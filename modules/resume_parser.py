import pdfplumber

def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extracts text from a PDF uploaded via Streamlit.
    Returns combined text from all pages.
    """
    text_parts = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
    return "\n".join(text_parts).strip()
