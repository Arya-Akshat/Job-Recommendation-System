from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

OUTPUT_PATH = 'data/test_resume.pdf'
text_lines = [
    'John Doe',
    'Experienced Software Engineer',
    'Skills: Python, Django, SQL, AWS, C++, Node.js, React'
]

c = canvas.Canvas(OUTPUT_PATH, pagesize=letter)
width, height = letter
y = height - 72
for line in text_lines:
    c.setFont('Helvetica', 12)
    c.drawString(72, y, line)
    y -= 18
c.save()
print(f'Wrote {OUTPUT_PATH}')
