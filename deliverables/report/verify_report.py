"""Independent arithmetic plus final PDF structure/font/link audit."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,re,hashlib,subprocess
import fitz
ROOT=Path(__file__).parent
MODEL_DIR=next(p for p in [ROOT/'basis',ROOT.parent/'cbp-v4',ROOT.parent/'v4'] if (p/'cbp_model.py').exists())
sys.path.insert(0,str(MODEL_DIR))
import cbp_model as m
from dataclasses import replace
U=[[F(1),F(0),F(1,4)],[F(3,4),F(7,10),F(1,2)],[F(0),F(1),F(5,8)]]
W=[[F(7,10),F(1,10),F(2,10)],[F(5,10),F(3,10),F(2,10)],[F(2,10),F(6,10),F(2,10)],[F(1,10),F(8,10),F(1,10)]]
independent=0
for used,w in zip([5000,6800,8200,9300],W):
    result=m.select(state=replace(m.State(),used=used))
    for candidate,u in zip('ABC',U):
        expected=sum(a*b for a,b in zip(u,w))
        assert abs(result['scores'][candidate]['RPS']-float(expected))<1e-12
        independent+=1
assert (140-100)*10000/F(400-200)*1000==2000000
assert (140-110)*10000/F(260-200)*1000==5000000
assert round(float((110-100)*10000/F(400-260)*1000)/10000,2)==71.43
assert (10000-8200-200)==1600
assert (10000-(8200+230))==1570
assert F(8200+230,10000)*100==F(843,10)
assert m.select(state=replace(m.State(),cost_limit=120))['scores']['B']['RPS']==.7
expected_hash='917d73b57889597b5c3a037aae9db4dc1c8bc2f4dcb724835b1d63af3a1c73cc'
assert hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()==expected_hash
pdf_path=ROOT/'cbp-idea-report.pdf';doc=fitz.open(pdf_path)
toc=json.loads((ROOT/'contents.json').read_text());assert len(doc)==len(toc)==27
norm=lambda x:re.sub(r'\s+','',x)
for i,page in enumerate(doc):
    txt=page.get_text();assert norm(toc[i]['title']) in norm(txt)
    assert '\ufffd' not in txt
    assert len(txt)>250
    for word in page.get_text('words'):
        assert word[0]>=0 and word[1]>=0 and word[2]<=page.rect.width+.1 and word[3]<=page.rect.height+.1
links=doc[2].get_links()
assert len(links)==25
assert sorted(v['page'] for v in links)==[i for i in range(27) if i not in [0,2]]
font_output=subprocess.check_output(['pdffonts',str(pdf_path)],text=True)
fonts=re.findall(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$',font_output,re.M)
assert fonts and all(embedded=='yes' and unicode=='yes' for embedded,subset,unicode in fonts)
layout=json.loads((ROOT/'layout_audit.json').read_text());assert len(layout)==27 and all(not p['overflow'] for p in layout)
report={'pages':27,'independent_RPS_checks':independent,'model_condition_checks':m.verify(),'toc_links_verified':len(links),'font_records_embedded_with_unicode':len(fonts),'layout_overflow':0,'pdf_page_title_checks':27,'pdf_sha256':hashlib.sha256(pdf_path.read_bytes()).hexdigest(),'model_sha256':expected_hash,'visual_review':'27 rendered pages inspected; source-table wrapping and chart legend corrected','limits':'Synthetic cases; no field efficacy or novelty proof.'}
(ROOT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
