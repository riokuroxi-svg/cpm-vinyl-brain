#!/usr/bin/env python3
"""CPM Vinyl Brain 0.3 — solucionador semántico integrado.

Construye estructura, rostro y accesorios con capas sólidas; compara varias
inicializaciones y refina conjuntamente las capas de cada región.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.metrics import structural_similarity

from solver_v02c import (
    ShapeLibrary, Layer, SOLID_SHAPES, fit_region, load_graph, mutate,
    render_recipe, render_target, transform_mask
)


FINAL_BUDGET = {
    # Perfil de prueba de alta fidelidad: 147 capas, por debajo del presupuesto 280.
    "headpiece": 10, "hair_back": 10,
    "sleeve_left_image": 3, "sleeve_right_image": 3,
    "apron": 8, "shoulder_frills": 5,
    "cuff_left_image": 3, "cuff_right_image": 3,
    "arm_right_image": 2, "neck": 3, "face": 8, "bow_dark": 6,
    "hair_front": 15, "hair_side": 20,
    "eye_white_left_image": 3, "eye_white_right_image": 3,
    "eye_dark_left_image": 6, "eye_dark_right_image": 6,
    "eye_cyan_left_image": 3, "eye_cyan_right_image": 3,
    "eye_highlight_left_image": 2, "eye_highlight_right_image": 2,
    "brow_left_image": 2, "brow_right_image": 2,
    "mouth": 3, "nose_detail": 1,
    "accessory_blue": 3, "accessory_yellow": 3,
    "accessory_pink_ribbon": 3, "headpiece_gray": 3,
}

SHAPE_POLICY = {
    "headpiece": ["08_circulo","09_gota","12_pentagono","06_arco_grueso","36_semicircle","38_rounded_rect","39_capsule"],
    "face": ["08_circulo","09_gota","12_pentagono","36_semicircle","38_rounded_rect","39_capsule"],
    "neck": ["08_circulo","13_rectangulo","12_pentagono","38_rounded_rect","39_capsule"],
    "arm_right_image": ["08_circulo","09_gota","13_rectangulo","39_capsule"],
    "hair_back": ["08_circulo","09_gota","10_bandera_ondulada","12_pentagono","35_wave_band","36_semicircle"],
    "hair_front": ["07_triangulo","09_gota","10_bandera_ondulada","11_flecha","12_pentagono","16_directional_pentagon","31_slope","35_wave_band"],
    "hair_side": ["07_triangulo","09_gota","10_bandera_ondulada","11_flecha","13_rectangulo","14_parallelogram","31_slope","39_capsule","40_line"],
    "eye_white_left_image": ["08_circulo","09_gota","06_arco_grueso","36_semicircle","37_crescent","39_capsule"],
    "eye_white_right_image": ["08_circulo","09_gota","06_arco_grueso","36_semicircle","37_crescent","39_capsule"],
    "eye_dark_left_image": ["05_arco_delgado","06_arco_grueso","08_circulo","09_gota","20_ring","25_circle_outline","33_u_shape","37_crescent","40_line"],
    "eye_dark_right_image": ["05_arco_delgado","06_arco_grueso","08_circulo","09_gota","20_ring","25_circle_outline","33_u_shape","37_crescent","40_line"],
    "eye_cyan_left_image": ["08_circulo","09_gota","36_semicircle"],
    "eye_cyan_right_image": ["08_circulo","09_gota","36_semicircle"],
    "eye_highlight_left_image": ["08_circulo","09_gota"],
    "eye_highlight_right_image": ["08_circulo","09_gota"],
    "brow_left_image": ["05_arco_delgado","13_rectangulo","09_gota","37_crescent","40_line"],
    "brow_right_image": ["05_arco_delgado","13_rectangulo","09_gota","37_crescent","40_line"],
    "mouth": ["05_arco_delgado","13_rectangulo","09_gota","33_u_shape","37_crescent","40_line"],
    "nose_detail": ["08_circulo","13_rectangulo","40_line"],
}

STRUCTURE_IDS = {
    "headpiece","hair_back","sleeve_left_image","sleeve_right_image","apron",
    "shoulder_frills","cuff_left_image","cuff_right_image","arm_right_image",
    "neck","face","bow_dark","hair_front","hair_side"
}
DETAIL_IDS = {id for id in FINAL_BUDGET if id.startswith(("eye_","brow_"))} | {"mouth","nose_detail"}


def phase(region_id: str) -> str:
    if region_id in STRUCTURE_IDS: return "structure"
    if region_id in DETAIL_IDS: return "facial_details"
    return "accessories"


def layers_union(layers: list[Layer], library: ShapeLibrary, shape):
    union=np.zeros(shape,bool)
    for layer in layers:
        union |= transform_mask(library.shapes[layer.shape_id],layer,shape)>=.48
    return union


def global_region_score(union: np.ndarray, target: np.ndarray, allowed: np.ndarray):
    area=max(1,int(target.sum()))
    inside=union & target
    hard=union & (~allowed)
    soft=union & allowed & (~target)
    coverage=inside.sum()/area
    hard_rate=hard.sum()/area
    soft_rate=soft.sum()/area
    tb=cv2.morphologyEx(target.astype(np.uint8),cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))>0
    ub=cv2.morphologyEx(union.astype(np.uint8),cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))>0
    td=cv2.dilate(tb.astype(np.uint8),np.ones((5,5),np.uint8))>0
    ud=cv2.dilate(ub.astype(np.uint8),np.ones((5,5),np.uint8))>0
    precision=(ub & td).sum()/max(1,ub.sum())
    recall=(tb & ud).sum()/max(1,tb.sum())
    boundary_f1=2*precision*recall/max(1e-9,precision+recall)
    score=coverage + .45*boundary_f1 - 5.5*hard_rate - .06*soft_rate
    return float(score),float(coverage),float(boundary_f1),float(hard_rate)


def refine_region(layers: list[Layer], target: np.ndarray, allowed: np.ndarray,
                  library: ShapeLibrary, rng, trials_per_layer: int, sweeps: int, shape_ids=None):
    if not layers: return layers
    h,w=target.shape
    rendered=[transform_mask(library.shapes[l.shape_id],l,(h,w))>=.48 for l in layers]
    union=np.logical_or.reduce(rendered)
    current_score,*_=global_region_score(union,target,allowed)
    shape_ids=list(shape_ids) if shape_ids else list(library.shapes)
    for sweep in range(sweeps):
        order=rng.permutation(len(layers))
        for index in order:
            others=np.zeros_like(target)
            for j,mask in enumerate(rendered):
                if j!=index: others |= mask
            best_layer=layers[index];best_mask=rendered[index];best_score=current_score
            for trial_index in range(trials_per_layer):
                step=max(.16,1.0-trial_index/max(1,trials_per_layer))*(.72**sweep)
                candidate=mutate(best_layer,rng,step,shape_ids,(h,w))
                mask=transform_mask(library.shapes[candidate.shape_id],candidate,(h,w))>=.48
                score,*_=global_region_score(others|mask,target,allowed)
                if score>best_score:
                    best_layer,best_mask,best_score=candidate,mask,score
            layers[index]=best_layer;rendered[index]=best_mask
            union=others|best_mask;current_score=best_score
    return layers


def fit_best(region_id,node,target,allowed,budget,library,seed,candidates,refinements,attempts):
    best=None
    for attempt in range(attempts):
        rng=np.random.default_rng(seed+attempt*104729+node['z']*37)
        policy=SHAPE_POLICY.get(region_id)
        layers,_=fit_region(region_id,target,allowed,budget,node['color_rgb'],node['z'],library,rng,
                            candidates,refinements,shape_ids_override=policy)
        layers=refine_region(layers,target,allowed,library,rng,trials_per_layer=30,sweeps=2,shape_ids=policy)
        union=layers_union(layers,library,target.shape) if layers else np.zeros_like(target)
        metrics=global_region_score(union,target,allowed)
        if best is None or metrics[0]>best[0]: best=(metrics[0],layers,metrics)
    return best[1],best[2]


def load_original(path: Path,w:int,h:int,background):
    im=Image.open(path).convert('RGBA').resize((w,h),Image.Resampling.LANCZOS)
    a=np.asarray(im)[:,:,3:4].astype(np.float32)/255
    rgb=np.asarray(im)[:,:,:3].astype(np.float32)
    bg=np.full_like(rgb,background,dtype=np.float32)
    return np.clip(rgb*a+bg*(1-a),0,255).astype(np.uint8)


def edge_f1(a: np.ndarray,b: np.ndarray):
    ga=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY);gb=cv2.cvtColor(b,cv2.COLOR_RGB2GRAY)
    ea=cv2.Canny(ga,60,140)>0;eb=cv2.Canny(gb,60,140)>0
    da=cv2.dilate(ea.astype(np.uint8),np.ones((3,3),np.uint8))>0
    db=cv2.dilate(eb.astype(np.uint8),np.ones((3,3),np.uint8))>0
    p=(eb&da).sum()/max(1,eb.sum());r=(ea&db).sum()/max(1,ea.sum())
    return float(2*p*r/max(1e-9,p+r))


def panel(items,path,subtitle):
    cellw,cellh=500,830;top=110
    out=Image.new('RGB',(cellw*len(items),top+cellh),(20,23,28));d=ImageDraw.Draw(out)
    try:
        title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',29)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
        sub=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
    except OSError:title=font=sub=ImageFont.load_default()
    d.text((24,20),'CPM VINYL BRAIN 0.3 · PRUEBA INTEGRADA',font=title,fill='white')
    d.text((24,65),subtitle,font=sub,fill=(174,184,197))
    for i,(label,image) in enumerate(items):
        im=Image.fromarray(image) if isinstance(image,np.ndarray) else Image.open(image).convert('RGB')
        im.thumbnail((450,740),Image.Resampling.LANCZOS)
        x=i*cellw+(cellw-im.width)//2;y=top+8
        out.paste(im,(x,y));d.rectangle((x,y,x+im.width-1,y+im.height-1),outline=(78,86,98),width=2)
        d.text((i*cellw+20,top+775),label,font=font,fill='white')
    out.save(path,optimize=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',required=True,type=Path)
    ap.add_argument('--shapes',required=True,type=Path)
    ap.add_argument('--input',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--max-side',type=int,default=384)
    ap.add_argument('--candidates',type=int,default=300)
    ap.add_argument('--refinements',type=int,default=100)
    ap.add_argument('--attempts',type=int,default=2)
    ap.add_argument('--seed',type=int,default=20260720)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)

    graph,nodes,w,h=load_graph(args.graph,args.max_side)
    library=ShapeLibrary(args.shapes,max_side=160)
    selected=[id for id in FINAL_BUDGET if id in nodes]
    selected.sort(key=lambda id:(nodes[id]['z'],list(FINAL_BUDGET).index(id)))
    background=nodes.get('background',{}).get('color_rgb',(24,24,26))

    # Máscaras futuras permiten que las capas posteriores recorten desbordamientos.
    future={};accum=np.zeros((h,w),bool)
    for rid in reversed(selected):
        future[rid]=accum.copy();accum|=nodes[rid]['mask_array']

    all_layers=[];reports=[]
    for index,rid in enumerate(selected):
        node=nodes[rid];target=node['mask_array'];allowed=target|future[rid]
        layers,metrics=fit_best(rid,node,target,allowed,FINAL_BUDGET[rid],library,
                                args.seed+index*7919,args.candidates,args.refinements,args.attempts)
        all_layers.extend(layers)
        score,cov,bf1,hard=metrics
        reports.append({'regionId':rid,'phase':phase(rid),'budget':FINAL_BUDGET[rid],
                        'used':len(layers),'coverage':round(cov,5),'boundaryF1':round(bf1,5),
                        'hardOverflow':round(hard,5),'score':round(score,5)})
        print(f"{phase(rid):14s} {rid:28s} {len(layers):2d}/{FINAL_BUDGET[rid]:2d} cov={cov*100:5.1f}% borde={bf1*100:5.1f}%")

    # Render de alta resolución y métricas contra el objetivo semántico.
    scale=3.0
    target_small=render_target(nodes,selected,(h,w),background)
    target=cv2.resize(target_small,(round(w*scale),round(h*scale)),interpolation=cv2.INTER_NEAREST)
    preview=render_recipe(all_layers,library,(h,w),background,scale=scale)
    original=load_original(args.input,preview.shape[1],preview.shape[0],background)
    ssim=float(structural_similarity(target,preview,channel_axis=2,data_range=255))
    ef1=edge_f1(target,preview)
    mae=float(np.abs(target.astype(np.float32)-preview.astype(np.float32)).mean())

    Image.fromarray(original).save(args.out/'original.png')
    Image.fromarray(target).save(args.out/'semantic_target.png')
    Image.fromarray(preview).save(args.out/'final_preview.png')
    panel([('ORIGINAL',original),('OBJETIVO SEMÁNTICO',target),('RECETA FINAL',preview)],
          args.out/'FINAL_COMPARISON.png',
          f"capas sólidas · opacidad 100% · SSIM {ssim:.3f} · Edge-F1 {ef1:.3f} · MAE {mae:.1f}")

    sorted_layers=[item for _,item in sorted(enumerate(all_layers),key=lambda x:(x[1].z,x[0]))]
    recipe_layers=[]
    for i,item in enumerate(sorted_layers):
        recipe_layers.append({
            'index':i,'phase':phase(item.region_id),'regionId':item.region_id,'shapeId':item.shape_id,
            'x':item.cx/w,'y':item.cy/h,'width':item.width/w,'height':item.height/h,
            'rotationDeg':item.angle,'color':'#%02X%02X%02X'%item.color,
            'opacity':1.0,'z':item.z
        })
    recipe={
        'format':'cpm-semantic-vinyl-recipe','version':'0.3.0','seed':args.seed,
        'canvas':{'width':w,'height':h,'backgroundColor':'#%02X%02X%02X'%background},
        'constraints':{'solidOnly':True,'opacity':1.0,'allowedShapes':SOLID_SHAPES},
        'layers':recipe_layers,'regionReport':reports,
        'metrics':{
            'requestedLayers':sum(FINAL_BUDGET[id] for id in selected),'generatedLayers':len(recipe_layers),
            'meanRegionCoverage':round(float(np.mean([r['coverage'] for r in reports])),5),
            'meanBoundaryF1':round(float(np.mean([r['boundaryF1'] for r in reports])),5),
            'semanticSSIM':round(ssim,5),'semanticEdgeF1':round(ef1,5),'semanticMAE':round(mae,5)
        },
        'shapeUsage':dict(Counter(layer.shape_id for layer in sorted_layers))
    }
    (args.out/'final_recipe.json').write_text(json.dumps(recipe,indent=2,ensure_ascii=False),encoding='utf-8')
    (args.out/'region_report.json').write_text(json.dumps(reports,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(recipe['metrics'],ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
