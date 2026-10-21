from pathlib import Path
import hashlib,zipfile
R=Path(__file__).parent
files=[p for p in sorted(R.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name not in ['SHA256SUMS.txt','cbp-final-package.zip']]
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(R))+'\n' for p in files))
with zipfile.ZipFile(R/'cbp-final-package.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in files+[R/'SHA256SUMS.txt']:z.write(p,'CBP_FINAL/'+str(p.relative_to(R)))
with zipfile.ZipFile(R/'cbp-final-package.zip') as z:
    assert z.testzip() is None
    for p in files:assert z.read('CBP_FINAL/'+str(p.relative_to(R)))==p.read_bytes()
print('Packaged and verified',len(files)+1,'files')
