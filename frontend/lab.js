(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const methods = {
    1:'Inspect local NIfTI cases and available MRI modalities.',2:'Clean invalid intensities, standardize nonbackground voxels and normalize an MRI slice.',3:'Inspect missing modalities and a unique case/modality inventory without deleting files.',4:'Compare CLAHE, Gaussian restoration, Otsu intensity partitioning and lossy JPEG.',5:'Match real MRI slices using SIFT and RANSAC, or run a compact patient-separated CNN training and inference experiment.',6:'Visualize same-patient MRI modalities, available segmentation and intensity distribution.',
    7:'Predict admissions from known calendar features using Ridge regression. Train on the first 80% of days and evaluate on the remaining 20%.',8:'Validate operational data, summarize admissions, occupancy and costs, and compare departments.',9:'Extend KPI analysis with trends, variance, Kruskal group comparisons and a computed occupancy priority ranking.',10:'Fit TF-IDF and logistic regression on training texts only; evaluate held-out texts. Cluster training documents with K-means.',11:'Find condition, medication, investigation and measurement mentions with a transparent lexicon and regular expressions.',12:'Rank documents with TF-IDF cosine similarity; disambiguate MS and RA using explicit context cues.',13:'Select numeric adult measurements, impute missing values, standardize and compare PCA with Isomap.',14:'Select adults by known age, calculate BMI in kg/m² and inspect distributions, missingness, IQR outliers and correlations.',15:'Fit a multivariable BMI regression with training-only imputation and scaling; evaluate held-out data and examine standardized coefficients and Pearson correlation confidence intervals.'
  };
  let tutorials = [], selected = 7, lastResult = null, busy = false;
  function node(tag, text, cls) { const el=document.createElement(tag); if(text!==undefined)el.textContent=text; if(cls)el.className=cls; return el; }
  function fmt(v){ return typeof v==='number' ? (Number.isInteger(v)?String(v):v.toLocaleString(undefined,{maximumFractionDigits:4})) : String(v ?? '—'); }
  function status(message,error=false){ $('status').textContent=message; $('status').className=error?'error':''; }
  function select(id){
    selected=id; lastResult=null; $('results').replaceChildren(); $('download').hidden=true;
    const t=tutorials.find(t=>t.id===id); if(!t)return;
    for(const el of $('tutorialNav').children){el.classList.toggle('active',Number(el.dataset.id)===id);el.setAttribute('aria-current',Number(el.dataset.id)===id?'page':'false');}
    $('title').textContent=t.title; $('tutorialNumber').textContent=`TUTORIAL ${String(id).padStart(2,'0')}`; $('method').textContent=methods[id];
    $('datasetInfo').textContent=id<=6?t.dataset_status+' · Local BraTS MRI assets preserved.': 'Default: deterministic synthetic demonstration (seed 42), not real patient data. Choose a compatible CSV to analyze your own data.';
    $('schema').textContent=id<=6?'Source: BraTS2020/ local NIfTI cases.':'Required CSV columns: '+t.required_columns.join(', ')+(id>=7&&id<=9?' · Optional: department, occupied_beds + capacity, cost':'');
    $('fileControls').hidden=id<=6; $('textControls').hidden=![10,11,12].includes(id); $('queryControls').hidden=id!==12; $('clusterControls').hidden=id!==10; $('workloadControls').hidden=id!==7; $('cnn').hidden=id!==5;
    $('clusters').disabled=id!==10; $('workload').disabled=id!==7;
    $('exampleLink').href=`/api/tutorials/${id}/example`; $('csv').value=''; $('runState').textContent='Ready to run';
    location.hash=`T${id}`; status('Ready. Results will be computed when you run the analysis.');
  }
  function render(result,cnn=false){
    lastResult=result;
    globalThis.HERResults.render($('results'),result,cnn);
    $('download').hidden=false;
  }
  async function analyze(cnn=false){
    if(busy)return; busy=true; const id=selected;
    $('run').disabled=true; $('cnn').disabled=true; for(const b of $('tutorialNav').children)b.disabled=true;
    $('results').replaceChildren();$('download').hidden=true;$('runState').textContent='Computing…';status(cnn?'Training a compact CNN on local MRI slices; please wait…':'Computing analysis…');
    try{
      const options={text:[10,11,12].includes(id)?$('clinicalText').value:'',query:id===12?$('query').value:'diabetes glucose',clusters:id===10?Number($('clusters').value):3,workload:id===7?Number($('workload').value):8};
      const file=$('csv').files[0]; let url=`/api/tutorials/${id}/run`,body=JSON.stringify(options),type='application/json';
      if(cnn){url='/api/cnn/demo';body='{}';}
      else if(file&&id>=7){
        if(!file.name.toLowerCase().endsWith('.csv'))throw Error('Choose a .csv file.');if(file.size>2*1024*1024)throw Error('CSV exceeds the 2 MB limit.');
        url=`/api/tutorials/${id}/upload?`+new URLSearchParams(options);body=await file.text();type='text/csv';
      }
      const response=await fetch(url,{method:'POST',headers:{'Content-Type':type},body});
      const result=await response.json();if(!response.ok)throw Error(typeof result.detail==='string'?result.detail:JSON.stringify(result.detail));
      render(result,cnn);$('runState').textContent='Run completed';status(`T${id} completed. Displaying computed results.`);
      const nav=$('tutorialNav').querySelector(`[data-id="${id}"]`); if(nav){nav.title='Analysis completed in this session';nav.querySelector('small').textContent='Run ✓';}
    }catch(error){$('runState').textContent='Run failed';status(error instanceof TypeError?'Cannot connect to the backend. Start run_server.bat and open http://127.0.0.1:8000.':error.message,true);}
    finally{busy=false;$('run').disabled=false;$('cnn').disabled=false;for(const b of $('tutorialNav').children)b.disabled=false;}
  }
  $('analysisForm').addEventListener('submit',e=>{e.preventDefault();analyze();});$('cnn').addEventListener('click',()=>analyze(true));
  $('download').addEventListener('click',()=>{if(!lastResult)return;const a=node('a');const url=URL.createObjectURL(new Blob([JSON.stringify(lastResult,null,2)],{type:'application/json'}));a.href=url;a.download=`T${selected}_analysis.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  async function init(){
    try{
      const [health,metadata]=await Promise.all([fetch('/api/health'),fetch('/api/tutorials')]);
      if(!health.ok||!metadata.ok)throw Error('Backend returned an error'); const h=await health.json();tutorials=(await metadata.json()).tutorials;
      $('connection').textContent=`● Connected · ${h.cases_found} MRI cases`;
      for(const t of tutorials){const b=node('button');b.type='button';b.dataset.id=t.id;b.append(node('b',`T${t.id}`),node('span',t.title),node('small','Ready'));b.title=`${t.status} · ${t.dataset_status}`;b.addEventListener('click',()=>select(t.id));$('tutorialNav').append(b);}
      const hash=Number(location.hash.replace('#T',''));select(hash>=1&&hash<=15?hash:7);
    }catch(e){$('connection').textContent='● Backend unavailable';$('run').disabled=true;status('Cannot connect to backend. Run run_server.bat and open http://127.0.0.1:8000 (avoid opening this HTML directly).',true);}
  }
  init();
})();
