"""Rebuild numerical results, figures and article; never modify index.qmd."""
from pathlib import Path
import csv, hashlib, io, json, re, subprocess, sys
import importlib.metadata
import platform
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'result'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
 'axes.spines.right':False,'figure.facecolor':'#ffffff','axes.facecolor':'#ffffff',
 'axes.labelcolor':'#253343','text.color':'#253343','svg.fonttype':'none','svg.hashsalt':'blog1-pca'})
TEAL, RED, BLUE, GREY = '#478578','#b65b3c','#2f6276','#dedede'

def write_if_changed(path, content):
    path = Path(path)
    payload = content.encode('utf-8') if isinstance(content, str) else content
    if path.exists() and path.read_bytes() == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return True


def save(fig, name):
    for extension in ['svg', 'png']:
        buffer = io.BytesIO()
        options = {'metadata': {'Date': None}} if extension == 'svg' else {'dpi': 300}
        fig.savefig(buffer, format=extension, bbox_inches='tight', **options)
        write_if_changed(OUT / 'figures' / f'{name}.{extension}', buffer.getvalue())
    plt.close(fig)


def csvwrite(path, header, rows):
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    write_if_changed(path, buffer.getvalue())


def axes2d(ax,lim):
    ax.axhline(0,color='#ddd5ca',lw=.8); ax.axvline(0,color='#ddd5ca',lw=.8)
    ax.set(xlim=lim,ylim=lim,xlabel='Horizontal coordinate',ylabel='Vertical coordinate')
    ax.set_aspect('equal'); ax.grid(alpha=.12)

iris=load_iris()
rawpath=ROOT/'data/iris.csv'
header=['observation_id','sepal_length_cm','sepal_width_cm','petal_length_cm','petal_width_cm','species']
if not rawpath.exists():
    csvwrite(rawpath,header,([i+1,*row,iris.target_names[iris.target[i]]] for i,row in enumerate(iris.data)))
with rawpath.open(encoding='utf-8') as f: rows=list(csv.DictReader(f))
X=np.array([[float(r['petal_length_cm']),float(r['petal_width_cm'])] for r in rows])
mu=X.mean(0); Z=X-mu; S=Z.T@Z/(len(X)-1)
e,V=np.linalg.eigh(S); order=np.argsort(e)[::-1]; e=e[order]; V=V[:,order]
if V[0,0]<0: V[:,0]*=-1
if V[0,1]<0: V[:,1]*=-1
scores=Z@V; recon=mu+np.outer(scores[:,0],V[:,0]); residual=X-recon
dist=np.linalg.norm(residual,axis=1); ratio=e/e.sum()
theta=np.linspace(0,np.pi,18001); W=np.stack([np.cos(theta),np.sin(theta)],axis=1)
variance=np.einsum('ij,jk,ik->i',W,S,W)
angle=np.degrees(np.arctan2(V[1,0],V[0,0]))
# Use the same observed covariance matrix for geometry and PCA.
v1, v2 = V[:,0], V[:,1]
fig,axs=plt.subplots(1,2,figsize=(10.6,4.8),layout='constrained')
ax=axs[0]; axes2d(ax,(-1.3,4.1)); ax.set_title('A. Covariance eigenvectors keep their lines',loc='left',fontsize=11,pad=12)
for vector,color,label in [(v1,TEAL,'v1'),(v2,RED,'v2'),(np.array([0.,1.]),BLUE,'u')]:
    after=S@vector
    ax.annotate('',xy=vector,xytext=(0,0),arrowprops=dict(arrowstyle='->',color=color,lw=1.8,linestyle='--'))
    ax.annotate('',xy=after,xytext=(0,0),arrowprops=dict(arrowstyle='->',color=color,lw=2.3))
    if label=='v1':
        ax.text(.9,.19,'v1',color=color,fontsize=9)
        ax.text(2.12,1.6,f'S v1 = {e[0]:.3f} v1',color=color,fontsize=9)
    if label=='v2':
        ax.text(.48,-.92,'v2',color=color,fontsize=9)
        ax.annotate(f'S v2 = {e[1]:.3f} v2',xy=after,xytext=(1.1,-.65),arrowprops=dict(arrowstyle='-',color=color),fontsize=9,color=color)
    if label=='u':
        ax.text(-.2,1.02,'u',color=color,fontsize=9)
        ax.text(after[0]+.12,after[1]-.04,'S u',color=color,fontsize=9)
ax.set(xlim=(-.45,3.85),ylim=(-1.3,1.95),xlabel='Direction coordinate 1',ylabel='Direction coordinate 2')
ax=axs[1]; axes2d(ax,(-1.15,1.3)); ax.set_title('B. The larger eigenvalue dominates repetition',loc='left',fontsize=11,pad=12)
ax.plot([-1.1*v1[0],1.28*v1[0]],[-1.1*v1[1],1.28*v1[1]],color=TEAL,lw=1,ls='--',label='Leading eigenvector line')
start_vector=v1+10*v2
for k in [0,1,2]:
    x=np.linalg.matrix_power(S,k)@start_vector; u=x/np.linalg.norm(x)
    ax.annotate('',xy=u,xytext=(0,0),arrowprops=dict(arrowstyle='->',color=BLUE,alpha=.4+.25*k,lw=2))
    labelpos={0:(u[0]+.05,u[1]-.04),1:(1.02,.24),2:(1.02,.49)}[k]
    ax.annotate(f'k = {k}',xy=u,xytext=labelpos,fontsize=9,color=BLUE)
ax.legend(loc='upper left',fontsize=8,frameon=False)
ax.set(xlim=(-.2,1.32),ylim=(-1.05,.85),xlabel='Normalized direction coordinate 1',ylabel='Normalized direction coordinate 2')
save(fig,'figure1_geometry')
fig,ax=plt.subplots(figsize=(9.8,5.7),layout='constrained')
ax.scatter(X[:,0],X[:,1],s=24,color=BLUE,alpha=.55,label='Observed flower')
idx=np.unique(np.r_[np.arange(0,len(X),7),np.argsort(dist)[-3:]])
for i in idx: ax.plot([X[i,0],recon[i,0]],[X[i,1],recon[i,1]],color=RED,alpha=.48,lw=.9)
ax.scatter(recon[idx,0],recon[idx,1],s=24,facecolors='none',edgecolors=TEAL,label='Reconstruction (selected flowers)')
t=np.array([-3.3,3.8]); line=mu+t[:,None]*V[:,0]
ax.plot(line[:,0],line[:,1],color=TEAL,lw=2,label='PC1 line through the sample mean')
ax.scatter(*mu,marker='X',s=100,color='#253343',label='Sample mean',zorder=4)
ax.set(xlabel='Petal length (cm)',ylabel='Petal width (cm)',xlim=(.6,7.3),ylim=(-.3,3.0))
ax.set_aspect('equal'); ax.grid(alpha=.15); ax.legend(fontsize=9,loc='upper left',frameon=False,ncol=2)
save(fig,'figure2_projection')

fig,axs=plt.subplots(1,2,figsize=(10.5,4.4),layout='constrained')
ax=axs[0]
ax.bar([0,1],e,color=[TEAL,RED],width=.55)
for j in range(2):
    ax.text(j,e[j]+.09,f'{e[j]:.3f} cm²\n{100*ratio[j]:.2f}%',ha='center',va='bottom',fontsize=10)
ax.set(xticks=[0,1],xticklabels=['PC1: keep','PC2: discard'],ylabel='Score variance = eigenvalue (cm²)',ylim=(0,4.5))
ax.set_title('A. Eigenvalues divide the total variance',loc='left',fontsize=11)
ax=axs[1]; ax.hist(dist,bins=np.arange(0,.82,.05),color=BLUE,edgecolor='#ffffff')
ax.axvline(np.sqrt(np.mean(dist**2)),color=RED,ls='--',label=f'RMS distance: {np.sqrt(np.mean(dist**2)):.3f} cm')
ax.set(xlabel='Distance from flower to its reconstruction (cm)',ylabel='Number of flowers',xlim=(0,.82))
ax.set_title('B. A high variance share still allows errors',loc='left',fontsize=12)
ax.legend(fontsize=9,frameon=False); save(fig,'figure3_tradeoff')

csvwrite(OUT/'pca_components.csv',['component','length_weight','width_weight','eigenvalue_cm2','variance_share'],([i+1,*V[:,i],e[i],ratio[i]] for i in range(2)))
csvwrite(OUT/'reconstruction.csv',['observation_id','petal_length_cm','petal_width_cm','pc1_score','reconstructed_length_cm','reconstructed_width_cm','distance_cm'],([i+1,*X[i],scores[i,0],*recon[i],dist[i]] for i in range(len(X))))
csvwrite(OUT/'direction_search.csv',['angle_degrees','projected_variance_cm2'],zip(np.degrees(theta),variance))
fit=PCA(n_components=1).fit(X)
assert np.allclose(fit.explained_variance_,e[:1])
assert np.allclose(fit.inverse_transform(fit.transform(X)),recon)
assert np.allclose(S@V,V*e)
assert np.allclose(V.T@V,np.eye(2))
assert np.isclose(np.sum(residual**2),(len(X)-1)*e[1])
assert np.isclose(variance.max(),e[0],rtol=1e-7)
assert np.allclose(Z,scores@V.T)
assert np.allclose(S@v1,e[0]*v1) and np.allclose(S@v2,e[1]*v2)
assert np.allclose(X,iris.data[:,2:4])
checks={'status':'passed','observations':len(X),'data_sha256':hashlib.sha256(rawpath.read_bytes()).hexdigest(),
 'eigen_equation':True,'orthonormal_directions':True,'sklearn_pca_agrees':True,'full_rotation_is_lossless':True,
 'reconstruction_loss_equals_discarded_variance':True,'angle_search_agrees':True,
 'retained_variance_percent':float(100*ratio[0]),'rms_reconstruction_distance_cm':float(np.sqrt(np.mean(dist**2))),
 'maximum_reconstruction_distance_cm':float(dist.max()),'geometry_uses_same_covariance':True,'eigenvalue_sum_equals_original_variance':bool(np.isclose(e.sum(),np.trace(S))),'score_variances_equal_eigenvalues':bool(np.allclose(scores.var(axis=0,ddof=1),e)),'numpy_version':np.__version__}
write_if_changed(OUT/'validation.json', json.dumps(checks,indent=2)+'\n')
mapping={'SHARE':f'{100*ratio[0]:.2f}','LOSS':f'{100*ratio[1]:.2f}',
 'W1':f'{V[0,0]:.3f}','W2':f'{V[1,0]:.3f}','M1':f'{mu[0]:.3f}','M2':f'{mu[1]:.3f}',
 'E1':f'{e[0]:.3f}','E2':f'{e[1]:.3f}','RMS':f'{np.sqrt(np.mean(dist**2)):.3f}',
 'ANGLE':f'{angle:.1f}','MAX':f'{dist.max():.3f}',
 'LENGTHSHARE':f'{100*S[0,0]/np.trace(S):.2f}'}
i=int(np.argmax(dist))
mapping.update({'WORSTID':str(i+1),'OBS1':f'{X[i,0]:.1f}','OBS2':f'{X[i,1]:.1f}',
 'RECON1':f'{recon[i,0]:.2f}','RECON2':f'{recon[i,1]:.2f}',
 'EXAMPLE_L':f'{X[0,0]:.1f}','EXAMPLE_W':f'{X[0,1]:.1f}','EXAMPLE_SCORE':f'{scores[0,0]:.2f}'})
body=(ROOT/'code/article_template_editorial.txt').read_text(encoding='utf-8')
for key,value in mapping.items(): body=body.replace('{{'+key+'}}',value)
assert not re.search(r'\{\{[A-Z0-9]+\}\}',body)
write_if_changed(OUT/'article.txt', body)
if '--html' in sys.argv:
    subprocess.run(['pandoc',str(OUT/'article.txt'),'--from=markdown+tex_math_dollars','--to=html5','--mathml',
      '--standalone','--include-before-body='+str(ROOT/'code/preview_header.html'),'--embed-resources','--resource-path='+str(ROOT),'--css='+str(ROOT/'code/style.css'),
      '--metadata','pagetitle=Two Measurements, One Score—and 99% of the Variation','--output='+str(ROOT/'index.html')],check=True)
environment = {'python': platform.python_version(), 'executable': sys.executable,
               **{name: importlib.metadata.version(name) for name in ['numpy','matplotlib','scikit-learn']}}
write_if_changed(OUT/'environment.json', json.dumps(environment,indent=2)+'\n')
print(json.dumps(checks,indent=2))
