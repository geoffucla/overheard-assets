import sys,re
# usage: md_to_email_text.py md_path date_text out_txt
md,date,out=sys.argv[1:4]
desc="As heard by Always-On Listening. Designed for human consumption."
import os
m=re.search(r"(\d{4}-\d{2}-\d{2})",os.path.basename(md))
WEB=("https://bay.overheardnews.com/editions/"+m.group(1)+"/") if m else "https://bay.overheardnews.com/"
L=["View this on the web: "+WEB,"Past issues: https://bay.overheardnews.com/archive/","","OVERHEARD IN THE BAY",date.upper(),desc,"="*60,""]
for ln in open(md).read().splitlines():
    s=ln.strip()
    if not s or s.startswith('# ') or s.startswith(('Curated by','Designed for human consumption','As heard by Always-On Listening')): continue
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
L+=["","Informed, opinionated, occasionally wrong. Verify before repeating at dinner.","","Written by Claude, an AI model made by Anthropic. All views expressed are strictly AI generated and are not the views of any human on, in, or around the loop, including the one who designed this for human consumption.","","(c) "+(m.group(1)[:4] if m else "2026")+" Humans Not Included Media, publisher of Overheard in the Bay. All rights reserved.","You are receiving this because you subscribed to Overheard in the Bay.","Unsubscribe: {{{RESEND_UNSUBSCRIBE_URL}}}"]
open(out,'w').write("\n".join(L))
