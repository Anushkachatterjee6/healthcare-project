import json
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app
from her_core.analytics import example_data, run_analysis
from her_core.preprocess import clean_image,zscore_standardize,minmax_normalize
from her_core.cnn import patient_level_split,_prepare_slice


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results={i:run_analysis(i) for i in range(7,16)}

    def test_all_example_outputs(self):
        for i,result in self.results.items():
            with self.subTest(tutorial=i):
                self.assertEqual(result['tutorial'],i)
                self.assertIn('synthetic',result['dataset'])
                self.assertTrue(result['tables'])
                self.assertTrue(result['interpretation'])
                json.dumps(result,allow_nan=False)

    def test_forecast_metrics_and_chronology(self):
        r=self.results[7]; rows=r['tables']['forecast']
        actual=np.array([x['actual'] for x in rows]);pred=np.array([x['predicted'] for x in rows])
        self.assertAlmostEqual(r['metrics']['MAE'],np.abs(actual-pred).mean(),places=7)
        self.assertEqual(r['metrics']['train_days'],144)
        self.assertEqual(rows[0]['date'],'2025-05-25')
        self.assertTrue(all(x['illustrative_staff']==int(np.ceil(x['predicted']/8)) for x in rows))

    def test_classifier_holdout(self):
        m=self.results[10]['metrics']
        for key in ['accuracy','precision','recall','F1']:self.assertTrue(0<=m[key]<=1)
        self.assertEqual(m['train_rows']+m['test_rows'],36)
        self.assertEqual(sum(x['size'] for x in self.results[10]['tables']['clusters']),m['train_rows'])

    def test_missing_empty_all_tutorials(self):
        for i in range(7,16):
            with self.subTest(tutorial=i):
                with self.assertRaises(ValueError):run_analysis(i,[])
                with self.assertRaises(ValueError):run_analysis(i,[{'wrong':1}])

    def test_entity_offsets_and_uncertainty(self):
        context='No fever. metformin 500 mg for diabetes.'
        r=run_analysis(11,text=context)
        for e in r['tables']['entities']:self.assertEqual(context[e['start']:e['end']],e['entity'])
        self.assertTrue(next(e for e in r['tables']['entities'] if e['entity']=='fever')['possible_negation'])
        self.assertIn('ambiguous',run_analysis(12,text='MS assessment')['tables']['disambiguation'][0]['interpretation'])
        r=run_analysis(12,text='MS neurological interferon')
        self.assertEqual(r['tables']['disambiguation'][0]['interpretation'],'multiple sclerosis')

    def test_pca_and_regression(self):
        variance=self.results[13]['tables']['explained_variance']
        self.assertAlmostEqual(variance[-1]['cumulative'],1)
        self.assertTrue(all(a['cumulative']<=b['cumulative'] for a,b in zip(variance,variance[1:])))
        features={x['feature'] for x in self.results[15]['tables']['coefficients']}
        self.assertNotIn('weight_kg',features);self.assertNotIn('height_m',features)
        self.assertLess(self.results[15]['metrics']['MAE'],4)

    def test_data_validation(self):
        df=example_data(7);df.loc[0,'capacity']=0
        with self.assertRaises(ValueError):run_analysis(7,df)
        df=example_data(7);df['admissions']=df.admissions.astype(object);df.loc[0,'admissions']='bad'
        with self.assertRaises(ValueError):run_analysis(7,df)
        df=example_data(14);df['age']=12
        with self.assertRaises(ValueError):run_analysis(14,df)
        df=example_data(15);df.loc[0,'sleep_hours']=np.nan
        result=run_analysis(15,df)
        self.assertIn('User-supplied',result['dataset'])
        self.assertTrue(np.isfinite(result['metrics']['RMSE']))
        df=example_data(13);df[:]=df.iloc[0].to_numpy()
        with self.assertRaises(ValueError):run_analysis(13,df)
        single=run_analysis(9,example_data(9).iloc[:1])
        self.assertIsNone(single['metrics']['daily_admissions_variance'])
        json.dumps(single,allow_nan=False)
        with self.assertRaises(ValueError):run_analysis(11,[{'text':123}])
        for i in (7,8,9):
            result=run_analysis(i,example_data(i)[['date','admissions']])
            self.assertEqual(result['tutorial'],i)
            self.assertNotIn('occupancy_rate',result['metrics'])

    def test_preprocessing_and_cnn_split(self):
        x=np.array([[np.nan,np.inf],[1,3]],dtype=float)
        self.assertTrue(np.isfinite(clean_image(x)).all())
        self.assertEqual(minmax_normalize(np.ones((2,2))).sum(),0)
        standardized=zscore_standardize(clean_image(x))
        self.assertAlmostEqual(float(standardized[clean_image(x)!=0].mean()),0)
        train,val=patient_level_split(['a','b','c','d'])
        self.assertFalse(set(train)&set(val))
        mask=np.zeros((64,64));mask[20:40,20:40]=4
        image,prepared,label=_prepare_slice(np.ones((64,64)),mask,(32,32))
        self.assertEqual(label,1);self.assertEqual(set(np.unique(prepared)),{0,1})


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.client=TestClient(app)

    def test_health_and_metadata(self):
        self.assertEqual(self.client.get('/api/health').status_code,200)
        data=self.client.get('/api/tutorials').json()['tutorials']
        self.assertEqual(len(data),15)

    def test_all_new_routes(self):
        for i in range(7,16):
            with self.subTest(tutorial=i):
                r=self.client.post(f'/api/tutorials/{i}/run',json={})
                self.assertEqual(r.status_code,200,r.text[:300]);self.assertEqual(r.json()['tutorial'],i)

    def test_invalid_uploads_and_schema(self):
        c=self.client
        self.assertEqual(c.post('/api/tutorials/7/upload',content=b'bad',headers={'content-type':'application/octet-stream'}).status_code,415)
        for data in [b'',b'bad\n1',b'\xff\x00']:
            self.assertEqual(c.post('/api/tutorials/7/upload',content=data,headers={'content-type':'text/csv'}).status_code,422)
        self.assertEqual(c.post('/api/tutorials/7/upload',content=b'a'*(2*1024*1024+1),headers={'content-type':'text/csv'}).status_code,413)
        self.assertEqual(c.post('/api/tutorials/7/run',json={'records':[]}).status_code,422)
        self.assertEqual(c.post('/api/tutorials/7/run',json={'workload':0}).status_code,422)
        self.assertEqual(c.post('/api/tutorials/99/run',json={}).status_code,404)
        self.assertEqual(c.get('/api/cases?data_root=C:/Windows').status_code,400)

    def test_csv_upload_and_download(self):
        for i in range(7,16):
            with self.subTest(tutorial=i):
                example=self.client.get(f'/api/tutorials/{i}/example')
                self.assertEqual(example.status_code,200)
                r=self.client.post(f'/api/tutorials/{i}/upload',content=example.content,headers={'content-type':'text/csv'})
                self.assertEqual(r.status_code,200,r.text[:300])
                self.assertIn('User-supplied',r.json()['dataset'])

    def test_frontend_and_missing_mri(self):
        for path in ['/','/image-analysis','/static/lab.js','/static/lab.css','/static/image-analysis.js']:
            self.assertEqual(self.client.get(path).status_code,200)
        with patch('backend.tutorials.discover_cases',return_value=[]):
            self.assertEqual(self.client.post('/api/tutorials/2/run',json={}).status_code,503)


if __name__=='__main__':unittest.main(verbosity=2)
