"""Generate an editable, evidence-led 42-slide PowerPoint and matching PDF."""
from pathlib import Path
import base64, json, shutil, textwrap
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE as ST
from pptx.enum.text import PP_ALIGN
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'deliverables'; AS=OUT/'Presentation_Assets'; OUT.mkdir(exist_ok=True); AS.mkdir(exist_ok=True)
NAVY=RGBColor(10,39,62); TEAL=RGBColor(0,123,122); SKY=RGBColor(68,145,169); PALE=RGBColor(239,247,246); INK=RGBColor(30,47,57); MUTED=RGBColor(83,101,109)
src={'accuracy':'models/training_accuracy.png','loss':'models/training_loss.png','roc':'models/roc_curve.png','confusion':'models/confusion_matrix.png','cnn':'artifacts/cnn_previews.png','t4':'artifacts/visual_T4_0.png','t6':'artifacts/visual_T6_5.png','t13':'artifacts/visual_T13_0.png','t14':'artifacts/visual_T14_2.png','t14b':'artifacts/visual_T14_3.png','forecast':'artifacts/forecast_preview.png','s1':'s1.png','s2':'s2.png','s3':'s3.png','s4':'s4.png','s5':'s5.png','s6':'s6.png','t7screen':'t7.png','t8screen':'t8.png','t9screen':'t9.png','t10screen':'t10.png','t10cluster':'t10_2.png','t11screen':'t11.png','t12screen':'t12.png','t13screen':'t13.png','t14screen':'t14.png','t15screen':'t15.png','uploadscreen':'real time work.png'}
A={}
for k,p in src.items():
 p=ROOT/p
 if p.exists(): shutil.copy2(p,AS/p.name); A[k]=str(AS/p.name)
nb=json.loads((ROOT/'HER_Biomedical_Image_Tutorials_T1_T6.ipynb').read_text(encoding='utf-8'))
for ci,c in enumerate(nb['cells']):
 if ci not in {8,11,19,21,23,25,28,30,42,46,48,49,51,52,53,55}: continue
 for oi,o in enumerate(c.get('outputs',[])):
  raw=o.get('data',{}).get('image/png')
  if raw:
   key=f'nb{ci}_{oi}'; f=AS/f'notebook_{key}.png'; f.write_bytes(base64.b64decode(''.join(raw) if isinstance(raw,list) else raw)); A[key]=str(f)
E=json.loads((ROOT/'models/evaluation_report.json').read_text()); M=json.loads((ROOT/'models/model_metadata.json').read_text())
def s(t,sub,b=(),im=(),kind='std',table=(),cap=''): return dict(t=t,sub=sub,b=list(b),im=list(im),kind=kind,table=list(table),cap=cap)
slides=[
s('Brain Tumor Detection Using MRI Images','Brain + MRI Research Platform | Academic project presentation',['Evidence-led biomedical imaging, tutorial delivery and experimental AI workflow','Research-only: no clinical diagnosis or patient-level claim'],['cnn'],'title','', 'Actual CNN preview artifact.'),
s('Presentation evidence audit','Revision checklist applied to the earlier sparse 33-slide deck.',['Expanded to technical diagrams, tables and source-backed metrics.','Embedded saved plots, original notebook outputs and project visualizations.','Expanded CNN to eleven methodology/evidence slides.','Covered T1–T15 with aim, inputs, processing, output and limitation.'],kind='check'),
s('Problem definition','MRI analysis requires reproducible processing before output can be interpreted.',['MRI volumes may include invalid values, intensity variation and absent modalities.','Supplied segmentation is reference ground truth—not a model prediction.','Small local data supports teaching/pipeline validation, not clinical validation.'],kind='flow'),
s('Platform architecture','Independent browser modules reuse validated MRI and analytics utilities.',['Browser: Dashboard, Tutorial Lab, Image Analysis Studio, MRI Research Studio.','FastAPI: validation, data-URL image serialization, case discovery and reporting.','Core: NIfTI I/O, preprocessing, SIFT/RANSAC, analytics and CNN inference.'],kind='arch'),
s('Frontend modules: contextual research workspace','Actual application screens show Dataset Intelligence and MRI Research Studio.',['Dataset Intelligence provides local case selection, modality context and actual slice preview.','MRI Research Studio separates workflow selection from case-specific analysis and upload inference.','The visible Back action follows contextual module hierarchy rather than always returning to Dashboard.'],['s2','s3'],'two',cap='Actual frontend screenshots: Dataset Intelligence and MRI Research Studio.'),
s('Data lineage and safeguards','Every visible result has a traceable source and status.',['Local FLAIR/SEG → validate → preprocess → algorithm/checkpoint → PNG/metrics → UI.','Missing masks stay missing; they are never converted to negative labels.','The persistent checkpoint is reused; request handling never trains a new model.'],kind='flow'),
s('Dataset audit: local BraTS2020 evidence','Actual findings from CNN_DATASET_AUDIT.md.',['8 case folders; FLAIR 8/8; SEG 6/8. Two unsegmented cases are excluded from supervision.','Six FLAIR/SEG pairs are 240 × 240 × 155. Labels 0,1,2,3; y=1 iff mask > 0.','All eligible labelled slices: 798 (355 negative, 443 positive).'],['nb8_0'],'std',cap='Original notebook output: local MRI middle slice.'),
s('MRI preprocessing contract','The exact branch is shared by training, validation, test and upload inference.',['Clean NaN/Inf → 160 × 160 centre crop (when applicable) → per-slice min–max.','x′ = (x − min(x)) / (max(x) − min(x)); resize to 128 × 128; one FLAIR channel.','This contract is implemented in her_core/cnn.py, not recreated per endpoint.'],['nb11_1'],'std',cap='Original notebook output: original, standardized, normalized.'),
s('Implemented application analysis modules','Frontend outputs demonstrate that preprocessing and radiomics are separate functional modules.',['Preprocessing Laboratory renders original, cleaned, normalized and contrast-enhanced MRI stages.','Radiomics Lab selects a case/modality and exposes feature-analysis actions backed by actual local data.','These modules are analysis tools; they do not report clinical diagnoses.'],['s4','s5'],'two',cap='Actual frontend screenshots: Preprocessing Laboratory and Radiomics Lab.'),
s('MRI Workspace and Dataset Explorer','Application modules render data rather than raw JSON.',['Case/modality/slice controls call the validated slice endpoint and return compact PNG data URLs.','Brightness, contrast, zoom and reference-mask overlay apply only where the actual input exists.','Dataset Explorer displays case inventory, modality availability, slice counts and integrity state.'],['s1','t6'],'two',cap='Actual Dataset Intelligence interface and multimodal/reference-mask output.'),
s('T1–T3: inspection, preprocessing and data quality','Foundational workflows establish data conditions before analysis.',['T1: discover local cases/modalities and show a middle slice.','T2: clean invalid values; compare z-score and min–max transformations.','T3: report missing modalities/duplicates without destructive assumptions.'],['nb8_0','nb11_1'],'two','', 'Original notebook evidence for T1/T2.'),
s('T4: biomedical image analysis','Aim: make enhancement and quality operations inspectable.',['Input: local MRI slice. CLAHE enhancement and bilateral denoising are displayed side by side.','Interpretation: altered contrast is presentation support—not tumour segmentation/diagnosis.','Implementation: notebook operations and reusable preprocessing helpers.'],['nb19_0','nb21_0'],'two',cap='Actual T4 notebook outputs: enhancement and restoration.'),
s('T4: reference overlay and compression','Reference masks remain distinct from processing effects.',['Same-case FLAIR + supplied SEG are overlaid as reference evidence.','JPEG comparison demonstrates storage/artefact trade-offs for teaching.','No predicted segmentation mask is claimed.'],['nb23_0','nb25_1'],'two',cap='Actual T4 overlay and compression outputs.'),
s('T4: intensity and 3-D context','Additional notebook evidence links slice-level work to volume context.',['Histogram uses non-background MRI intensity values, making intensity distribution explicit.','3-D threshold display is a visualisation of high-intensity voxels, not a tumour segmentation.','These figures support inspection before feature extraction or classification.'],['nb52_0','nb55_0'],'two',cap='Original notebook intensity and 3-D visualisation outputs.'),
s('T5: SIFT + RANSAC','Aim: robust correspondence evidence between nearby MRI slices.',['SIFT detects scale-invariant keypoints and descriptors from normalized intensity.','Descriptor matching proposes candidates; RANSAC estimates a robust transform/rejects outliers.','Output supports image correspondence analysis, not tumour presence.'],['nb28_1','nb30_1'],'two',cap='Actual T5 keypoint and RANSAC-match outputs.'),
s('T5 CNN: target and leakage control','Binary slice labels derive only from reference-mask pixels.',['y = 1 if any(mask > 0), otherwise 0; unlabelled cases are excluded.','Case separation: train 4 cases/132 slices; validation 1/35; held-out test 1/35.','No patient contributes slices to more than one partition.'],kind='split'),
s('T5 CNN: layer-by-layer architecture','Saved model brats-flair-slice-cnn-v1 | input 128 × 128 × 1.',['Conv2D(32,3×3,ReLU,same) + pool → Conv2D(64) + pool → Conv2D(128) + pool.','Flatten → Dense(128, ReLU) → Dropout(0.5) → Dense(1, sigmoid).','Sigmoid is model-estimated P(tumour slice); evaluation threshold = 0.50.'],kind='cnn'),
s('T5 CNN: experiment configuration','Persistent run from scripts/train_brain_tumor_cnn.py.',['Fixed seed 42; 12 requested epochs; best validation-loss checkpoint persisted.','Training-only weights: no-tumour 1.1786; tumour 0.8684.','Evenly spaced cap: 40 slices/case for the practical training run.'],kind='table',table=[['Partition','Cases','Slices','Role'],['Train','457,449,218,206','132','Optimisation'],['Validation','306','35','Selection'],['Held-out test','318','35','Experimental test']]),
s('T5 CNN: training and validation accuracy','Actual persisted history; 11 recorded epochs.',['Training accuracy: 0.7197 → 0.9848. Validation ends at 0.8571.','The gap is a small-cohort caution, not deployment evidence.','Validation is for model selection; held-out reporting is separate.'],['accuracy'],'std',cap='models/training_accuracy.png'),
s('T5 CNN: training and validation loss','Actual persisted loss history; checkpoint selected by validation loss.',['Training loss: 0.5823 → 0.0772. Validation loss is non-monotonic and ends at 0.4496.','The curves motivate independent patient-level evaluation; they do not prove generalisation.'],['loss'],'std',cap='models/training_loss.png'),
s('T5 CNN: held-out confusion matrix','Actual one-patient held-out test: 35 slices.',['[[11,1],[12,11]] = 11 TN, 1 FP, 12 FN, 11 TP.','Tumour recall = 0.4783: 12/23 positive slices missed at threshold 0.50.','Negative slice result cannot rule out tumour.'],['confusion'],'std',cap='models/confusion_matrix.png'),
s('T5 CNN: ROC and threshold interpretation','Score ranking and thresholded classification answer different questions.',['Held-out ROC-AUC = 0.9384; thresholded accuracy = 0.6286; tumour recall = 0.4783.','High AUC can coexist with modest recall at one fixed threshold.','One held-out patient means neither statistic establishes clinical calibration.'],['roc'],'std',cap='models/roc_curve.png'),
s('T5 CNN: classification report','Actual held-out metrics (35 slices).',kind='table',table=[['Class','Precision','Recall','F1','Support'],['No Tumor','0.4783','0.9167','0.6286','12'],['Tumor Present','0.9167','0.4783','0.6286','23'],['Macro average','0.6975','0.6975','0.6286','35'],['Weighted average','0.7664','0.6286','0.6286','35']]),
s('T5 CNN: actual inference visualization','Notebook evidence demonstrates genuine preprocessed-slice predictions.',['UI renders original MRI and exact 128 × 128 model input.','Tutorial data can show actual label separately; arbitrary uploads do not have ground truth.','Probabilities are model estimates, never diagnostic certainty.'],['nb48_0','nb49_0'],'two',cap='Original notebook CNN prediction outputs.'),
s('T5 CNN: result interpretation','Model output is technically useful only within its documented scope.',['A sigmoid probability ranks the uploaded/preprocessed slice under the trained experimental model.','Thresholding at 0.50 creates a class label; it does not transform probability into clinical certainty.','False negatives in the held-out matrix and one-patient test design require a conservative interpretation.'],['cnn','confusion'],'two',cap='Actual integration preview and held-out confusion-matrix evidence.'),
s('T6: multimodal MRI visualization','Aim: compare compatible modalities and supplied segmentation context.',['Same-case volumes are rendered with consistent orientation.','SEG pane is supplied reference where present—not CNN output.','Modality comparison precedes downstream interpretation.'],['nb51_0','t6'],'two',cap='Actual T6 notebook/project visualizations.'),
s('T7: MRI review queue','Aim: operational case review from actual data availability.',['Input: discovered local cases plus FLAIR/SEG availability.','Output: review state and completeness status; T7–T9 do not request synthetic text examples.','Availability is operational metadata, not a medical finding.'],['t7screen'],'std',cap='Actual T7 availability/completeness output.'),
s('T8: healthcare data analysis','Aim: inspect dataset inventory and supplied tumour-burden information.',['Inputs: local metadata and SEG only where provided.','Processing: counts, availability checks and volume-derived summaries.','Small local summaries are repository descriptions—not epidemiological estimates.'],['t8screen'],'std',cap='Actual T8 inventory and distribution dashboard.'),
s('T9: feature exploration','Aim: derive MRI features for descriptive statistics.',['Normalized images/volumes yield intensity and simple morphology-derived exploration.','Associations are descriptive; local cohort size limits inference and generalisation.'],['t9screen'],'std',cap='Actual T9 feature-correlation and availability output.'),
s('T10: text classification','A synthetic teaching-report workflow, distinct from MRI imaging.',['Supported synthetic CSV examples are restricted to T10–T12.','TF–IDF features feed logistic classification and class-oriented tutorial outputs.','No real patient reports, clinical NLP accuracy or diagnosis is claimed.'],['t10screen'],'std',cap='Actual T10 synthetic-text classification confusion matrix.'),
s('T10: clustering','Clustering remains independent from text classification.',['TF–IDF vectors feed K-Means; cluster IDs describe lexical similarity, not diagnoses.','Separate UI controls preserve the difference between supervised and unsupervised workflows.'],['t10cluster'],'std',cap='Actual T10 clustering distribution and PCA projection.'),
s('T11: entity extraction','Transparent lexicon and measurement-rule extraction.',['Synthetic text is processed with term and pattern matching.','Output is structured teaching evidence, not a trained clinical NER system.'],['t11screen'],'std',cap='Actual T11 extracted-entity output.'),
s('T12: ranking and disambiguation','TF–IDF cosine ranking of synthetic report passages.',['Query/corpus → vectorisation → cosine similarity → ranked result with ambiguity context.','This demonstrates retrieval mechanics, not clinical decision support.'],['t12screen'],'std',cap='Actual T12 ranking and word-overlap output.'),
s('T13: PCA and t-SNE','Aim: lower-dimensional exploratory projections of standardised MRI features.',['PCA reports linear projection/explained-variance evidence; t-SNE offers nonlinear neighbourhoods.','Visual clusters are hypothesis-generating, not validated biological subtypes.'],['t13screen'],'std',cap='Actual T13 PCA, t-SNE and feature-space output.'),
s('T14: tumour-burden associations','Aim: exploratory associations with supplied reference-mask burden.',['Feature summaries are paired with SEG-derived burden only when a reference mask exists.','Association plots are non-causal and missing masks remain missing.'],['t14screen'],'std',cap='Actual T14 association/correlation output.'),
s('T15: held-out regression','Aim: estimate segmentation-derived tumour burden continuously.',['Task is regression, not tumour/no-tumour classification.','Prediction-versus-reference visualisation requires regression metrics—not an invalid ROC claim.','Local size limits confidence in generalisation.'],['t15screen'],'std',cap='Actual T15 held-out regression output.'),
s('Image Analysis Studio','SIFT/RANSAC and CNN cards render actual serialized image results.',['Controls → endpoint → preprocess/model or feature algorithm → PNG/JPEG data URL → responsive cards.','CNN cards present input, label only if available, probability/class and saved evaluation evidence.','SIFT/RANSAC remains an independent working visual workflow.'],['t4','cnn'],'two',cap='Actual project visual assets.'),
s('MRI Upload & AI Analysis','Persistent checkpoint inference is a separate application workflow.',['Compatible PNG/JPEG/NIfTI FLAIR inputs are server-validated (30 MB maximum).','L/LA/RGB/RGBA images normalise safely to one grayscale channel, then reuse the unchanged FLAIR preprocessing.','Response includes previews, slice probabilities/classes, duration and limitations.'],['uploadscreen'],'std',cap='Actual MRI Upload & AI Analysis inference interface.'),
s('Research reporting and reproducibility','Reports retain actual response data and limitations.',['HTML/PDF reports contain metadata, model version, preprocessing, previews and returned slice predictions.','No dataset reference mask is presented as an upload prediction; no synthetic metrics are generated.','Artifacts: checkpoint, metadata, history, evaluation JSON, curves, ROC and matrix.'],kind='report'),
s('Implementation traceability','Source files map directly to visible project behaviour.',['`her_core/cnn.py`: exact preprocessing branch and saved CNN architecture.','`scripts/train_brain_tumor_cnn.py`: patient-level experiment and persisted artifacts.','`backend/main.py` / `backend/tutorials.py`: validated API routes; `frontend/*`: response rendering and contextual navigation.'],kind='workflow'),
s('Implementation verification','Automated checks previously completed against this project.',['Python: 21 passed (39 subtests) in the recorded project verification run.','Frontend integration covered T1–T15 and CNN visualization wiring; app integration checks completed.','This delivery validates asset presence, PPTX package slide count and all rendered PDF pages.'],kind='check'),
s('Limitations and safeguards','Transparency is a core technical requirement.',['Six labelled cases and one held-out test patient: experimental slice-level evidence only.','No patient diagnosis, segmentation prediction, clinical confidence or arbitrary-upload accuracy is asserted.','Raw BraTS data remains local/authorized; uploads are validated and not publicly exposed.'],kind='limits'),
s('Future work','Substantive improvements require new data and validation.',['Multi-centre cohorts, prospective patient-level splits and independent test sets.','Calibration/threshold selection within documented use cases and uncertainty analysis.','Segmentation only after genuine segmentation-specific training/validation.'],kind='future'),
s('Conclusion','A reproducible academic platform connecting MRI engineering, tutorials and transparent AI evidence.',['T1–T15 are represented through distinct aims, methods, actual output and limitations.','The persistent FLAIR CNN is integrated but remains experimental and slice-level.','Source-backed visuals and metrics make the work inspectable for an academic demonstration.'],['cnn','confusion'],'two',cap='Actual inference and held-out evaluation artifacts.')]

def tx(slide,text,x,y,w,h,sz=14,col=INK,bold=False,align=None):
 b=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); f=b.text_frame; f.clear(); f.word_wrap=True; p=f.paragraphs[0]; p.text=text; p.font.name='Aptos'; p.font.size=Pt(sz); p.font.bold=bold; p.font.color.rgb=col
 if align is not None:p.alignment=align
def box(slide,x,y,w,h,fill=PALE):
 q=slide.shapes.add_shape(ST.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)); q.fill.solid();q.fill.fore_color.rgb=fill;q.line.color.rgb=TEAL
def pic(slide,k,x,y,w,h):
 if k in A: slide.shapes.add_picture(A[k],Inches(x),Inches(y),width=Inches(w),height=Inches(h))
def bullets(slide,bs,x=.65,y=1.75,w=5.65):
 for b in bs: tx(slide,'• '+b,x,y,w,.66,13,INK);y+=.72
def diagram(slide,kind):
 if kind=='arch': labs=['Browser modules','FastAPI routes','her_core utilities','Models + artifacts','Rendered evidence']
 elif kind=='split': labs=['Training\n4 cases · 132','Validation\n1 case · 35','Held-out test\n1 case · 35']
 elif kind=='cnn':labs=['Input\n128²×1','Conv 32','Conv 64','Conv 128','Flatten','Dense 128','Sigmoid']
 elif kind=='check':labs=['✓ Technical depth','✓ Original figures','✓ T1–T15 coverage','✓ Saved metrics','✓ Limits visible','✓ QA']
 elif kind in {'workflow','cluster','report','limits','future','flow'}: labs={'workflow':['INPUT','VALIDATE','COMPUTE','INTERPRET'],'cluster':['TEXT','TF–IDF','K-MEANS','CLUSTERS'],'report':['RESPONSE','REPORT','HTML / PDF','RECORD'],'limits':['SMALL COHORT','METRICS','LIMITS','NO CLAIM'],'future':['NEW DATA','VALIDATE','CALIBRATE','GOVERN'],'flow':['FLAIR / SEG','VALIDATE','PREPROCESS','ALGORITHM','PNG / METRICS','UI']}[kind]
 else:return
 n=len(labs); w=11.4/n
 for i,l in enumerate(labs):
  x=.95+i*w; box(slide,x,3.1,w-.20,.85,SKY if i%2 else PALE); tx(slide,l,x+.06,3.38,w-.32,.28,12,INK,True,PP_ALIGN.CENTER)
  if i<n-1:tx(slide,'→',x+w-.14,3.36,.2,.2,16,TEAL,True)
def table(slide,rows):
 x,y,w,h=.8,2.0,11.75,3.7;cw=w/len(rows[0]);rh=h/len(rows)
 for r,row in enumerate(rows):
  for c,v in enumerate(row):
   q=slide.shapes.add_shape(ST.RECTANGLE,Inches(x+c*cw),Inches(y+r*rh),Inches(cw),Inches(rh));q.fill.solid();q.fill.fore_color.rgb=NAVY if r==0 else (PALE if r%2 else RGBColor(255,255,255));q.line.color.rgb=RGBColor(211,224,222)
   tx(slide,str(v),x+c*cw+.05,y+r*rh+.12,cw-.1,rh-.14,11,RGBColor(255,255,255) if r==0 else INK,r==0,PP_ALIGN.CENTER)
def ppt():
 p=Presentation();p.slide_width=Inches(13.333);p.slide_height=Inches(7.5)
 for n,d in enumerate(slides,1):
  sl=p.slides.add_slide(p.slide_layouts[6]);bg=sl.background.fill;bg.solid();bg.fore_color.rgb=RGBColor(250,252,252);q=sl.shapes.add_shape(ST.RECTANGLE,0,0,Inches(.18),Inches(7.5));q.fill.solid();q.fill.fore_color.rgb=TEAL;q.line.fill.background()
  tx(sl,'BRAIN + MRI RESEARCH PLATFORM',.52,.25,5,.2,9,TEAL,True);tx(sl,d['t'],.52,.54,12,.55,24,NAVY,True);tx(sl,d['sub'],.54,1.15,12,.3,12,MUTED);tx(sl,f'{n:02d} | Healthcare project evidence deck',.52,7.12,3.7,.15,8,TEAL);tx(sl,'Research-only · not a clinical diagnosis',8.6,7.12,4,.15,8,TEAL,False,PP_ALIGN.RIGHT)
  if d['kind']=='table':bullets(sl,d['b'],.65,1.65,12);table(sl,d['table'])
  elif d['kind'] in {'arch','split','cnn','check','workflow','cluster','report','limits','future','flow'}:bullets(sl,d['b'],.65,1.65,12);diagram(sl,d['kind'])
  elif len(d['im'])==2:bullets(sl,d['b']);pic(sl,d['im'][0],6.48,1.8,2.85,4.55);pic(sl,d['im'][1],9.55,1.8,2.85,4.55)
  elif len(d['im'])==1:
   wide=d['im'][0].endswith('screen') or d['im'][0] in {'s1','s2','s3','s4','s5','s6','uploadscreen'}
   if wide:
    bullets(sl,d['b'],.65,1.60,12);pic(sl,d['im'][0],1.0,3.45,11.25,2.90)
   else:
    bullets(sl,d['b']);pic(sl,d['im'][0],6.55,1.7,5.65,4.75)
  else:bullets(sl,d['b'],.65,1.8,12)
  if d['cap']:tx(sl,d['cap'],6.55,6.5,5.65,.15,8,MUTED,False,PP_ALIGN.CENTER)
 p.save(OUT/'Healthcare_Project_Presentation_Final.pptx')
def pdftext(c,t,x,y,w,size=10,bold=False):
 c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.setFillColor(HexColor('#1e2f39'))
 for line in textwrap.wrap(t,max(14,int(w/(size*.52)))):c.drawString(x,y,line);y-=size*1.25
 return y
def pdf():
 c=canvas.Canvas(str(OUT/'Healthcare_Project_Presentation_Final.pdf'),pagesize=landscape(A4));W,H=landscape(A4)
 for n,d in enumerate(slides,1):
  c.setFillColor(HexColor('#fafcfc'));c.rect(0,0,W,H,fill=1,stroke=0);c.setFillColor(HexColor('#007b7a'));c.rect(0,0,12,H,fill=1,stroke=0);c.setFont('Helvetica-Bold',8);c.drawString(36,H-20,'BRAIN + MRI RESEARCH PLATFORM');c.setFillColor(HexColor('#0a273e'));c.setFont('Helvetica-Bold',21);c.drawString(36,H-44,d['t'][:95]);c.setFont('Helvetica',10);c.setFillColor(HexColor('#53656d'));c.drawString(36,H-62,d['sub'][:145]);y=H-86
  if d['kind']=='table':
   for b in d['b']:y=pdftext(c,'• '+b,45,y,W-90)
   rows=d['table'];cw=(W-110)/len(rows[0]);y-=8
   for r,row in enumerate(rows):
    for j,v in enumerate(row):
     c.setFillColor(HexColor('#0a273e' if r==0 else '#eff7f6'));c.rect(55+j*cw,y-r*26,cw,26,fill=1,stroke=1);c.setFillColor(HexColor('#ffffff' if r==0 else '#1e2f39'));c.setFont('Helvetica-Bold' if r==0 else 'Helvetica',8);c.drawCentredString(55+j*cw+cw/2,y-r*26+10,str(v))
  else:
   bw=W-90 if not d['im'] else W*.47
   for b in d['b']:y=pdftext(c,'• '+b,45,y,bw)
   if len(d['im'])==1 and d['im'][0] in A:
    wide=d['im'][0].endswith('screen') or d['im'][0] in {'s1','s2','s3','s4','s5','s6','uploadscreen'}
    if wide:c.drawImage(ImageReader(A[d['im'][0]]),W*.08,55,W*.84,H*.38,preserveAspectRatio=True,anchor='c')
    else:c.drawImage(ImageReader(A[d['im'][0]]),W*.52,70,W*.41,H*.57,preserveAspectRatio=True,anchor='c')
   if len(d['im'])==2:
    for i,k in enumerate(d['im']):
     if k in A:c.drawImage(ImageReader(A[k]),W*.50+i*W*.24,70,W*.22,H*.57,preserveAspectRatio=True,anchor='c')
   if d['kind'] in {'arch','split','cnn','check','workflow','cluster','report','limits','future','flow'}:
    labs=['INPUT','VALIDATE','COMPUTE','INTERPRET'];cw=(W-90)/len(labs)
    for i,l in enumerate(labs):c.setFillColor(HexColor('#eff7f6'));c.roundRect(45+i*cw,H-260,cw-10,36,6,fill=1,stroke=1);c.setFillColor(HexColor('#1e2f39'));c.setFont('Helvetica-Bold',9);c.drawCentredString(45+i*cw+(cw-10)/2,H-241,l)
  c.setFillColor(HexColor('#007b7a'));c.setFont('Helvetica',7);c.drawString(36,18,f'{n:02d} | Healthcare project evidence deck');c.drawRightString(W-36,18,'Research-only · not a clinical diagnosis');c.showPage()
 c.save()
def refs():
 lines=['# Presentation Content Reference','',f'- **{len(slides)} slides**; **{len(A)} actual project figures/notebook outputs** copied into `Presentation_Assets/`.','- `models/model_metadata.json`: brats-flair-slice-cnn-v1; 128×128×1 FLAIR; threshold 0.50.','- `models/evaluation_report.json`: accuracy 0.6286, ROC-AUC 0.9384, confusion matrix [[11,1],[12,11]], one held-out patient.','- `models/training_history.json`: embedded learning curves.','- `HER_Biomedical_Image_Tutorials_T1_T6.ipynb`: extracted original plots for T1–T6.','- `artifacts/visual_T13_0.png`, `visual_T14_2.png`, `visual_T14_3.png`, `forecast_preview.png`: T13–T15 outputs.','- `backend/tutorials.py`, `her_core/*`, `frontend/*`: implementation sources.','','All CNN claims are experimental, slice-level and research-only. No clinical validation, diagnosis, predicted segmentation or fabricated metric is asserted.']
 (OUT/'Presentation_Content_Reference.md').write_text('\n'.join(lines),encoding='utf-8')
 audit=['# Presentation Revision Audit Checklist','', 'The earlier 33-slide delivery was audited slide-by-slide before rebuilding. The observed issues were sparse technical detail, large unused areas, limited output evidence, and only summary-level tutorial treatment.', '', '## Corrective coverage', '', '- [x] Slides 1–3: replaced generic opening material with evidence audit, problem statement and data safeguards.', '- [x] Slides 4–8: added architecture, data lineage, dataset audit, preprocessing contract and workspace visual evidence.', '- [x] Slides 9–24: expanded T1–T6 and CNN material with original notebook figures, layer diagram, split, configuration table, learning curves, matrix, ROC and report.', '- [x] Slides 25–34: added individual T7–T15 technical scope slides and all available saved project outputs for T13–T15.', '- [x] Slides 35–42: added application integration, upload inference, reporting, traceability, verification, safeguards, future work and conclusion.', '', '## Render QA', '', '- [x] Editable PPTX contains 42 slides.', '- [x] PDF contains the same 42 slide specifications and was rendered page-by-page for visual inspection.', '- [x] 28 project-source raster assets were copied to `Presentation_Assets` and no missing picture blobs were detected.', '- [x] LibreOffice was not installed, so the matching PDF was generated from the same slide specification rather than converted by LibreOffice.', '', '## Evidence limitation', '', 'T7–T12 expose data/table/text workflows but the repository contains no saved raster screenshots for them. Their slides therefore use source-backed workflow diagrams rather than fabricated output screenshots.']
 (OUT/'Presentation_Audit_Checklist.md').write_text('\n'.join(audit),encoding='utf-8')
ppt();pdf();refs();print(f'Generated {len(slides)} slides and {len(A)} actual figures.')
