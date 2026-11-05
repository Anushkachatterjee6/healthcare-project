"""Restructure the existing final deck into a 30-slide evidence-preserving edition."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import fitz
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'deliverables'
SOURCE=OUT/'Healthcare_Project_Presentation_Final.pptx'; TARGET=OUT/'Healthcare_Project_Presentation_30_Slides.pptx'
NAVY=RGBColor(10,39,62); TEAL=RGBColor(0,123,122); INK=RGBColor(30,47,57); MUTED=RGBColor(83,101,109)

def text(slide,value,x,y,w,h,size=12,color=INK,bold=False,align=None):
    shape=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=shape.text_frame; tf.clear(); tf.word_wrap=True
    p=tf.paragraphs[0];p.text=value;p.font.name='Aptos';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=color
    if align is not None:p.alignment=align

def add_images(source,target,slots):
    imgs=[sh for sh in source.shapes if sh.shape_type==13]
    for sh,(x,y,w,h) in zip(imgs,slots): target.shapes.add_picture(BytesIO(sh.image.blob),Inches(x),Inches(y),width=Inches(w),height=Inches(h))

prs=Presentation(SOURCE)
# Original one-based slide numbers. Move unique visual evidence before deletion.
# Slide 10 Dataset Explorer image -> slide 5 frontend overview (three modules in one visual row).
add_images(prs.slides[9],prs.slides[4],[(.75,4.25,3.7,1.45)])
text(prs.slides[4],'Dataset Intelligence: inventory, case details and true local MRI availability.',.75,5.72,3.7,.25,9,MUTED,False,PP_ALIGN.CENTER)
# Slide 13's T4 reference overlay/compression -> slide 12 as a balanced 2x2 evidence grid.
add_images(prs.slides[12],prs.slides[11],[(6.55,4.25,2.65,1.75),(9.55,4.25,2.65,1.75)])
text(prs.slides[11],'Reference-mask overlay',6.55,6.08,2.65,.2,9,MUTED,False,PP_ALIGN.CENTER)
text(prs.slides[11],'JPEG compression comparison',9.55,6.08,2.65,.2,9,MUTED,False,PP_ALIGN.CENTER)
# Loss chart becomes the second panel on training slide.
for sh in [x for x in prs.slides[18].shapes if x.shape_type==13]:
    prs.slides[18].shapes.add_picture(BytesIO(sh.image.blob),Inches(9.45),Inches(3.65),width=Inches(2.8),height=Inches(2.5))
text(prs.slides[18],'Training accuracy',6.55,6.25,2.8,.2,9,MUTED,False,PP_ALIGN.CENTER)
text(prs.slides[18],'Training / validation loss',9.45,6.25,2.8,.2,9,MUTED,False,PP_ALIGN.CENTER)
# ROC chart becomes the second panel on confusion-matrix slide.
for sh in [x for x in prs.slides[21].shapes if x.shape_type==13]:
    prs.slides[20].shapes.add_picture(BytesIO(sh.image.blob),Inches(9.45),Inches(3.65),width=Inches(2.8),height=Inches(2.5))
text(prs.slides[20],'Confusion matrix',6.55,6.25,2.8,.2,9,MUTED,False,PP_ALIGN.CENTER)
text(prs.slides[20],'ROC curve (AUC = 0.9384)',9.45,6.25,2.8,.2,9,MUTED,False,PP_ALIGN.CENTER)
# Use a subtitle replacement and compact technical callout to retain dropped CNN configuration information.
for sh in prs.slides[16].shapes:
    if sh.has_text_frame and sh.text.startswith('T5 CNN: layer-by-layer architecture'):
        sh.text_frame.paragraphs[0].text='T5 CNN: architecture and experiment configuration'
text(prs.slides[16],'Input 128×128×1 FLAIR · Adam + binary cross-entropy · fixed seed 42 · 12 requested epochs · class weights 1.1786 / 0.8684',.65,5.15,11.8,.30,11,TEAL,True,PP_ALIGN.CENTER)
# Retain project purpose, architecture, workflow, reporting, verification and future scope in retained title/conclusion slides.
text(prs.slides[0],'Objective: reproducible MRI inspection, image analysis and transparent experimental slice-level CNN inference.',.62,6.22,11.9,.25,11,TEAL,False,PP_ALIGN.CENTER)
text(prs.slides[3],'Data flow: validated local FLAIR/SEG → shared preprocessing → algorithm/checkpoint → compact PNG/metrics response → research UI.',.72,5.22,11.6,.30,11,TEAL,True,PP_ALIGN.CENTER)
text(prs.slides[37],'Report outputs retain actual input metadata, previews, returned slice probabilities, threshold, duration and research-only limitations.',.7,5.30,11.7,.32,11,TEAL,True,PP_ALIGN.CENTER)
text(prs.slides[43],'Future work: larger multi-centre cohorts, patient-level independent validation, calibration and governance before clinical translation.',.65,5.42,12,.30,11,TEAL,True,PP_ALIGN.CENTER)
# Delete selected redundant/merged slides in descending order. Unique visual evidence was moved above.
remove=[43,41,40,39,37,25,22,20,18,13,10,8,3,2]
for one_based in remove:
    idx=one_based-1; xml=prs.slides._sldIdLst[idx]; rel=xml.rId; prs.part.drop_rel(rel); del prs.slides._sldIdLst[idx]
assert len(prs.slides)==30
# Refresh footer page numbering consistently.
for n,slide in enumerate(prs.slides,1):
    for sh in slide.shapes:
        if sh.has_text_frame and 'Healthcare project evidence deck' in sh.text:
            sh.text_frame.paragraphs[0].text=f'{n:02d} | Healthcare project evidence deck'
prs.save(TARGET)

# PDF: retain the 30 selected original pages in the same order; final PPTX visual moves are internal layout enhancements.
src_pdf=fitz.open(OUT/'Healthcare_Project_Presentation_Final.pdf')
deleted=set(remove); out_pdf=fitz.open()
for i in range(1,len(src_pdf)+1):
    if i not in deleted: out_pdf.insert_pdf(src_pdf,from_page=i-1,to_page=i-1)
# Apply the same four evidence consolidations to the matching PDF pages.
assets=OUT/'Presentation_Assets'
def pdf_image(page_no, filename, rect, caption):
    page=out_pdf[page_no-1]; page.insert_image(fitz.Rect(*rect),filename=str(assets/filename),keep_proportion=True,overlay=True)
    page.insert_text((rect[0],rect[3]+10),caption,fontsize=6,color=(.32,.40,.43))
pdf_image(2,'s1.png',(47,337,281,452),'Dataset Intelligence: inventory and case details')
pdf_image(7,'notebook_nb23_0.png',(413,337,580,476),'Reference-mask overlay')
pdf_image(7,'notebook_nb25_1.png',(603,337,770,476),'JPEG compression comparison')
pdf_image(12,'training_loss.png',(597,290,774,488),'Training / validation loss')
pdf_image(13,'roc_curve.png',(597,290,774,488),'ROC curve (AUC = 0.9384)')
out_pdf.save(OUT/'Healthcare_Project_Presentation_30_Slides.pdf')
print('slides',len(prs.slides),'pages',len(out_pdf))
