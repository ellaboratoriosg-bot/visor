# Vectores del cartel nuevo: base blanca (unión), letras verdes, piezas doradas
import json, numpy as np, cv2
exec(open('/home/claude/visor/_herramientas/vec.py').read().split("clips={")[0].replace("SVG=sys.argv[1]","SVG='new.svg'"))
clips={c.get('id'):c.find(NS+'path') for c in r.iter(NS+'clipPath')}
pieces=[]
# base blanca: unión raster de los 2 paths blancos (evenodd), a 4 px/pt
K=4.0
whites=[p for p in r.iter(NS+'path') if p.get('fill')=='rgb(100%, 100%, 100%)']
allw=np.concatenate([np.array(rg) for p in whites for rg in rings_of(p.get('d'))])
ox,oy=allw[:,0].min()-10,allw[:,1].min()-10
W=int((allw[:,0].max()-ox+10)*K);H=int((allw[:,1].max()-oy+10)*K)
mask=np.zeros((H,W),np.uint8)
for p in whites:
    m=np.zeros((H,W),np.uint8)
    for rg in rings_of(p.get('d'),0.5):
        t=np.zeros((H,W),np.uint8);cv2.fillPoly(t,[np.round((np.array(rg)-[ox,oy])*K*16).astype(np.int32)],255,cv2.LINE_8,4);m^=t
    mask|=m
cs,hier=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
for i,c in enumerate(cs):
    if hier[0][i][3]!=-1: continue
    rings=[c]; ch=hier[0][i][2]
    while ch!=-1:
        if cv2.contourArea(cs[ch])>3200: rings.append(cs[ch])
        ch=hier[0][ch][0]
    if cv2.contourArea(c)<1000: continue
    rr=[]
    for c2 in rings:
        a=cv2.approxPolyDP(c2,1.0,True)[:,0,:].astype(float)
        rr.append(((a+0.5)/K+[ox,oy]).tolist())
    pieces.append({'grupo':'base','mat':'blanco','rings':rr})
nb=len(pieces)
green=[p for p in r.iter(NS+'path') if (p.get('fill') or '').startswith('rgb(7.45')]
for p in green: pieces.append({'grupo':'letras','mat':'verde','rings':rings_of(p.get('d'))})
for k in (3,5,7,9,11,13,15): pieces.append({'grupo':'letras','mat':'dorado','rings':rings_of(clips['clip-%d'%k].get('d'))})
for pc in pieces:
    a=np.concatenate([np.array(x) for x in pc['rings']]); print(pc['grupo'],pc['mat'],len(pc['rings']),'anillos',sum(len(x) for x in pc['rings']),'pts','x %.0f-%.0f y %.0f-%.0f'%(a[:,0].min(),a[:,0].max(),a[:,1].min(),a[:,1].max()))
json.dump(pieces,open('piezas.json','w'))
