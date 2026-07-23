#!/usr/bin/env python3
"""CPM Vinyl Brain 0.5 — overcomplete ADD/CUT + Optimize & Reduce.

Toma una receta semántica 0.3 como inicialización, crea un pool virtual sin
presupuesto estricto mediante correcciones opacas y compila recetas progresivas.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.metrics import structural_similarity

from solver_v02c import ShapeLibrary, Layer, SOLID_SHAPES, load_graph, mutate, random_candidate, residual_geometry, transform_mask
from solver_final import SHAPE_POLICY, edge_f1


@dataclass
class Record:
    uid: int
    layer: Layer
    phase: str
    operation: str
    source: str


def rgb(hex_color: str):
    return tuple(int(hex_color[i:i+2],16) for i in (1,3,5))


def load_base_recipe(path: Path,w:int,h:int):
    data=json.loads(path.read_text(encoding='utf-8'))
    result=[]
    for i,item in enumerate(data['layers']):
        result.append(Record(
            i,
            Layer(item['regionId'],item['shapeId'],item['x']*w,item['y']*h,
                  item['width']*w,item['height']*h,item['rotationDeg'],rgb(item['color']),item.get('z',i)),
            item.get('phase','structure'),'ADD','semantic_base'
        ))
    return data,result


def render_records(records,library,shape,background,with_owner=False):
    h,w=shape
    image=np.empty((h,w,3),np.uint8);image[:]=background
    owner=np.full((h,w),-1,np.int32)
    for rec in records:
        mask=transform_mask(library.shapes[rec.layer.shape_id],rec.layer,shape)>=.48
        image[mask]=rec.layer.color
        owner[mask]=rec.uid
    return (image,owner) if with_owner else image


def semantic_weight(label_map: np.ndarray):
    weight=np.ones(label_map.shape,np.float32)
    for key,factor in [
        ('eye_',4.0),('brow_',3.5),('mouth',4.0),('nose',2.5),
        ('face',2.0),('hair_front',2.2),('hair_side',1.6),('hair_back',1.4),
        ('headpiece',1.25),('bow',1.4),('accessory',1.5)
    ]:
        weight[np.char.startswith(label_map.astype(str),key)]=factor
    return weight


def build_label_map(graph,nodes,shape):
    h,w=shape
    labels=np.full((h,w),'background',dtype='<U40')
    ordered=[id for id in graph.get('renderOrder',[]) if id in nodes]
    for id in ordered:
        labels[nodes[id]['mask_array']]=id
    return labels


def error_map(image,target,weight):
    return np.abs(image.astype(np.int16)-target.astype(np.int16)).sum(2).astype(np.float32)*weight


def choose_error_component(error,target,label_map,rng):
    flat=error.ravel(); positive=np.flatnonzero(flat>8)
    if not len(positive): return None
    # Muestrear entre el 12% de píxeles con mayor error evita obsesionarse con un único borde.
    values=flat[positive]; threshold=np.quantile(values,.88)
    top=positive[values>=threshold]
    index=int(top[rng.integers(0,len(top))]); y,x=divmod(index,error.shape[1])
    color=target[y,x].copy(); region=str(label_map[y,x])
    same=np.all(target==color,axis=2) & (error>8)
    n,cc,stats,_=cv2.connectedComponentsWithStats(same.astype(np.uint8),8)
    cid=int(cc[y,x])
    if cid==0:
        component=np.zeros_like(same);component[y,x]=True
    else:
        component=cc==cid
    ys,xs=np.where(component)
    if not len(xs): return None
    box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
    return component,tuple(map(int,color)),region,box


def candidate_improvement(mask,current,target,color,weight):
    chosen=mask>=.48
    if not chosen.any(): return -1e30
    old=np.abs(current[chosen].astype(np.int16)-target[chosen].astype(np.int16)).sum(1)
    c=np.array(color,np.int16)
    new=np.abs(c-target[chosen].astype(np.int16)).sum(1)
    return float(((old-new)*weight[chosen]).sum())


def correction_candidate(component,color,region,current,target,weight,library,rng,candidates,refinements,uid):
    h,w=component.shape
    geometry=residual_geometry(component)
    ys,xs=np.where(component);box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
    policies=SHAPE_POLICY.get(region,list(library.shapes))
    policies=[id for id in policies if id in library.shapes] or list(library.shapes)
    best=None;best_score=-1e30;best_mask=None
    for _ in range(candidates):
        sid=policies[rng.integers(0,len(policies))]
        layer=random_candidate(rng,region,sid,geometry,box,color,1000+uid)
        # En corrección se favorecen piezas algo menores para evitar borrar detalles vecinos.
        if rng.random()<.65:
            layer.width*=rng.uniform(.35,.85);layer.height*=rng.uniform(.35,.85)
        mask=transform_mask(library.shapes[sid],layer,(h,w))
        score=candidate_improvement(mask,current,target,color,weight)
        if score>best_score:best,best_score,best_mask=layer,score,mask
    if best is None:return None
    for i in range(refinements):
        step=max(.15,1-i/max(1,refinements))
        trial=mutate(best,rng,step,policies,(h,w));trial.color=color;trial.region_id=region
        mask=transform_mask(library.shapes[trial.shape_id],trial,(h,w))
        score=candidate_improvement(mask,current,target,color,weight)
        if score>best_score:best,best_score,best_mask=trial,score,mask
    return best,best_score,best_mask


def classify_operation(region,current,target,mask,color):
    chosen=mask>=.48
    if not chosen.any():return 'ADD'
    old=np.median(current[chosen],axis=0)
    group_cut=region in {'background','face','neck','apron','cuff_left_image','cuff_right_image'}
    changed=np.linalg.norm(old-np.array(color))>20
    return 'CUT' if group_cut and changed else 'ADD'


def expand_pool(records,library,target,label_map,background,virtual_layers,seed,candidates,refinements):
    rng=np.random.default_rng(seed)
    current,_=render_records(records,library,target.shape[:2],background,True)
    weight=semantic_weight(label_map)
    next_uid=max((r.uid for r in records),default=-1)+1
    stalled=0
    while len(records)<virtual_layers and stalled<40:
        err=error_map(current,target,weight)
        chosen=choose_error_component(err,target,label_map,rng)
        if chosen is None:break
        component,color,region,_=chosen
        result=correction_candidate(component,color,region,current,target,weight,library,rng,candidates,refinements,next_uid)
        if result is None:
            stalled+=1;continue
        layer,score,mask=result
        # Costo mínimo para no llenar el pool con ruido de uno o dos píxeles.
        if score<max(20.0,float(weight[component].mean()*18)):
            stalled+=1;continue
        operation=classify_operation(region,current,target,mask,color)
        records.append(Record(next_uid,layer,'gap_correction',operation,'virtual_overcomplete'))
        current[mask>=.48]=color
        next_uid+=1;stalled=0
        if len(records)%50==0:
            print(f"pool={len(records)} MAE={np.abs(current.astype(np.int16)-target.astype(np.int16)).mean():.2f}")
    return records,current


def cache_masks(records,library,shape):
    return {r.uid:(transform_mask(library.shapes[r.layer.shape_id],r.layer,shape)>=.48) for r in records}


def stack_state(active,records_by_uid,masks,target,background,weight):
    h,w=target.shape[:2]
    image=np.empty((h,w,3),np.uint8);image[:]=background
    owner=np.full((h,w),-1,np.int32);second=np.full((h,w),-1,np.int32)
    for uid in active:
        rec=records_by_uid[uid];mask=masks[uid]
        second[mask]=owner[mask];owner[mask]=uid;image[mask]=rec.layer.color
    err=error_map(image,target,weight)
    return image,owner,second,err


def importance(active,records_by_uid,masks,target,background,weight):
    image,owner,second,current_error=stack_state(active,records_by_uid,masks,target,background,weight)
    scores={uid:0.0 for uid in active}
    # Construir el color inmediatamente inferior de cada píxel superior.
    for uid in active:
        pixels=owner==uid
        if not pixels.any():
            scores[uid]=-1e12;continue
        sec=second[pixels]
        below=np.empty((pixels.sum(),3),np.uint8);below[:]=background
        for sid in np.unique(sec):
            if sid>=0: below[sec==sid]=records_by_uid[int(sid)].layer.color
        target_px=target[pixels].astype(np.int16)
        below_err=np.abs(below.astype(np.int16)-target_px).sum(1)*weight[pixels]
        delta=float((below_err-current_error[pixels]).sum())
        rec=records_by_uid[uid]
        # Pequeño bono estructural; no puede salvar una capa totalmente inútil.
        bonus=0.015*pixels.sum()*weight[pixels].mean() if rec.source=='semantic_base' else 0.0
        scores[uid]=delta+bonus
    return scores,image


def reduce_to(active,records_by_uid,masks,target,background,weight,target_count):
    active=list(active)
    while len(active)>target_count:
        scores,_=importance(active,records_by_uid,masks,target,background,weight)
        counts=Counter(records_by_uid[uid].layer.region_id for uid in active)
        removable=[]
        for uid in active:
            rec=records_by_uid[uid]
            minimum=1 if target_count>=64 and rec.layer.region_id not in {'nose_detail'} else 0
            if counts[rec.layer.region_id]>minimum:removable.append(uid)
        if not removable:removable=active.copy()
        batch=max(1,min(len(active)-target_count,max(1,len(active)//40)))
        doomed=sorted(removable,key=lambda uid:scores[uid])[:batch]
        doomed_set=set(doomed);active=[uid for uid in active if uid not in doomed_set]
    return active


def metrics(image,target):
    ssim=float(structural_similarity(target,image,channel_axis=2,data_range=255))
    ef1=edge_f1(target,image)
    mae=float(np.abs(image.astype(np.float32)-target.astype(np.float32)).mean())
    exact=float(np.mean(np.all(image==target,axis=2)))
    score=.45*ssim+.25*ef1+.20*(1-mae/255)+.10*exact
    return {'ssim':ssim,'edgeF1':ef1,'mae':mae,'exactPixelFraction':exact,'qualityScore':score}


def serialize(active,records_by_uid,w,h,background,metrics_data,version='0.5.0'):
    layers=[]
    for i,uid in enumerate(active):
        rec=records_by_uid[uid];l=rec.layer
        layers.append({'index':i,'uid':uid,'phase':rec.phase,'operation':rec.operation,'source':rec.source,
                       'regionId':l.region_id,'shapeId':l.shape_id,'x':l.cx/w,'y':l.cy/h,
                       'width':l.width/w,'height':l.height/h,'rotationDeg':l.angle,
                       'color':'#%02X%02X%02X'%l.color,'opacity':1.0,'z':i})
    return {'format':'cpm-optimize-reduce-recipe','version':version,
            'canvas':{'width':w,'height':h,'backgroundColor':'#%02X%02X%02X'%background},
            'constraints':{'solidOnly':True,'opacity':1.0,'gameLimit':450,'reservedCalibrationLayers':20},
            'layers':layers,'metrics':metrics_data,
            'operationUsage':dict(Counter(x['operation'] for x in layers)),
            'shapeUsage':dict(Counter(x['shapeId'] for x in layers))}


def panel(images,labels,path,subtitle):
    n=len(images);cellw,cellh=430,740;top=108
    out=Image.new('RGB',(n*cellw,top+cellh),(20,23,28));d=ImageDraw.Draw(out)
    try:
        title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',28)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',17)
        sub=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    except OSError:title=font=sub=ImageFont.load_default()
    d.text((22,18),'CPM VINYL BRAIN 0.5 · OPTIMIZE & REDUCE',font=title,fill='white')
    d.text((22,60),subtitle,font=sub,fill=(175,185,198))
    for i,(im,label) in enumerate(zip(images,labels)):
        pil=Image.fromarray(im);pil.thumbnail((390,650),Image.Resampling.LANCZOS)
        x=i*cellw+(cellw-pil.width)//2;y=top+8;out.paste(pil,(x,y))
        d.rectangle((x,y,x+pil.width-1,y+pil.height-1),outline=(80,88,100),width=2)
        d.text((i*cellw+14,top+675),label,font=font,fill='white')
    out.save(path,optimize=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base-recipe',required=True,type=Path)
    ap.add_argument('--semantic-target',required=True,type=Path)
    ap.add_argument('--graph',required=True,type=Path)
    ap.add_argument('--shapes',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--work-side',type=int,default=256)
    ap.add_argument('--virtual-layers',type=int,default=500)
    ap.add_argument('--candidates',type=int,default=70)
    ap.add_argument('--refinements',type=int,default=18)
    ap.add_argument('--seed',type=int,default=20260721)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)

    base_data=json.loads(args.base_recipe.read_text(encoding='utf-8'))
    aspect=base_data['canvas']['width']/base_data['canvas']['height']
    h=args.work_side;w=max(32,round(h*aspect));background=rgb(base_data['canvas']['backgroundColor'])
    library=ShapeLibrary(args.shapes,max_side=128)
    _,records=load_base_recipe(args.base_recipe,w,h)
    graph,nodes,gw,gh=load_graph(args.graph,args.work_side)
    # Asegurar la misma geometría que la receta.
    if (gw,gh)!=(w,h):
        for node in nodes.values():node['mask_array']=cv2.resize(node['mask_array'].astype(np.uint8),(w,h),interpolation=cv2.INTER_NEAREST)>0
    label_map=build_label_map(graph,nodes,(h,w));weight=semantic_weight(label_map)
    target=np.asarray(Image.open(args.semantic_target).convert('RGB').resize((w,h),Image.Resampling.NEAREST))

    base_image=render_records(records,library,(h,w),background)
    base_metrics=metrics(base_image,target)
    print('Base 0.3:',base_metrics)
    records,pool_image=expand_pool(records,library,target,label_map,background,args.virtual_layers,args.seed,args.candidates,args.refinements)
    print(f"Pool virtual final: {len(records)}")

    by_uid={r.uid:r for r in records};masks=cache_masks(records,library,(h,w));all_active=[r.uid for r in records]
    pool_metrics=metrics(pool_image,target)
    outputs={}
    # Reducir secuencialmente, guardando primero la máxima fidelidad.
    active=all_active
    for budget in [430,256,128,64]:
        target_count=min(budget,len(active));active=reduce_to(active,by_uid,masks,target,background,weight,target_count)
        image,_,_,_=stack_state(active,by_uid,masks,target,background,weight)
        data=metrics(image,target);data['layers']=len(active)
        recipe=serialize(active,by_uid,w,h,background,data)
        name=f"recipe_{budget:03d}.json";(args.out/name).write_text(json.dumps(recipe,indent=2,ensure_ascii=False),encoding='utf-8')
        Image.fromarray(image).save(args.out/f"preview_{budget:03d}.png")
        outputs[budget]=(list(active),image,data)
        print(budget,data)

    # Comparación justa: 0.3 (127) frente a 0.5 reducido a 128.
    winner='0.5' if outputs[128][2]['qualityScore']>base_metrics['qualityScore'] else '0.3'
    comparison={'base03':base_metrics,'poolVirtual':pool_metrics,
                'progressive':{str(k):v[2] for k,v in outputs.items()},
                'winnerSameBudget':winner,
                'notes':['comparison 0.3 uses 127 layers; 0.5 uses 128','qualityScore combines SSIM, edges, MAE and exact pixels']}
    (args.out/'comparison_metrics.json').write_text(json.dumps(comparison,indent=2,ensure_ascii=False),encoding='utf-8')
    panel([target,base_image,outputs[128][1],outputs[430][1]],
          ['OBJETIVO','BRAIN 0.3 · 127','BRAIN 0.5 · 128','BRAIN 0.5 · 430'],
          args.out/'FINAL_COMPARISON_03_VS_05.png',
          f"ganador mismo presupuesto: {winner} · pool virtual {len(records)} capas")
    print('GANADOR MISMO PRESUPUESTO:',winner)


if __name__=='__main__':
    main()
