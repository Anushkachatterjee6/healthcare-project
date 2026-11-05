"""Direct formatting pass over the existing 30-slide deck using the uploaded deck's hierarchy."""
from io import BytesIO
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE as ST
from pptx.enum.text import PP_ALIGN

OUT=Path(__file__).resolve().parents[1]/'deliverables'; path=OUT/'Healthcare_Project_Presentation_30_Slides.pptx'
prs=Presentation(path); W,H=13.333,7.5
NAVY=RGBColor(10,39,62); TEAL=RGBColor(0,123,122); OFF=RGBColor(250,252,252); INK=RGBColor(30,47,57); GREY=RGBColor(83,101,109)

def fit(shape,x,y,w,h):
    im=Image.open(BytesIO(shape.image.blob)); ratio=im.width/im.height
    if w/h>ratio: nw=h*ratio; nh=h; nx=x+(w-nw)/2; ny=y
    else: nw=w; nh=w/ratio; nx=x; ny=y+(h-nh)/2
    shape.left,shape.top,shape.width,shape.height=Inches(nx),Inches(ny),Inches(nw),Inches(nh)

for n,slide in enumerate(prs.slides,1):
    # professional light canvas and navy top rule, retaining the existing teal identity rail
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb=OFF
    rule=slide.shapes.add_shape(ST.RECTANGLE,Inches(.18),0,Inches(W-.18),Inches(.08)); rule.fill.solid();rule.fill.fore_color.rgb=NAVY;rule.line.fill.background()
    label=slide.shapes.add_textbox(Inches(.52),Inches(.18),Inches(3.7),Inches(.18));p=label.text_frame.paragraphs[0];p.text='BRAIN + MRI RESEARCH PLATFORM';p.font.name='Aptos Display';p.font.size=Pt(8);p.font.bold=True;p.font.color.rgb=TEAL
    # normalize existing text hierarchy
    text_shapes=[sh for sh in slide.shapes if sh.has_text_frame and sh.text.strip()]
    for sh in text_shapes:
        first=sh.text_frame.paragraphs[0]
        for para in sh.text_frame.paragraphs:
            para.font.name='Aptos'
        if 'Healthcare project evidence deck' in sh.text:
            first.text=f'{n:02d}  |  BRAIN + MRI RESEARCH PLATFORM';first.font.size=Pt(8);first.font.color.rgb=TEAL
        elif 'Research-only' in sh.text:
            first.font.size=Pt(8);first.font.color.rgb=TEAL
    pics=[sh for sh in slide.shapes if sh.shape_type==13]
    # one clear evidence panel per slide; use wide area for UI / chart screenshots
    if len(pics)==1:
        fit(pics[0],.72,3.0,11.9,3.45)
    elif len(pics)==2:
        fit(pics[0],6.45,1.72,2.85,4.65); fit(pics[1],9.62,1.72,2.85,4.65)
    elif len(pics)>=3:
        slots=[(.72,4.1,3.7,1.45),(4.78,4.1,3.7,1.45),(8.84,4.1,3.7,1.45)]
        for pic,slot in zip(pics,slots):fit(pic,*slot)
    # Add small, non-overlapping visual caption bar to evidence slides.
    if pics:
        cap=slide.shapes.add_textbox(Inches(.72),Inches(6.55),Inches(11.9),Inches(.2));p=cap.text_frame.paragraphs[0];p.text='Actual project evidence · source images, notebook output or saved model artifact';p.font.name='Aptos';p.font.size=Pt(8);p.font.color.rgb=GREY;p.alignment=PP_ALIGN.CENTER
prs.save(path)
print('refined',len(prs.slides),'slides')
