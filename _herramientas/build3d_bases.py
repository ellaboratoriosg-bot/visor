import json, struct, io, numpy as np
from scipy.spatial import Delaunay
from PIL import Image, ImageDraw, ImageFilter
P=json.load(open('piezas.json'))
IN=0.0254
X0,X1=179.9,1800.5
allp=np.concatenate([np.array(r) for p in P for r in p['rings']]); X0,X1=allp[:,0].min(),allp[:,0].max()
S=IN/72.0                     # dibujo a escala 1:1 (1 pt = 1/72 in)
YBOT=allp[:,1].max()
print('ancho %.2f in x alto %.2f in'%((X1-X0)*S/IN,(YBOT-allp[:,1].min())*S/IN))
CX=(X0+X1)/2; CY=(allp[:,1].min()+YBOT)/2
T=0.25*IN; GAP=1.0*IN
def tf(pt): pt=np.asarray(pt,float); return np.stack([(pt[...,0]-CX)*S,-(pt[...,1]-CY)*S],-1)
def densify(r,step):
    r=np.array(r);out=[]
    for a,b in zip(r,np.roll(r,-1,0)):
        n=max(1,int(np.ceil(np.linalg.norm(b-a)/step)))
        out+= [a+(b-a)*k/n for k in range(n)]
    return np.array(out)
def inside(pts,rings):
    c=np.zeros(len(pts),bool)
    for r in rings:
        a=r;b=np.roll(r,-1,0)
        for (x1,y1),(x2,y2) in zip(a,b):
            cond=((y1>pts[:,1])!=(y2>pts[:,1]))
            with np.errstate(divide='ignore',invalid='ignore'):
                xi=(x2-x1)*(pts[:,1]-y1)/(y2-y1)+x1
            c^=cond&(pts[:,0]<xi)
    return c
def area(r): x,y=r[:,0],r[:,1]; return 0.5*np.sum(x*np.roll(y,-1)-np.roll(x,-1)*y)
def piece_mesh(rings_pt,z0,z1):
    rings=[tf(densify(r,2.5)) for r in rings_pt]
    pts=np.concatenate(rings); tri=Delaunay(pts).simplices
    cen=pts[tri].mean(1); tri=tri[inside(cen,rings)]
    # orientar CCW
    a=pts[tri]; cr=(a[:,1,0]-a[:,0,0])*(a[:,2,1]-a[:,0,1])-(a[:,1,1]-a[:,0,1])*(a[:,2,0]-a[:,0,0])
    tri[cr<0]=tri[cr<0][:,[0,2,1]]
    pa=sum(abs(area(r))*(1 if inside(np.array([r.mean(0)+0]),[q for q in rings if q is not r]).sum()%2==0 else 1) for r in rings)
    tri_area=np.abs(cr).sum()/2
    target=abs(sum(area(r)*(1 if np.sign(area(r))==np.sign(area(max(rings,key=lambda q:abs(area(q))))) else 1) for r in rings))
    V=[];N=[];I=[]
    def add(v,n,idx):
        b=len(V); V.extend(v); N.extend(n); I.extend((np.asarray(idx)+b).tolist())
    n=len(pts)
    add(np.c_[pts,np.full(n,z1)],[[0,0,1]]*n,tri.reshape(-1))
    add(np.c_[pts,np.full(n,z0)],[[0,0,-1]]*n,tri[:,[0,2,1]].reshape(-1))
    for r in rings:
        a=r;b=np.roll(r,-1,0);d=b-a;L=np.linalg.norm(d,axis=1,keepdims=True);nrm=np.c_[d[:,1],-d[:,0]]/np.maximum(L,1e-12)
        mid=(a+b)/2; probe=mid+nrm*1e-4
        flip=inside(probe,rings); nrm[flip]*=-1
        for k in range(len(a)):
            p0,p1=a[k],b[k];nn=[nrm[k,0],nrm[k,1],0]
            q=[[*p0,z0],[*p1,z0],[*p1,z1],[*p0,z1]]
            # orientar para que la normal salga
            e1=np.subtract(q[1],q[0]);e2=np.subtract(q[2],q[0]);c=np.cross(e1,e2)
            idx=[0,1,2,0,2,3] if np.dot(c,nn)>0 else [0,2,1,0,3,2]
            add(q,[nn]*4,idx)
    return np.array(V,np.float32),np.array(N,np.float32),np.array(I,np.uint32),tri_area
# --- geometría: base blanca separada de la pared, letras encima de la base
groups={}
for p in P:
    z0,z1=(GAP,GAP+T) if p['grupo']=='base' else (GAP+T,GAP+2*T)
    v,n,i,ta=piece_mesh(p['rings'],z0,z1)
    key=(p['grupo'],p['mat']); g=groups.setdefault(key,[[],[],[],0])
    g[2].append(i+g[3]); g[0].append(v); g[1].append(n); g[3]+=len(v)
LUZ=(252,250,168)   # color del resplandor del diseño nuevo
# --- halo detrás de las bases
up=[p for p in P if p['grupo']=='base']
ua=np.concatenate([np.array(r) for p in up for r in p['rings']])
M=110
hx0,hy0,hx1,hy1=ua[:,0].min()-M,ua[:,1].min()-M,ua[:,0].max()+M,ua[:,1].max()+M
W=2048;H=int(W*(hy1-hy0)/(hx1-hx0)); H=(H+3)//4*4
k=float(W/(hx1-hx0))
def rmask(pcs,x0,y0,kk,WW,HH):
    m=np.zeros((HH,WW),np.uint8)
    for p in pcs:
        q=np.zeros((HH,WW),np.uint8)
        for r in p['rings']:
            rr=Image.new('L',(WW,HH),0);ImageDraw.Draw(rr).polygon([((x-x0)*kk,(y-y0)*kk) for x,y in r],fill=255);q^=np.array(rr)
        m|=q
    return m
mask=Image.fromarray(rmask(up,hx0,hy0,k,W,H))
g1=np.array(mask.filter(ImageFilter.GaussianBlur(12*k)),float)
g2=np.array(mask.filter(ImageFilter.GaussianBlur(32*k)),float)
a=(255*(1-np.exp(-np.clip(g1*1.6+g2*1.3,0,255)/75))).clip(0,255)
rgb=np.zeros((H,W,3));rgb[...]=LUZ
halo=Image.fromarray(np.dstack([rgb,a]).astype(np.uint8),'RGBA')
buf=io.BytesIO();halo.save(buf,'PNG',optimize=True);halo_png=buf.getvalue()
hq=tf(np.array([[hx0,hy1],[hx1,hy1],[hx1,hy0],[hx0,hy0]]));hz=0.002
# --- GLB
def lin(c): c=np.array(c)/255; return list(np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4))+[1]
bin_=bytearray();bviews=[];accs=[]
def pushbuf(b,target=None):
    while len(bin_)%4: bin_.append(0)
    off=len(bin_);bin_.extend(b);bv={'buffer':0,'byteOffset':off,'byteLength':len(b)}
    if target: bv['target']=target
    bviews.append(bv);return len(bviews)-1
def acc(arr,typ,ctype,target,minmax=False):
    bv=pushbuf(arr.tobytes(),target);a={'bufferView':bv,'componentType':ctype,'count':int(arr.shape[0] if arr.ndim>1 else arr.size),'type':typ}
    if minmax: a['min']=arr.min(0).tolist();a['max']=arr.max(0).tolist()
    accs.append(a);return len(accs)-1
mats=[
 {'name':'Acrilico verde','pbrMetallicRoughness':{'baseColorFactor':lin((19,69,70)),'metallicFactor':0.0,'roughnessFactor':0.5},'extensions':{'KHR_materials_specular':{'specularFactor':0.35}}},
 {'name':'Acrilico dorado','pbrMetallicRoughness':{'baseColorFactor':lin((214,170,84)),'metallicFactor':1.0,'roughnessFactor':0.28}},
 {'name':'Luz calida','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0.0,'roughnessFactor':1.0},'alphaMode':'BLEND','doubleSided':False,'extensions':{'KHR_materials_unlit':{}}},
 {'name':'Acrilico blanco','pbrMetallicRoughness':{'baseColorFactor':lin((246,246,244)),'metallicFactor':0.0,'roughnessFactor':0.4},'extensions':{'KHR_materials_specular':{'specularFactor':0.35}}},
]
matidx={'verde':0,'dorado':1,'blanco':3}
meshes=[];nodes=[]
for name,keys in (('Base blanca',[('base','blanco')]),('Letras',[('letras','verde'),('letras','dorado')])):
    prims=[]
    for key in keys:
        v,n,i=groups[key][:3]; V=np.concatenate(v);N=np.concatenate(n);I=np.concatenate(i).astype(np.uint32)
        prims.append({'attributes':{'POSITION':acc(V,'VEC3',5126,34962,True),'NORMAL':acc(N,'VEC3',5126,34962)},'indices':acc(I,'SCALAR',5125,34963),'material':matidx[key[1]]})
    meshes.append({'name':name,'primitives':prims});nodes.append({'name':name,'mesh':len(meshes)-1})
HV=np.c_[hq,np.full(4,hz)].astype(np.float32);HN=np.array([[0,0,1]]*4,np.float32);HT=np.array([[0,1],[1,1],[1,0],[0,0]],np.float32);HI=np.array([0,1,2,0,2,3],np.uint32)
meshes.append({'name':'Luz','primitives':[{'attributes':{'POSITION':acc(HV,'VEC3',5126,34962,True),'NORMAL':acc(HN,'VEC3',5126,34962),'TEXCOORD_0':acc(HT,'VEC2',5126,34962)},'indices':acc(HI,'SCALAR',5125,34963),'material':2}]})
nodes.insert(0,{'name':'Luz','mesh':len(meshes)-1})
imgbv=pushbuf(halo_png)
while len(bin_)%4: bin_.append(0)
gl={'asset':{'version':'2.0','generator':'El Laboratorio SG'},'extensionsUsed':['KHR_materials_unlit','KHR_materials_specular'],'scene':0,'scenes':[{'name':'Hair Transplant Design','nodes':list(range(len(nodes)))}],
 'nodes':nodes,'meshes':meshes,'materials':mats,'accessors':accs,'bufferViews':bviews,'buffers':[{'byteLength':len(bin_)}],
 'images':[{'bufferView':imgbv,'mimeType':'image/png'}],'textures':[{'source':0,'sampler':0}],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}]}
js=json.dumps(gl,separators=(',',':')).encode()
while len(js)%4: js+=b' '
glb=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(bin_))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(bin_),0x004E4942)+bytes(bin_)
open('modelo.glb','wb').write(glb);print('GLB %.1f MB'%(len(glb)/1e6))
# --- PNGs modo foto
pad=130;bx0,by0=X0-pad,allp[:,1].min()-pad;bx1,by1=X1+pad,YBOT+pad
WW=2400;HH=int(WW*(by1-by0)/(bx1-bx0));kk=float(WW/(bx1-bx0))
gx=np.linspace(0,1,WW)[None,:]
gold=np.dstack([170+70*np.sin(gx*9)**2,128+60*np.sin(gx*9)**2,50+40*np.sin(gx*9)**2])*np.ones((HH,1,1))
bm=rmask(up,bx0,by0,kk,WW,HH)
def compose(on):
    out=np.zeros((HH,WW,4),float)
    def over(rgb,a):
        a=a[...,None]/255.0;oa=out[...,3:]/255.0;na=a+oa*(1-a);out[...,:3]=np.where(na>0,(rgb*a+out[...,:3]*oa*(1-a))/np.maximum(na,1e-6),0);out[...,3:]=na*255
    sh=np.array(Image.fromarray(np.roll(np.roll(bm,int(14*kk*0.3),0),int(8*kk*0.3),1)).filter(ImageFilter.GaussianBlur(9*kk)),float)*(0.10 if on else 0.30)
    over(np.zeros(3),sh)
    if on:
        g1=np.array(Image.fromarray(bm).filter(ImageFilter.GaussianBlur(12*kk)),float);g2=np.array(Image.fromarray(bm).filter(ImageFilter.GaussianBlur(32*kk)),float)
        over(np.array(LUZ,float),255*(1-np.exp(-np.clip(g1*2.2+g2*1.4,0,255)/90)))
    over(np.array([250,250,248.]),bm.astype(float))
    for p in P:
        if p['grupo']=='base': continue
        m=rmask([p],bx0,by0,kk,WW,HH).astype(float)
        sh2=np.array(Image.fromarray(np.roll(m.astype(np.uint8),2,0)).filter(ImageFilter.GaussianBlur(1.5*kk)),float)*0.25
        over(np.zeros(3),sh2)
        over(np.array([19,69,70.]) if p['mat']=='verde' else gold,m)
    return Image.fromarray(out.clip(0,255).astype(np.uint8),'RGBA')
compose(True).save('logo-encendido.png',optimize=True);compose(False).save('logo-apagado.png',optimize=True)
