from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import os


def create_pdf_from_markdown(md_path, pdf_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        md = f.read()

    styles = getSampleStyleSheet()
    normal = styles['Normal']
    heading = styles['Heading1']

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []

    for line in md.splitlines():
        if line.startswith('# '):
            story.append(Paragraph(line[2:].strip(), heading))
            story.append(Spacer(1, 8))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:].strip(), styles['Heading2']))
            story.append(Spacer(1, 6))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:].strip(), styles['Heading3']))
            story.append(Spacer(1, 4))
        else:
            # simple conversion for lists and code blocks
            if line.startswith('- '):
                story.append(Paragraph('• ' + line[2:].strip(), normal))
            else:
                story.append(Paragraph(line or ' ', normal))
            story.append(Spacer(1, 4))

    doc.build(story)


if __name__ == '__main__':
    base = os.path.dirname(os.path.dirname(__file__))
    md = os.path.join(base, 'README.md')
    pdf = os.path.join(base, 'README.pdf')
    create_pdf_from_markdown(md, pdf)
    print('README.pdf created at', pdf)
