import pdfplumber

file_path = "uploads/b5fa769e-6d8b-4549-bd2a-011bbb814b2a.pdf"

print("--- TESTING DEFAULT EXTRACT ---")
with pdfplumber.open(file_path) as pdf:
    text = pdf.pages[1].extract_text() # Page 2 (0-indexed page 1)
    print("DEFAULT:")
    print(text[:300])

print("\n--- TESTING x_tolerance = 2 ---")
with pdfplumber.open(file_path) as pdf:
    text = pdf.pages[1].extract_text(x_tolerance=2)
    print("x_tolerance=2:")
    print(text[:300])

print("\n--- TESTING x_tolerance = 1.5 ---")
with pdfplumber.open(file_path) as pdf:
    text = pdf.pages[1].extract_text(x_tolerance=1.5)
    print("x_tolerance=1.5:")
    print(text[:300])

print("\n--- TESTING x_tolerance = 1 ---")
with pdfplumber.open(file_path) as pdf:
    text = pdf.pages[1].extract_text(x_tolerance=1)
    print("x_tolerance=1:")
    print(text[:300])

print("\n--- TESTING layout=True ---")
with pdfplumber.open(file_path) as pdf:
    try:
        text = pdf.pages[1].extract_text(layout=True)
        print("layout=True:")
        print(text[:300])
    except Exception as e:
        print("layout=True error:", e)
