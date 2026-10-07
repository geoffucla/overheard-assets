#!/usr/bin/env python3
"""Repeated-phrase checker for Overheard in the Bay.

Usage:
  phrase_check.py check DRAFT.md HISTORY_DIR [HISTORY_DIR ...] [--last 10]
      Flags multi-word phrases in the draft that already appeared in recent editions
      (and phrases the draft repeats within itself).
  Signature phrases (desks/signatures.txt, set with --signatures FILE) are enforced instead of
  flagged: required in their section every time, allowed there, and forbidden elsewhere.
"""
import sys,re,glob,os,collections
STOP=set("a an the and or but of to in on at for with by from as is are was were be been it its this that these those he she they we you i his her their our your not no so if then than there here has have had do does did will would can could may might must about into over after before also just more most some any all each every very than which who whom what when where why how while".split())
def clean(md):
    out=[]
    for ln in md.splitlines():
        s=ln.strip()
        if not s or s.startswith('#') or s.startswith('>') or s.startswith('Curated by') or s.startswith('Designed for human'):
            continue
        s=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',s)
        s=s.replace('**','')
        s=re.sub(r'^(UP|DOWN):\s*','',s)
        out.append(s)
    return out
def toks(sentence_lines):
    """return list of (token_lower, is_name_or_number) per sentence"""
    sents=[]
    for ln in sentence_lines:
        for sent in re.split(r'(?<=[.!?])\s+',ln):
            words=sent.split()
            row=[]
            for i,w in enumerate(words):
                core=re.sub(r"^[^\w$%]+|[^\w$%]+$",'',w)
                if not core: continue
                low=core.lower()
                skip=bool(re.search(r'\d|\$|%',core)) or (i>0 and core[0].isupper())
                row.append((low,skip))
            if row: sents.append(row)
    return sents
def grams(sents,nmin=4,nmax=8):
    G=collections.defaultdict(int)
    for row in sents:
        L=len(row)
        for n in range(nmin,nmax+1):
            for i in range(L-n+1):
                seg=row[i:i+n]
                if any(s for _,s in seg): continue
                words=[w for w,_ in seg]
                if sum(1 for w in words if w not in STOP)<2: continue
                G[' '.join(words)]+=1
    return G
def load(dirs,last=None):
    files=[]
    for d in dirs: files+=sorted(glob.glob(os.path.join(d,'SCUTTLEBUTT_*.md')))
    files=sorted(set(files),key=lambda p:os.path.basename(p))
    if last: files=files[-last:]
    return files
def maximal(phrases):
    ps=sorted(phrases,key=len,reverse=True); keep=[]
    for p in ps:
        if not any(p in k for k in keep): keep.append(p)
    return keep
def read_sigs(path):
    sigs={}
    if path and os.path.exists(path):
        for ln in open(path):
            ln=ln.strip()
            if not ln or ln.startswith('#') or '|' not in ln: continue
            h,p=[x.strip() for x in ln.split('|',1)]
            sigs.setdefault(h.upper(),[]).append(p.lower())
    return sigs
def sections(md):
    cur='';out={}
    for ln in md.splitlines():
        if ln.startswith('## '): cur=ln[3:].strip().upper(); out[cur]=''; continue
        out[cur]=out.get(cur,'')+ln+'\n'
    return out
def sig_problems(md,sigs):
    probs=[];secs=sections(md)
    for head,phrases in sigs.items():
        for ph in phrases:
            if head in secs and ph not in secs[head].lower():
                probs.append(f'MISSING signature "{ph}" in section {head}')
            for other,txt in secs.items():
                if other!=head and other and ph in txt.lower():
                    probs.append(f'signature "{ph}" (belongs to {head}) also used in {other}')
    return probs
def main():
    a=sys.argv[1:]
    if not a: print(__doc__); return
    last=None
    if '--last' in a:
        i=a.index('--last'); last=int(a[i+1]); del a[i:i+2]
    sigfile=None
    if '--signatures' in a:
        i=a.index('--signatures'); sigfile=a[i+1]; del a[i:i+2]
    sigs=read_sigs(sigfile)
    def _core(p):
        w=p.split()
        while w and w[0] in STOP: w=w[1:]
        return ' '.join(w) or p
    sigset={_core(p) for v in sigs.values() for p in v}
    if a[0]=='check':
        draft=open(a[1]).read()
        files=[f for f in load(a[2:],last) if os.path.abspath(f)!=os.path.abspath(a[1])]
        dg=grams(toks(clean(draft)))
        hist=collections.defaultdict(set)
        for f in files:
            for k in grams(toks(clean(open(f).read()))): hist[k].add(os.path.basename(f))
        rep=[k for k in dg if k in hist and not any(sp in k or k in sp for sp in sigset)]
        inside=[k for k,v in dg.items() if v>=2 and not any(sp in k or k in sp for sp in sigset)]
        print(f"checked against {len(files)} earlier editions")
        r=maximal(rep)
        print(f"REPEATED FROM EARLIER EDITIONS ({len(r)}):")
        for k in sorted(r): print(f"  \"{k}\"  (in {len(hist[k])}: {', '.join(sorted(hist[k]))[:80]})")
        i2=maximal(inside)
        print(f"REPEATED WITHIN THIS DRAFT ({len(i2)}):")
        for k in sorted(i2): print(f"  \"{k}\"")
        sp=sig_problems(draft,sigs)
        print(f"SIGNATURE PHRASE PROBLEMS ({len(sp)}):")
        for x in sp: print("  "+x)
        sys.exit(1 if (r or i2 or sp) else 0)
main()
