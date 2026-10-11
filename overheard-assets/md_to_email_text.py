import sys,re,os,json
_ED=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'regions','editions.json')))[os.environ.get('EDITION','bay')]
# usage: md_to_email_text.py md_path date_text out_txt
md,date,out=sys.argv[1:4]
desc="Your secret to being clued in and quotable before your first meeting."
import os
m=re.search(r"(\d{4}-\d{2}-\d{2})",os.path.basename(md))
WEB=(_ED["site"]+"/editions/"+m.group(1)+"/") if m else _ED["site"]+"/"
L=["View this on the web: "+WEB,"Past issues: "+_ED["site"]+"/archive/","",_ED["name"].upper(),date.upper(),desc,"="*60,""]
for ln in open(md).read().splitlines():
    s=ln.strip()
    if not s or s.startswith('# ') or s.startswith(('Curated by','Designed for human consumption','Designed by hand','As heard by Always-On Listening')): continue
    if s.startswith('## '):
        L+=["",s[3:].upper(),"-"*len(s[3:])]; continue
    if s.startswith('~ '):
        L+=[s[2:],""]; continue
    more=s.startswith('> ')
    if more: s=s[2:]
    s=re.sub(r'\*\*(.+?)\*\*',r'\1',s)
    s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 (\2)',s)
    s=re.sub(r'^(UP|DOWN): ',lambda m:'['+m.group(1)+'] ',s)
    if more:
        if L and L[-1]=="": L.pop()
        L.append("  "+s)
    else:
        L.append(s)
    L.append("")
L+=["","Informed, opinionated, occasionally wrong. Verify before repeating at dinner.","Designed by hand, written by Claude.","","All views expressed are strictly AI generated and are not those of any human.","","(c) "+(m.group(1)[:4] if m else "2026")+" Humans Not Included Media, publisher of "+_ED["name"]+". All rights reserved.","You are receiving this because you subscribed to Terms Undisclosed: Bay Blend.","Unsubscribe: {{{RESEND_UNSUBSCRIBE_URL}}}"]
open(out,'w').write("\n".join(L))
