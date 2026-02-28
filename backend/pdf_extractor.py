import pymupdf


def extract_text_from_pdf(file_path: str) -> str:
    doc = pymupdf.open(file_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text


if __name__ == "__main__":
    import sys
    text = extract_text_from_pdf(sys.argv[1])
    print(text[:500])
