import os
from pathlib import Path
from fpdf import FPDF

# Output locations
root = Path("/home/master/Downloads/test_search")
os.makedirs(root, exist_ok=True)

# Define files: (filename, content)
files = [
    ("shopping_list.txt", "Milk\nBread\nEggs\nCheese"),
    ("my_books.txt", "1984 by George Orwell\nBrave New World\nDune\nSapiens"),
    ("vacation_ideas.pdf", "Plan for Italy\nVisit Rome, Venice, Florence\nTry gelato!"),
    ("project_notes.txt", "Tasks:\n- Refactor file search\n- Test fuzzy match\n- Log output"),
    ("movie_quotes.pdf", "May the Force be with you.\nI'll be back.\nWhy so serious?")
]

# Create text and PDF files
for name, content in files:
    path = root / name
    if name.endswith(".txt"):
        with open(path, "w") as f:
            f.write(content)
    elif name.endswith(".pdf"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in content.splitlines():
            pdf.cell(200, 10, txt=line, ln=True)
        pdf.output(str(path))

print(f"✅ Created {len(files)} files in {root}")
