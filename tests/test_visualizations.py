"""API/PNG completeness and data-derived visualization regression checks."""
import base64
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from backend.main import app
from her_core.analytics import example_data, run_analysis
from her_core.io import discover_cases


EXPECTED_VISUALS={
    1:['Original MRI middle slice','Available modality counts'],
    2:['Preprocessing'],
    3:['Missing MRI modalities'],
    4:['Image processing','MRI + provided segmentation overlay'],
    5:['SIFT + RANSAC correspondences','Original MRI slice 1','Original MRI slice 2',
       'SIFT keypoints — slice 1','SIFT keypoints — slice 2','Feature matches before RANSAC'],
    6:['Same-patient multimodal MRI','Nonbackground intensity histogram','Segmentation mask',
       'MRI + provided segmentation overlay','Notebook enhancement and restoration comparison','3D MRI intensity threshold'],
    7:['Chronological holdout: admissions','Admission forecast residuals','Illustrative staffing demand'],
    8:['Daily admissions','Admissions by department','Occupancy and capacity over time','Cost per admission by department'],
    9:['Daily admissions','Computed planning priority','Admissions distributions by department'],
    10:['Training document clusters','Clinical text holdout confusion matrix'],
    11:['Detected text mentions by category'],
    12:['Document relevance (cosine similarity)','Word-sense context evidence'],
    13:['PCA projection','Isomap nonlinear projection (up to 500 rows)','PCA explained and cumulative variance'],
    14:['Physical activity and BMI','Adult BMI distribution','Adult measurement correlations','Adult behavioral feature distributions'],
    15:['Physical activity and BMI','Adult BMI distribution','Held-out BMI predictions','Multivariable BMI coefficients','Held-out BMI residuals'],
}


class VisualizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client=TestClient(app);cls.results={};cls.summary=[]
        for tutorial in range(1,16):
            response=cls.client.post(f'/api/tutorials/{tutorial}/run',json={})
            if response.status_code!=200:raise AssertionError(f'T{tutorial}: {response.text}')
            result=response.json();cls.results[tutorial]=result
            cls.summary.append({'tutorial':tutorial,'status':response.status_code,'bytes':len(response.content),
                'plots':[{'title':p['title'],'caption':p.get('caption','')} for p in result['plots']],
                'tables':{name:len(rows) for name,rows in result['tables'].items()},
                'annotation_spans':len(result.get('annotations',{}).get('spans',[]))})
        outdir=Path(__file__).resolve().parents[1]/'artifacts';outdir.mkdir(exist_ok=True)
        (outdir/'visualization_verification.json').write_text(json.dumps(cls.summary,indent=2),encoding='utf-8')

    def test_every_tutorial_returns_expected_unique_visuals(self):
        for tutorial,result in self.results.items():
            with self.subTest(tutorial=tutorial):
                titles=[p['title'] for p in result['plots']]
                self.assertTrue(set(EXPECTED_VISUALS[tutorial])<=set(titles))
                self.assertEqual(len(titles),len(set(titles)))
                json.dumps(result,allow_nan=False)
                self.assertLess(next(s['bytes'] for s in self.summary if s['tutorial']==tutorial),3_000_000)

    def test_all_images_decode_and_have_readable_dimensions(self):
        for tutorial,result in self.results.items():
            for plot in result['plots']:
                with self.subTest(tutorial=tutorial,title=plot['title']):
                    png=base64.b64decode(plot['png'],validate=True)
                    self.assertTrue(png.startswith(b'\x89PNG\r\n\x1a\n'))
                    with Image.open(BytesIO(png)) as image:
                        self.assertGreaterEqual(image.width,200);self.assertGreaterEqual(image.height,200)
                        image.verify()

    def test_forecast_error_values_and_staffing_source(self):
        result=self.results[7]
        forecast=result['tables']['forecast'];errors=result['tables']['forecast_errors']
        self.assertEqual(len(forecast),len(errors))
        for predicted,error in zip(forecast,errors):
            self.assertEqual(predicted['date'],error['date'])
            self.assertAlmostEqual(error['residual_admissions'],predicted['actual']-predicted['predicted'],places=7)
        staffing=next(p for p in result['plots'] if p['title']=='Illustrative staffing demand')
        self.assertIn('not a staffing prescription',staffing['caption'])

    def test_text_offsets_and_sense_evidence(self):
        text='<script>alert("x")</script> No fever. Metformin 500 mg for diabetes.'
        result=run_analysis(11,text=text)
        annotation=result['annotations'];self.assertEqual(annotation['text'],text)
        for span,entity in zip(annotation['spans'],result['tables']['entities']):
            self.assertEqual(text[span['start']:span['end']],entity['entity'])
        resolved=run_analysis(12,text='MS neurological interferon')
        scores={r['sense']:r['matched_cues'] for r in resolved['tables']['sense_evidence']}
        self.assertEqual(scores,{'multiple sclerosis':2,'mitral stenosis':0})
        empty=run_analysis(11,text='No supported dictionary terms here.')
        self.assertEqual(empty['plots'],[]);self.assertTrue(empty['visualization_notes'])
        unsupported=run_analysis(12,text='Unsupported abbreviation XYZ')
        self.assertEqual(unsupported['tables']['sense_evidence'],[])
        self.assertTrue(unsupported['visualization_notes'])

    def test_missing_optional_operational_fields_do_not_invent_charts(self):
        for tutorial in (8,9):
            result=run_analysis(tutorial,example_data(tutorial)[['date','admissions']])
            titles=[p['title'] for p in result['plots']]
            self.assertFalse(any('Occupancy' in t or 'Cost' in t for t in titles))
            self.assertIn('User-supplied',result['dataset'])

    def test_adult_missingness_and_holdout_residuals(self):
        df=example_data(14);df.loc[0,'sleep_hours']=np.nan
        result=run_analysis(14,df)
        self.assertIn('Adult feature missingness',[p['title'] for p in result['plots']])
        predictions=self.results[15]['tables']['regression_predictions']
        for row in predictions:
            self.assertAlmostEqual(row['residual_BMI'],row['actual_BMI']-row['predicted_BMI'],places=7)
        self.assertAlmostEqual(np.mean([abs(row['residual_BMI']) for row in predictions]),self.results[15]['metrics']['MAE'],places=7)

    def test_real_duplicate_file_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            paths=[Path(folder)/f'demo_{i}_flair.nii' for i in range(2)]
            for path in paths:path.write_bytes(b'deterministic file bytes for duplicate-check test')
            cases=[{'case_id':f'synthetic_{i}','path':p.parent,'modalities':{'flair':p}} for i,p in enumerate(paths)]
            with patch('backend.tutorials.discover_cases',return_value=cases):
                result=self.client.post('/api/tutorials/3/run',json={}).json()
            self.assertEqual(result['metrics']['exact_duplicate_files'],2)
            self.assertEqual(len(result['tables']['exact_duplicate_files']),2)

    def test_3d_cap_and_missing_mri_inputs(self):
        projection=next(p for p in self.results[6]['plots'] if p['title']=='3D MRI intensity threshold')
        self.assertTrue(0<projection['points_displayed']<=12000)
        with patch('backend.tutorials.discover_cases',return_value=[]):
            for tutorial in range(1,7):
                self.assertEqual(self.client.post(f'/api/tutorials/{tutorial}/run',json={}).status_code,503)
        for tutorial in range(7,16):
            self.assertEqual(self.client.post(f'/api/tutorials/{tutorial}/run',json={'records':[]}).status_code,422)
            self.assertEqual(self.client.post(f'/api/tutorials/{tutorial}/run',json={'records':[{'invalid':1}]}).status_code,422)

    def test_optional_segmentation_is_not_fabricated(self):
        case=next(c for c in discover_cases() if 'flair' in c['modalities'] and 'seg' not in c['modalities'])
        with patch('backend.tutorials.discover_cases',return_value=[case]):
            for tutorial in (4,6):
                response=self.client.post(f'/api/tutorials/{tutorial}/run',json={})
                self.assertEqual(response.status_code,200)
                result=response.json()
                self.assertNotIn('MRI + provided segmentation overlay',[p['title'] for p in result['plots']])
                self.assertTrue(result['warnings'])


if __name__=='__main__':unittest.main(verbosity=2)
