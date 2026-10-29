"""Offline educational T7–T15 analyses. No patient records or external downloads."""
from __future__ import annotations

import base64
import json
from io import BytesIO
import re
import threading
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import Isomap
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (accuracy_score, precision_recall_fscore_support,
    confusion_matrix, silhouette_score, mean_absolute_error, mean_squared_error, r2_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

TITLES = [
    'Understanding biomedical MRI data', 'Standardization and data cleaning',
    'Redundant data removal and missing data', 'Enhancement, restoration, segmentation, compression',
    'SIFT, RANSAC and CNN image analysis', 'Biomedical image visualization',
    'Patient prediction for improved staffing',
    'Using healthcare data for informed strategic planning — Part 1',
    'Using healthcare data for informed strategic planning — Part 2',
    'Classification and clustering of clinical text data',
    'Information extraction and entity recognition of clinical text data',
    'Ranking and word disambiguation of clinical text data',
    'Dimensionality reduction for exploratory data analysis in daily medical research',
    'Analyzing the complexity of behavioral factors influencing WEIGHTS IN ADULTS — Part 1',
    'Analyzing the complexity of behavioral factors influencing WEIGHTS IN ADULTS — Part 2']
PLOT_LOCK = threading.Lock()


def example_data(tutorial):
    rng = np.random.default_rng(42)
    if tutorial in (7, 8, 9):
        n = 180
        day = np.arange(n)
        return pd.DataFrame(dict(date=pd.date_range('2025-01-01', periods=n).strftime('%Y-%m-%d'),
            admissions=np.maximum(1, np.round(70 + .15*day + 12*np.sin(2*np.pi*day/7) + rng.normal(0, 4, n))),
            department=np.array(['Emergency', 'Medicine', 'Surgery'])[day % 3],
            occupied_beds=rng.integers(50, 96, n), capacity=np.full(n, 100),
            cost=rng.uniform(15000, 35000, n).round(2)))
    if tutorial in (10, 11, 12):
        templates = {
            'respiratory': ['cough wheeze asthma inhaler chest xray', 'dyspnea fever pneumonia oxygen chest imaging', 'wheezing cough shortness breath spirometry'],
            'cardiac': ['chest pain angina ECG aspirin cardiology', 'palpitations arrhythmia ECG heart monitor', 'hypertension heart failure edema echocardiogram'],
            'metabolic': ['diabetes glucose insulin HbA1c metformin', 'hyperglycemia thirst diabetes blood glucose', 'diabetes fatigue glucose monitoring insulin']}
        return pd.DataFrame([{'text': text + ' ' + suffix, 'label': label}
            for label, texts in templates.items() for text in texts
            for suffix in ['review today', 'follow up scheduled', 'assessment recorded', 'outpatient visit']])
    n = 180
    age = rng.integers(18, 76, n)
    height = rng.normal(1.68, .09, n).clip(1.4, 2)
    activity = rng.uniform(0, 8, n)
    sedentary = rng.uniform(2, 12, n)
    sleep = rng.uniform(4, 9, n)
    bmi = 25 + .035*(age-40) - .6*activity + .5*sedentary - .3*sleep + rng.normal(0, 2, n)
    return pd.DataFrame(dict(age=age, height_m=height, weight_kg=bmi*height**2,
        activity_hours_week=activity, sedentary_hours_day=sedentary, sleep_hours=sleep))


def records(df):
    return json.loads(df.replace([np.inf, -np.inf], np.nan).to_json(orient='records',date_format='iso'))


def figure_plot(title, x, series, kind='line', *, xlabel='', ylabel=''):
    # Matplotlib state is not thread safe; use object API under a small lock.
    from matplotlib.figure import Figure
    with PLOT_LOCK:
        fig = Figure(figsize=(8, 4), layout='constrained')
        ax = fig.subplots()
        for label, y in series.items():
            if kind == 'scatter': ax.scatter(x, y, label=label, s=14, alpha=.7)
            elif kind == 'bar': ax.bar(x, y, label=label)
            else: ax.plot(x, y, label=label)
        ax.set_title(title)
        if xlabel:ax.set_xlabel(xlabel)
        if ylabel:ax.set_ylabel(ylabel)
        ax.legend()
        if len(x) > 12 and isinstance(list(x)[0], str):
            ax.set_xticks(np.arange(0, len(x), max(1, len(x)//6)))
        ax.tick_params(axis='x', labelrotation=25)
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=110)
        return {'title': title, 'png': base64.b64encode(buf.getvalue()).decode(), 'x_label':xlabel, 'y_label':ylabel}


def require(df, columns, numeric=()):
    missing = sorted(set(columns)-set(df.columns))
    if missing: raise ValueError('Missing required columns: ' + ', '.join(missing))
    df = df.copy()
    for col in numeric:
        original = df[col]
        df[col] = pd.to_numeric(original, errors='coerce')
        if (original.notna() & df[col].isna()).any(): raise ValueError(f'{col} contains nonnumeric values')
        if np.isinf(df[col]).any(): raise ValueError(f'{col} contains infinite values')
    return df


def run_analysis(tutorial, data=None, *, text='', query='diabetes glucose', clusters=3, workload=8):
    from .visualizations import chart, bars, heatmap, behavioral_distributions
    if tutorial not in range(7, 16): raise ValueError('Analytics tutorial must be T7–T15')
    synthetic = data is None
    df = example_data(tutorial) if synthetic else pd.DataFrame(data)
    if df.empty: raise ValueError('Dataset is empty')
    if len(df)>5000 or len(df.columns)>50: raise ValueError('Limit: 5000 rows and 50 columns')
    if not 2 <= clusters <= 10: raise ValueError('Cluster count must be 2–10')
    if not 0 < workload <= 100: raise ValueError('Workload per staff must be greater than zero and at most 100')
    out = dict(tutorial=tutorial, title=TITLES[tutorial-1],
        dataset='Deterministic synthetic demonstration (seed 42); not actual patient data' if synthetic else 'User-supplied data; provenance not independently verified',
        metrics={}, tables={}, plots=[], interpretation=[], warnings=[], rows_input=len(df))
    out['tables']['missing_values'] = records(df.isna().sum().rename('missing').rename_axis('column').reset_index())
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    out['metrics']['duplicate_rows_removed'] = before-len(df)
    if tutorial in (7, 8, 9):
        # Only request operational fields actually needed by the analysis.
        numeric=[c for c in ['admissions','occupied_beds','capacity','cost'] if c in df]
        df = require(df, ['date','admissions'], numeric)
        if 'department' not in df: df['department']='All records'
        if ('occupied_beds' in df) != ('capacity' in df): raise ValueError('Supply occupied_beds and capacity together, or omit both')
        has_beds='capacity' in df
        df['date'] = pd.to_datetime(df.date, errors='coerce')
        if df.isna().any().any(): raise ValueError('Operational data require complete values and valid dates')
        if ((df[[c for c in ['admissions','occupied_beds','cost'] if c in df]]<0).any().any() or (has_beds and ((df.capacity<=0).any() or (df.occupied_beds>df.capacity).any()))):
            raise ValueError('Counts/cost must be nonnegative, capacity positive, occupancy within capacity')
        daily = df.groupby('date')[numeric].sum().sort_index()
        if has_beds: daily['occupancy'] = daily.occupied_beds/daily.capacity
        out['tables']['daily'] = records(daily.reset_index().assign(date=lambda x:x.date.dt.strftime('%Y-%m-%d')))
        if tutorial == 7:
            if len(daily)<30: raise ValueError('Forecasting requires at least 30 distinct days')
            if not (daily.index.to_series().diff().dropna()==pd.Timedelta(days=1)).all(): raise ValueError('Forecasting requires consecutive daily observations')
            features = pd.DataFrame({'trend':np.arange(len(daily)), 'sin_week':np.sin(2*np.pi*daily.index.dayofweek/7), 'cos_week':np.cos(2*np.pi*daily.index.dayofweek/7)}, index=daily.index)
            split = int(.8*len(daily))
            model = make_pipeline(StandardScaler(), Ridge(alpha=1)).fit(features.iloc[:split], daily.admissions.iloc[:split])
            predicted = np.maximum(0, model.predict(features.iloc[split:]))
            actual = daily.admissions.iloc[split:].to_numpy()
            baseline = np.full(len(actual), daily.admissions.iloc[:split].mean())
            out['metrics'].update(MAE=float(mean_absolute_error(actual,predicted)), RMSE=float(np.sqrt(mean_squared_error(actual,predicted))), baseline_MAE=float(mean_absolute_error(actual,baseline)), train_days=split, test_days=len(actual), workload_per_staff=workload)
            out['tables']['forecast'] = records(pd.DataFrame({'date':daily.index[split:].strftime('%Y-%m-%d'),'actual':actual,'predicted':predicted,'illustrative_staff':np.ceil(predicted/workload).astype(int)}))
            out['plots'].append(figure_plot('Chronological holdout: admissions',daily.index[split:].strftime('%m-%d'), {'actual':actual,'predicted':predicted},xlabel='Holdout date (month-day)',ylabel='Admissions (patients/day)'))
            residuals=actual-predicted
            out['tables']['forecast_errors']=records(pd.DataFrame({'date':daily.index[split:].strftime('%Y-%m-%d'),'residual_admissions':residuals}))
            def residual_chart(ax):
                ax.plot(daily.index[split:],residuals,label='Actual − predicted')
                ax.axhline(0,color='gray',linestyle='--');ax.legend()
                ax.tick_params(axis='x',rotation=25)
            out['plots'].append(chart('Admission forecast residuals',residual_chart,xlabel='Holdout date',ylabel='Admission error (patients)'))
            staff=np.ceil(predicted/workload)
            def staffing_chart(ax):
                ax.step(daily.index[split:],staff,where='mid',label='ceil(predicted / workload)')
                ax.legend();ax.tick_params(axis='x',rotation=25)
            out['plots'].append(chart('Illustrative staffing demand',staffing_chart,xlabel='Holdout date',ylabel='Illustrative staff count',
                caption=f'Assumes {workload:g} admissions per staff member per day; not a staffing prescription.'))
            out['interpretation'].append(f'One-day demand modeled using calendar features known in advance; last {len(actual)} days held out. Illustrative staff = ceil(predicted admissions / {workload}); this is a workload assumption, not a staffing prescription.')
        else:
            aggregations={'admissions':('admissions','sum'),'observations':('admissions','size')}
            if has_beds: aggregations.update(occupancy=('occupied_beds','sum'),capacity=('capacity','sum'))
            if 'cost' in df: aggregations['cost']=('cost','sum')
            grouped = df.groupby('department').agg(**aggregations)
            if has_beds: grouped['occupancy_rate'] = grouped.occupancy/grouped.capacity
            if 'cost' in df: grouped['cost_per_admission'] = grouped.cost/grouped.admissions.replace(0,np.nan)
            out['tables']['departments'] = records(grouped.reset_index())
            out['tables']['descriptive'] = records(df.describe().reset_index())
            out['metrics']['total_admissions']=float(df.admissions.sum())
            if has_beds: out['metrics']['occupancy_rate']=float(df.occupied_beds.sum()/df.capacity.sum())
            if 'cost' in df: out['metrics']['total_cost']=float(df.cost.sum())
            out['plots'].append(figure_plot('Daily admissions',daily.index.strftime('%m-%d'),{'admissions':daily.admissions},xlabel='Observation date (month-day)',ylabel='Admissions per date'))
            view=grouped.head(20)
            if tutorial==8:
                out['plots'].append(bars('Admissions by department',view.index,view.admissions,ylabel='Admissions',caption='First 20 department names if more are supplied; complete results are in the table.'))
                if has_beds:
                    def occupancy_chart(ax):
                        ax.plot(daily.index,daily.occupied_beds,label='Occupied beds')
                        ax.plot(daily.index,daily.capacity,label='Supplied capacity');ax.legend()
                        ax.tick_params(axis='x',rotation=25)
                    out['plots'].append(chart('Occupancy and capacity over time',occupancy_chart,xlabel='Observation date',ylabel='Beds',caption='Counts use the supplied records; do not mix facility totals with department subtotals.'))
                if 'cost' in df:
                    out['plots'].append(bars('Cost per admission by department',view.index,view.cost_per_admission,ylabel='Supplied currency / admission',caption='Undefined when admissions are zero; no cost is estimated when absent.'))
            if tutorial == 9:
                samples=[g.admissions.to_numpy() for _,g in df.groupby('department') if len(g)>=5]
                if len(samples)>=2 and np.ptp(np.concatenate(samples))>0:
                    test=stats.kruskal(*samples)
                    out['metrics'].update(kruskal_H=float(test.statistic), kruskal_p=float(test.pvalue))
                out['metrics']['daily_admissions_variance']=float(daily.admissions.var()) if len(daily)>1 else None
                elapsed_days=(daily.index-daily.index[0]).total_seconds()/86400
                slope=stats.linregress(elapsed_days,daily.admissions) if len(daily)>1 else None
                if slope: out['metrics']['admissions_trend_per_day']=float(slope.slope)
                priority='occupancy_rate' if has_beds else 'admissions'
                ranked=grouped.sort_values(priority,ascending=False)
                out['tables']['planning_priority']=records(ranked.reset_index())
                rank_view=ranked.head(20)
                out['plots'].append(bars('Computed planning priority',rank_view.index,rank_view[priority],
                    ylabel='Occupied / capacity' if has_beds else 'Admissions',caption=f'Ranked by {priority}; up to 20 groups, complete ranking in the table.'))
                grouped_samples=list(df.groupby('department'))[:20]
                def variance_chart(ax):
                    ax.boxplot([group.admissions.to_numpy() for _,group in grouped_samples])
                    ax.set_xticks(np.arange(1,len(grouped_samples)+1),[str(name) for name,_ in grouped_samples],rotation=25,ha='right')
                out['plots'].append(chart('Admissions distributions by department',variance_chart,ylabel='Admissions per supplied record',
                    caption='Median, quartiles, whiskers and outliers of observed admissions; first 20 group names if needed.'))
                out['interpretation'].append(f'Highest observed {priority}: {ranked.index[0]} ({ranked[priority].iloc[0]:.4g}); review available capacity and cost evidence before allocating resources. Rank is by computed {priority} only.')
                out['warnings'].append('Kruskal comparison assumes independent observations; repeated facility/day records and temporal correlation can invalidate inferential p-values.')
            else: out['interpretation'].append('Compare measured occupancy, admissions and cost by department; these descriptive KPIs identify areas for further operational review.')
    elif tutorial in (10,11,12):
        df=require(df,['text'] + (['label'] if tutorial==10 else []))
        if df.text.isna().any() or (df.text.astype(str).str.strip()=='').any(): raise ValueError('Text records must be nonempty')
        if not df.text.map(lambda value:isinstance(value,str)).all(): raise ValueError('Text column must contain strings')
        if df.text.astype(str).str.len().max()>20000: raise ValueError('Text records limited to 20000 characters')
        docs=df.text.astype(str).tolist()
        if tutorial==10:
            if df.label.isna().any(): raise ValueError('Labels cannot be missing')
            # Keep identical normalized documents together by rejecting conflicting labels and deduplicating.
            df['normalized']=df.text.str.lower().str.replace(r'[^a-z0-9\s]',' ',regex=True).str.replace(r'\s+',' ',regex=True).str.strip()
            if df.groupby('normalized').label.nunique().max()>1: raise ValueError('Identical text has conflicting labels')
            df=df.drop_duplicates('normalized')
            counts=df.label.value_counts()
            if len(counts)<2 or counts.min()<3 or len(df)<12: raise ValueError('Need at least 12 distinct texts, 2 classes, and 3 texts per class')
            train,test=train_test_split(np.arange(len(df)),test_size=max(len(counts),int(np.ceil(.25*len(df)))),stratify=df.label,random_state=42)
            vec=TfidfVectorizer(lowercase=True,strip_accents='unicode',max_features=3000)
            xtrain=vec.fit_transform(df.normalized.iloc[train]); xtest=vec.transform(df.normalized.iloc[test])
            model=LogisticRegression(max_iter=500,random_state=42).fit(xtrain,df.label.iloc[train])
            pred=model.predict(xtest)
            p,r,f,_=precision_recall_fscore_support(df.label.iloc[test],pred,average='weighted',zero_division=0)
            out['metrics'].update(accuracy=float(accuracy_score(df.label.iloc[test],pred)),precision=float(p),recall=float(r),F1=float(f),train_rows=len(train),test_rows=len(test))
            labels=model.classes_
            text_cm=confusion_matrix(df.label.iloc[test],pred,labels=labels)
            out['tables']['confusion_matrix']=records(pd.DataFrame(text_cm,columns=labels).assign(actual=labels))
            out['plots'].append(heatmap('Clinical text holdout confusion matrix',text_cm[:20,:20],labels[:20],labels[:20],
                caption='Rows = actual, columns = predicted. Counts use held-out texts only; top-left 20 classes displayed if necessary.'))
            out['tables']['holdout_predictions']=records(pd.DataFrame({'actual':df.label.iloc[test].to_numpy(),'predicted':pred}))
            if text.strip(): out['tables']['entered_text_prediction']=[{'text':text,'predicted':str(model.predict(vec.transform([text]))[0])}]
            # Cluster training documents only; classification test data never participate in fitting.
            if clusters>=xtrain.shape[0]: raise ValueError('Clusters must be fewer than training documents')
            km=KMeans(n_clusters=clusters,n_init=10,random_state=42).fit(xtrain)
            terms=vec.get_feature_names_out()
            out['tables']['clusters']=[{'cluster':i,'size':int(sum(km.labels_==i)), 'terms':', '.join(terms[np.argsort(center)[-6:][::-1]])} for i,center in enumerate(km.cluster_centers_)]
            out['tables']['cluster_assignments']=records(pd.DataFrame({'text':df.text.iloc[train].to_numpy(),'cluster':km.labels_}))
            if 1<len(set(km.labels_))<len(train): out['metrics']['silhouette_cosine']=float(silhouette_score(xtrain,km.labels_,metric='cosine'))
            out['plots'].append(figure_plot('Training document clusters',np.arange(clusters),{'documents':np.bincount(km.labels_,minlength=clusters)},'bar',xlabel='Cluster ID',ylabel='Training documents'))
            out['interpretation'].append('TF-IDF and classifier fitted on training texts only. Template-based synthetic examples are easy and do not estimate real clinical generalization.')
        elif tutorial==11:
            context=text.strip() or docs[0]
            groups={'condition/symptom':['diabetes','asthma','pneumonia','hypertension','cough','fever','chest pain','fatigue','dyspnea'], 'medication':['aspirin','insulin','metformin','albuterol'], 'investigation/procedure':['ECG','MRI','CT','HbA1c','spirometry','chest xray']}
            entities=[]
            for category,terms in groups.items():
                for term in terms:
                    for match in re.finditer(r'\b'+re.escape(term)+r'\b',context,re.I):
                        prefix=context[max(0,match.start()-35):match.start()]
                        entities.append(dict(entity=match.group(),category=category,start=match.start(),end=match.end(),source_text=context,method='case-insensitive lexicon',possible_negation=bool(re.search(r'\b(no|denies|without|not)\b',prefix,re.I))))
            for match in re.finditer(r'\b\d+(?:\.\d+)?\s*(?:mg/dL|mmHg|kg|mg|bpm|cm|%)',context,re.I):
                entities.append(dict(entity=match.group(),category='measurement',start=match.start(),end=match.end(),source_text=context,method='measurement regex'))
            out['tables']['entities']=sorted(entities,key=lambda x:x['start'])
            out['annotations']={'text':context,'spans':[{'start':e['start'],'end':e['end'],'category':e['category'],
                'possible_negation':e.get('possible_negation',False)} for e in out['tables']['entities']]}
            out['metrics']['mentions']=len(entities)
            if entities:
                counts=pd.Series([e['category'] for e in entities]).value_counts()
                out['plots'].append(figure_plot('Detected text mentions by category',counts.index,{'mentions':counts.values},'bar',xlabel='Entity category',ylabel='Detected mentions'))
            else:out.setdefault('visualization_notes',[]).append('No supported entity mentions were detected, so a category-count chart is not applicable. The original text remains visible.')
            out['interpretation'].append('Detected mentions are not verified clinical facts. Negation flag uses a 35-character cue window and can be wrong. No annotated ground truth: precision/recall cannot be estimated.')
        else:
            if not query.strip(): raise ValueError('Enter a nonempty ranking query')
            vec=TfidfVectorizer(max_features=3000); matrix=vec.fit_transform(docs)
            scores=cosine_similarity(vec.transform([query]),matrix).ravel()
            out['tables']['ranking']=[{'rank':j+1,'document':docs[i],'score':float(scores[i])} for j,i in enumerate(np.argsort(-scores)[:10])]
            context=text.strip() or 'MS treated with interferon after neurological assessment'
            senses={'MS':{'multiple sclerosis':['neurolog','interferon','demyelin'], 'mitral stenosis':['valve','mitral','murmur']},'RA':{'rheumatoid arthritis':['joint','arthritis','methotrexate'],'right atrium':['atrium','cardiac','echo']}}
            rows=[];evidence=[]
            for term,options in senses.items():
                if re.search(r'\b'+term+r'\b',context,re.I):
                    scored={sense:sum(cue in context.lower() for cue in cues) for sense,cues in options.items()}
                    evidence.extend({'term':term,'sense':sense,'matched_cues':score} for sense,score in scored.items())
                    best=max(scored,key=scored.get)
                    resolved=scored[best]>0 and list(scored.values()).count(scored[best])==1
                    rows.append({'term':term,'context':context,'interpretation':best if resolved else 'ambiguous: insufficient or conflicting context','method':'explicit context cue counts','cue_scores':str(scored)})
            out['tables']['disambiguation']=rows or [{'context':context,'interpretation':'unsupported term; supported: MS, RA','method':'explicit context cue counts'}]
            out['tables']['sense_evidence']=evidence
            if evidence:
                out['plots'].append(bars('Word-sense context evidence',[f"{e['term']}: {e['sense']}" for e in evidence],
                    [e['matched_cues'] for e in evidence],ylabel='Matched context cues (count)',caption='Explicit cue counts, not probabilities or validated sense accuracy. Zero/tied evidence remains uncertain.'))
            else:out.setdefault('visualization_notes',[]).append('No supported MS/RA abbreviation occurs in this context; word-sense evidence chart is not applicable.')
            out['metrics']['top_relevance']=float(scores.max())
            order=np.argsort(-scores)[:10]
            out['plots'].append(figure_plot('Document relevance (cosine similarity)',[f'Doc {i+1}' for i in order],{'cosine similarity':scores[order]},'bar',xlabel='Corpus document',ylabel='TF-IDF cosine similarity'))
            out['interpretation'].append('Cosine similarity is lexical relevance, not clinical advice. No relevance judgments or sense labels are supplied, so ranking and sense accuracy are not measured.')
    else:
        required=['age','height_m','weight_kg','activity_hours_week','sedentary_hours_day','sleep_hours']
        df=require(df,required,required)
        out['metrics']['unknown_age_rows_excluded']=int(df.age.isna().sum())
        df=df[df.age>=18].copy()
        if len(df)<20: raise ValueError('Need at least 20 adult observations with known age')
        for col,low,high in [('age',18,120),('height_m',.8,2.5),('weight_kg',20,400),('activity_hours_week',0,168),('sedentary_hours_day',0,24),('sleep_hours',0,24)]:
            if ((df[col].dropna()<low)|(df[col].dropna()>high)).any(): raise ValueError(f'{col} outside supported measurement range [{low}, {high}]')
        df['BMI']=df.weight_kg/df.height_m**2
        if tutorial in (14,15) and not df.BMI.notna().any(): raise ValueError('No adults have valid observed height and weight for BMI analysis')
        features=['age','activity_hours_week','sedentary_hours_day','sleep_hours']
        if any(df[c].notna().sum()<2 for c in features): raise ValueError('Each predictor needs at least 2 observed values')
        out['metrics']['adult_rows']=len(df)
        out['tables']['descriptive']=records(df[required+['BMI']].describe().reset_index())
        out['tables']['correlations']=records(df[required+['BMI']].corr().reset_index())
        q1=df[required].quantile(.25); q3=df[required].quantile(.75)
        out['tables']['outlier_inspection']=records(((df[required]<q1-1.5*(q3-q1))|(df[required]>q3+1.5*(q3-q1))).sum().rename('IQR_flags').rename_axis('feature').reset_index())
        if tutorial==13:
            if any(df[c].notna().sum()<2 for c in required): raise ValueError('PCA needs at least 2 observed values per numerical column')
            x=make_pipeline(SimpleImputer(strategy='median'),StandardScaler()).fit_transform(df[required])
            if float(np.var(x,axis=0).sum())<1e-12: raise ValueError('PCA requires nonconstant numerical data')
            pca=PCA().fit(x); projection=pca.transform(x)
            out['tables']['explained_variance']=records(pd.DataFrame({'component':np.arange(1,len(required)+1),'variance':pca.explained_variance_ratio_,'cumulative':np.cumsum(pca.explained_variance_ratio_)}))
            def variance_chart(ax):
                components=np.arange(1,len(required)+1)
                ax.bar(components,pca.explained_variance_ratio_,label='Individual component')
                ax.plot(components,np.cumsum(pca.explained_variance_ratio_),marker='o',color='#ba6635',label='Cumulative')
                ax.set_ylim(0,1.05);ax.legend()
            out['plots'].append(chart('PCA explained and cumulative variance',variance_chart,xlabel='Principal component',ylabel='Fraction of standardized variance',caption='Same PCA fit as the projections; exploratory, not a biological group test.'))
            out['tables']['pca_coordinates']=records(pd.DataFrame(projection[:,:2],columns=['PC1','PC2']))
            out['plots'].append(figure_plot('PCA projection',projection[:,0],{'PC2':projection[:,1]},'scatter',xlabel='PC1 score (standardized features)',ylabel='PC2 score'))
            nonlinear=Isomap(n_components=2,n_neighbors=min(8,len(x)-1)).fit_transform(x[:500])
            out['plots'].append(figure_plot('Isomap nonlinear projection (up to 500 rows)',nonlinear[:,0],{'dimension 2':nonlinear[:,1]},'scatter',xlabel='Isomap dimension 1',ylabel='Isomap dimension 2'))
            out['metrics']['first_two_variance']=float(sum(pca.explained_variance_ratio_[:2]))
            out['interpretation'].append('Median imputation and standardization precede PCA. Isomap preserves neighborhood geometry; axes and distances differ from PCA. Projections are exploratory and establish no biological groups.')
        else:
            out['plots'].append(figure_plot('Physical activity and BMI',df.activity_hours_week,{'BMI (kg/m²)':df.BMI},'scatter',xlabel='Activity (hours/week)',ylabel='BMI (kg/m²)'))
            hist,edges=np.histogram(df.BMI.dropna(),bins=15)
            out['plots'].append(figure_plot('Adult BMI distribution',(edges[:-1]+edges[1:])/2,{'observations':hist},'bar',xlabel='BMI (kg/m²)',ylabel='Adult observations'))
            if tutorial==14:
                missing=df[required].isna().sum()
                if missing.any():
                    out['plots'].append(bars('Adult feature missingness',missing.index,missing.values,ylabel='Missing observed values',caption='Known adults only; descriptive plots use observed values, not imputed values.'))
                else:out.setdefault('visualization_notes',[]).append('All required features are observed in the selected adults; missingness counts remain in the table rather than a zero-only chart.')
                correlation=df[required+['BMI']].corr()
                out['plots'].append(heatmap('Adult measurement correlations',correlation.to_numpy(),correlation.index,correlation.columns,
                    limits=(-1,1),caption='Pairwise complete observations. BMI derives from height/weight; associations do not establish causation.'))
                out['plots'].append(behavioral_distributions(df,features))
                flags=out['tables']['outlier_inspection']
                if any(row['IQR_flags'] for row in flags):
                    out['plots'].append(bars('Adult feature IQR inspection',[row['feature'] for row in flags],[row['IQR_flags'] for row in flags],ylabel='Flagged observed values',caption='1.5×IQR inspection flags only; observations are not automatically removed.'))
                else:out.setdefault('visualization_notes',[]).append('No 1.5×IQR outlier flags in this sample; the zero-count inspection remains available in the table.')
            if tutorial==15:
                valid=df.dropna(subset=['BMI'])
                if len(valid)<20: raise ValueError('Need 20 adults with valid height and weight')
                train,test=train_test_split(valid,test_size=.25,random_state=42)
                model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LinearRegression()).fit(train[features],train.BMI)
                pred=model.predict(test[features])
                out['metrics'].update(MAE=float(mean_absolute_error(test.BMI,pred)),RMSE=float(np.sqrt(mean_squared_error(test.BMI,pred))),R2=float(r2_score(test.BMI,pred)),train_rows=len(train),test_rows=len(test))
                out['tables']['coefficients']=[{'feature':c,'BMI_change_per_training_SD':float(v)} for c,v in zip(features,model[-1].coef_)]
                out['tables']['regression_predictions']=records(pd.DataFrame({'actual_BMI':test.BMI.to_numpy(),'predicted_BMI':pred,'residual_BMI':test.BMI.to_numpy()-pred}))
                out['plots'].append(bars('Multivariable BMI coefficients',features,model[-1].coef_,ylabel='BMI units per training-feature SD',caption='Training-only imputation/scaling; adjusted associations in the fitted model, not causal effects.'))
                def bmi_residuals(ax):
                    ax.scatter(pred,test.BMI.to_numpy()-pred,s=16,alpha=.7)
                    ax.axhline(0,color='gray',linestyle='--')
                out['plots'].append(chart('Held-out BMI residuals',bmi_residuals,xlabel='Predicted BMI (kg/m²)',ylabel='Actual − predicted BMI (kg/m²)',caption='Same held-out adults and predictions as the reported MAE/RMSE.'))
                pairs=valid[['activity_hours_week','BMI']].dropna()
                if len(pairs)>3 and pairs.nunique().min()>1:
                    correlation=stats.pearsonr(pairs.activity_hours_week,pairs.BMI)
                    ci=correlation.confidence_interval()
                    out['metrics'].update(activity_pearson_r=float(correlation.statistic),activity_p=float(correlation.pvalue),correlation_CI_low=float(ci.low),correlation_CI_high=float(ci.high))
                out['plots'].append(figure_plot('Held-out BMI predictions',test.BMI,{'predicted BMI':pred},'scatter',xlabel='Actual BMI (kg/m²)',ylabel='Predicted BMI (kg/m²)'))
                strongest=features[int(np.argmax(np.abs(model[-1].coef_)))]
                out['interpretation'].append(f'Largest absolute standardized coefficient: {strongest}. Pearson inference assumes independent observations and an approximately bivariate-normal relationship. Confidence interval uses Fisher transformation.')
            out['interpretation'].append('BMI = weight_kg / height_m² only for valid measured values. Adults selected by known age ≥18; IQR flags are inspected, not automatically removed. Associations do not establish causation or justify health recommendations.')
    return out
