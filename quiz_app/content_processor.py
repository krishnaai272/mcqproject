import PyPDF2

def _get_text_from_txt(file_path):
    """Reads text from a .txt file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def _get_text_from_pdf(file_path):
    """Extracts text from a .pdf file."""
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text

def process_document(file_path: str) -> str | None:
    """
    Processes a document based on its file extension and returns the text content.
    """
    try:
        if file_path.lower().endswith('.txt'):
            return _get_text_from_txt(file_path)
        elif file_path.lower().endswith('.pdf'):
            return _get_text_from_pdf(file_path)
        else:
            print(f"Error: Unsupported file format for '{file_path}'. Please use .txt or .pdf.")
            return None
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while processing the document: {e}")
        return None