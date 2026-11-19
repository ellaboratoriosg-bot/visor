import xml.etree.ElementTree as ET, re, json, sys
import numpy as np
SVG=sys.argv[1]
NS='{http://www.w3.org/2000/svg}'
r=ET.parse(SVG).getroot()
def rings_of(d,step=1.2):
    toks=re.findall(r'[MLCZ]|-?[\d.]+(?:e-?\d+)?',d)
    rings=[];cur=[];i=0;cmd=None;pos=None
    while i<len(toks):
        t=toks[i]
        if t in 'MLCZ': cmd=t;i+=1
        if cmd=='Z':
            if len(cur)>2: rings.append(cur)
            cur=[];cmd=None;continue
        if cmd=='M':
            if len(cur)>2: rings.append(cur)
            pos=(float(toks[i]),float(toks[i+1]));cur=[pos];i+=2;cmd='L'
        elif cmd=='L':
            p=(float(toks[i]),float(toks[i+1]));i+=2
            if p!=cur[-1]: cur.append(p)
        elif cmd=='C':
            a=np.array([cur[-1]]+[(float(toks[i+2*k]),float(toks[i+2*k+1])) for k in range(3)]);i+=6
            L=np.linalg.norm(np.diff(a,axis=0),axis=1).sum();n=max(4,int(L/step))
            for tt in np.linspace(0,1,n+1)[1:]:
                b=(1-tt)**3*a[0]+3*(1-tt)**2*tt*a[1]+3*(1-tt)*tt**2*a[2]+tt**3*a[3]
                cur.append(tuple(b))
        else: i+=1
    if len(cur)>2: rings.append(cur)
    out=[]
    for rg in rings:
        if np.allclose(rg[0],rg[-1]): rg=rg[:-1]
        out.append(rg)
    return out
clips={c.get('id'):c.find(NS+'path') for c in r.iter(NS+'clipPath')}
pieces=[]
green=[p for p in r.iter(NS+'path') if (p.get('fill') or '').startswith('rgb(7.45')]
for p in green: pieces.append({'grupo':'arriba','mat':'verde','rings':rings_of(p.get('d'))})
pieces.append({'grupo':'arriba','mat':'dorado','rings':rings_of(clips['clip-3'].get('d'))})
for k in (7,9,11,13,15,17): pieces.append({'grupo':'design','mat':'dorado','rings':rings_of(clips['clip-%d'%k].get('d'))})
allp=np.concatenate([np.array(rg) for pc in pieces for rg in pc['rings']])
print(len(pieces),'piezas; bbox x %.1f-%.1f y %.1f-%.1f'%(allp[:,0].min(),allp[:,0].max(),allp[:,1].min(),allp[:,1].max()))
for pc in pieces:
    a=np.concatenate([np.array(x) for x in pc['rings']]); print(pc['grupo'],pc['mat'],len(pc['rings']),'anillos','x %.0f-%.0f y %.0f-%.0f'%(a[:,0].min(),a[:,0].max(),a[:,1].min(),a[:,1].max()))
json.dump(pieces,open('piezas.json','w'))
