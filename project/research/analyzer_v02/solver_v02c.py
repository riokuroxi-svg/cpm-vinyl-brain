#!/usr/bin/env python3
"""Solucionador regional de vinilos 0.2C.

Ajusta exclusivamente figuras sólidas a las máscaras grandes del Nivel 0.
No usa ojos, pinceles, brillos ni opacidad variable.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


SOLID_SHAPES = [
    "05_arco_delgado", "06_arco_grueso", "07_triangulo", "08_circulo",
    "09_gota", "10_bandera_ondulada", "11_flecha", "12_pentagono", "13_rectangulo",
    "14_parallelogram", "15_diamond", "16_directional_pentagon", "17_chevron",
    "18_double_chevron", "19_sunburst", "20_ring", "21_star", "22_zigzag",
    "23_zigzag_thin", "24_square_outline", "25_circle_outline", "26_hexagon",
    "27_hexagon_outline", "28_arrow_outline", "29_triangle_outline",
    "30_concave_hourglass", "31_slope", "32_spiral", "33_u_shape", "34_heart",
    "35_wave_band", "36_semicircle", "37_crescent", "38_rounded_rect",
    "39_capsule", "40_line", "41_cross", "42_star4"
]

# 40 capas: solamente masas principales del Nivel 0.
DEFAULT_BUDGET = {
    # Las masas simples necesitan pocas capas; la silueta del cabello lateral
    # recibe el mayor presupuesto porque concentra gran parte de la identidad.
    "headpiece": 3,
    "hair_back": 3,
    "sleeve_left_image": 1,
    "sleeve_right_image": 1,
    "apron": 3,
    "shoulder_frills": 1,
    "cuff_left_image": 1,
    "cuff_right_image": 1,
    "arm_right_image": 1,
    "neck": 1,
    "face": 3,
    "bow_dark": 2,
    "hair_front": 6,
    "hair_side": 13,
}


@dataclass
class ShapeMask:
    id: str
    alpha: np.ndarray


@dataclass
class Layer:
    region_id: str
    shape_id: str
    cx: float
    cy: float
    width: float
    height: float
    angle: float
    color: tuple[int, int, int]
    z: int
    local_score: float = 0.0


class ShapeLibrary:
    def __init__(self, root: Path, max_side: int = 128):
        self.shapes: dict[str, ShapeMask] = {}
        for shape_id in SOLID_SHAPES:
            path = root / f"{shape_id}.png"
            image = np.asarray(Image.open(path).convert("RGBA"), dtype=np.uint8)
            alpha = image[:, :, 3]
            ys, xs = np.where(alpha > 2)
            if not len(xs):
                continue
            alpha = alpha[ys.min():ys.max()+1, xs.min():xs.max()+1]
            scale = min(1.0, max_side / max(alpha.shape))
            if scale < 1:
                alpha = cv2.resize(alpha, (round(alpha.shape[1]*scale), round(alpha.shape[0]*scale)), interpolation=cv2.INTER_AREA)
            self.shapes[shape_id] = ShapeMask(shape_id, alpha.astype(np.float32) / 255.0)
        missing = set(SOLID_SHAPES) - set(self.shapes)
        if missing:
            raise RuntimeError(f"Faltan figuras: {sorted(missing)}")


def load_graph(graph_path: Path, max_side: int):
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    source_w, source_h = graph["width"], graph["height"]
    scale = min(1.0, max_side / max(source_w, source_h))
    w, h = max(32, round(source_w*scale)), max(32, round(source_h*scale))
    nodes = {}
    root = graph_path.parent
    for node in graph["nodes"]:
        mask_rgba = np.asarray(Image.open(root / node["mask"]).convert("RGBA"))
        mask = mask_rgba[:, :, 3]
        if (mask.shape[1], mask.shape[0]) != (w, h):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_AREA)
        nodes[node["id"]] = {
            **node,
            "mask_array": mask >= 96,
            "color_rgb": tuple(int(node["color"][i:i+2], 16) for i in (1,3,5)),
        }
    return graph, nodes, w, h


def transform_mask(shape: ShapeMask, layer: Layer, canvas_shape: tuple[int,int], antialias=False):
    h, w = canvas_shape
    src = shape.alpha
    sh, sw = src.shape
    c = math.cos(math.radians(layer.angle)); s = math.sin(math.radians(layer.angle))
    sx = layer.width / max(1, sw); sy = layer.height / max(1, sh)
    matrix = np.array([
        [c*sx, -s*sy, layer.cx - c*sx*sw/2 + s*sy*sh/2],
        [s*sx,  c*sy, layer.cy - s*sx*sw/2 - c*sy*sh/2],
    ], dtype=np.float32)
    interpolation = cv2.INTER_LINEAR if antialias else cv2.INTER_NEAREST
    return cv2.warpAffine(src, matrix, (w,h), flags=interpolation, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def mask_boundary(mask: np.ndarray):
    k=np.ones((3,3),np.uint8)
    return cv2.morphologyEx(mask.astype(np.uint8),cv2.MORPH_GRADIENT,k)>0


def candidate_score(candidate: np.ndarray, target: np.ndarray, covered: np.ndarray, allowed: np.ndarray,
                    reward_map: np.ndarray, outside_distance: np.ndarray):
    cand = candidate >= .48
    if not cand.any():
        return -1e30
    new = cand & target & (~covered)
    if not new.any():
        return -1e30
    hard_overflow = cand & (~allowed)
    soft_overflow = cand & allowed & (~target)
    duplicate = cand & target & covered
    reward = float(reward_map[new].sum())
    hard_cost = float((1.0 + outside_distance[hard_overflow] * .16).sum())
    return reward - 4.8*hard_cost - .08*float(soft_overflow.sum()) - .10*float(duplicate.sum())


def residual_geometry(residual: np.ndarray):
    comps = cv2.connectedComponentsWithStats(residual.astype(np.uint8), 8)
    n, labels, stats, centroids = comps
    if n <= 1:
        ys,xs=np.where(residual)
        return (float(xs.mean()),float(ys.mean()),max(2,float(np.ptp(xs)+1)),max(2,float(np.ptp(ys)+1)),0.0)
    idx=1+np.argmax(stats[1:,cv2.CC_STAT_AREA])
    component=labels==idx
    ys,xs=np.where(component)
    coords=np.c_[xs,ys].astype(np.float32)
    center=coords.mean(0)
    angle=0.0
    if len(coords)>=3:
        cov=np.cov(coords-center,rowvar=False)
        values,vectors=np.linalg.eigh(cov)
        major=vectors[:,np.argmax(values)]
        angle=math.degrees(math.atan2(major[1],major[0]))
    return (float(center[0]),float(center[1]),float(xs.max()-xs.min()+1),float(ys.max()-ys.min()+1),angle)


def random_candidate(rng, region_id, shape_id, geometry, bbox_region, color, z):
    cx0,cy0,cw,ch,base_angle=geometry
    x0,y0,x1,y1=bbox_region
    bw=max(3,x1-x0); bh=max(3,y1-y0)
    if rng.random()<.58:
        width=cw*rng.uniform(.45,1.25)
        height=ch*rng.uniform(.45,1.25)
        cx=cx0+rng.normal(0,max(1,cw*.16)); cy=cy0+rng.normal(0,max(1,ch*.16))
        angle=base_angle+rng.normal(0,35)
    else:
        width=bw*math.exp(rng.uniform(math.log(.08),math.log(.75)))
        height=bh*math.exp(rng.uniform(math.log(.08),math.log(.75)))
        cx=rng.uniform(x0,x1); cy=rng.uniform(y0,y1)
        angle=rng.uniform(0,360)
    return Layer(region_id,shape_id,float(cx),float(cy),max(2,float(width)),max(2,float(height)),float(angle%360),color,z)


def mutate(layer: Layer, rng, step: float, shape_ids: list[str], canvas_shape):
    h,w=canvas_shape
    choice=rng.integers(0,7)
    result=replace(layer)
    if choice==0: result.cx += rng.normal(0,w*.025*step)
    elif choice==1: result.cy += rng.normal(0,h*.025*step)
    elif choice==2: result.width *= math.exp(rng.normal(0,.14*step))
    elif choice==3: result.height *= math.exp(rng.normal(0,.14*step))
    elif choice==4: result.angle=(result.angle+rng.normal(0,18*step))%360
    elif choice==5:
        result.cx += rng.normal(0,w*.012*step); result.cy += rng.normal(0,h*.012*step)
        result.angle=(result.angle+rng.normal(0,8*step))%360
    else: result.shape_id=shape_ids[rng.integers(0,len(shape_ids))]
    result.cx=float(np.clip(result.cx,-w*.15,w*1.15)); result.cy=float(np.clip(result.cy,-h*.15,h*1.15))
    result.width=float(np.clip(result.width,2,w*1.4)); result.height=float(np.clip(result.height,2,h*1.4))
    return result


def fit_region(region_id: str, target: np.ndarray, allowed: np.ndarray, budget: int, color, z: int,
               library: ShapeLibrary, rng, candidates: int, refinements: int, shape_ids_override=None):
    h,w=target.shape
    boundary=mask_boundary(target)
    reward_map=np.ones((h,w),np.float32); reward_map[boundary]=2.4
    outside_distance=cv2.distanceTransform((~target).astype(np.uint8),cv2.DIST_L2,3)
    ys,xs=np.where(target)
    if not len(xs): return [],0.0
    region_bbox=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
    covered=np.zeros_like(target)
    layers=[]
    shape_ids=list(shape_ids_override) if shape_ids_override else list(library.shapes)
    shape_ids=[shape_id for shape_id in shape_ids if shape_id in library.shapes]
    if not shape_ids:
        shape_ids=list(library.shapes)

    for _ in range(budget):
        residual=target & (~covered)
        if residual.sum()<max(3,target.sum()*.006): break
        geometry=residual_geometry(residual)
        best=None; best_score=-1e30; best_mask=None
        for _ in range(candidates):
            shape_id=shape_ids[rng.integers(0,len(shape_ids))]
            layer=random_candidate(rng,region_id,shape_id,geometry,region_bbox,color,z)
            rendered=transform_mask(library.shapes[layer.shape_id],layer,(h,w))
            score=candidate_score(rendered,target,covered,allowed,reward_map,outside_distance)
            if score>best_score:
                best,best_score,best_mask=layer,score,rendered
        if best is None or best_score<=0: break

        current=best; current_score=best_score; current_mask=best_mask
        for iteration in range(refinements):
            step=max(.18,1.0-iteration/max(1,refinements))
            trial=mutate(current,rng,step,shape_ids,(h,w))
            rendered=transform_mask(library.shapes[trial.shape_id],trial,(h,w))
            score=candidate_score(rendered,target,covered,allowed,reward_map,outside_distance)
            if score>current_score:
                current,current_score,current_mask=trial,score,rendered
        current.local_score=current_score
        layers.append(current)
        covered |= current_mask>=.48

    coverage=float((covered & target).sum()/max(1,target.sum()))
    return layers,coverage


def render_recipe(layers: list[Layer], library: ShapeLibrary, canvas_shape, background, scale=1.0):
    h,w=canvas_shape
    oh,ow=round(h*scale),round(w*scale)
    canvas=np.empty((oh,ow,3),np.float32); canvas[:]=background
    for layer in sorted(enumerate(layers),key=lambda x:(x[1].z,x[0])):
        _,item=layer
        scaled=replace(item,cx=item.cx*scale,cy=item.cy*scale,width=item.width*scale,height=item.height*scale)
        alpha=transform_mask(library.shapes[item.shape_id],scaled,(oh,ow),antialias=True)[...,None]
        color=np.array(item.color,np.float32)
        canvas=color*alpha+canvas*(1-alpha)
    return np.clip(canvas,0,255).astype(np.uint8)


def render_target(nodes, selected_ids, shape, background):
    h,w=shape; canvas=np.empty((h,w,3),np.uint8);canvas[:]=background
    for node in sorted((nodes[i] for i in selected_ids if i in nodes),key=lambda n:n['z']):
        canvas[node['mask_array']]=node['color_rgb']
    return canvas


def comparison(target,preview,path):
    h,w=target.shape[:2]; gap=12
    out=Image.new('RGB',(w*2+gap,h+70),(20,23,28));d=ImageDraw.Draw(out)
    out.paste(Image.fromarray(target),(0,70));out.paste(Image.fromarray(preview),(w+gap,70))
    try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',22)
    except OSError: font=ImageFont.load_default()
    d.text((16,20),'OBJETIVO NIVEL 0',font=font,fill='white');d.text((w+gap+16,20),'40 VINILOS SÓLIDOS',font=font,fill='white')
    out.save(path,optimize=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',required=True,type=Path)
    ap.add_argument('--shapes',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--max-side',type=int,default=320)
    ap.add_argument('--candidates',type=int,default=260)
    ap.add_argument('--refinements',type=int,default=90)
    ap.add_argument('--seed',type=int,default=20260720)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)

    graph,nodes,w,h=load_graph(args.graph,args.max_side)
    library=ShapeLibrary(args.shapes)
    rng=np.random.default_rng(args.seed)
    selected=[id for id in DEFAULT_BUDGET if id in nodes]
    selected.sort(key=lambda id:nodes[id]['z'])
    background=nodes.get('background',{}).get('color_rgb',(24,24,26))

    # Una capa posterior puede invadir únicamente zonas que serán cubiertas por regiones posteriores.
    future={}
    accumulated=np.zeros((h,w),bool)
    for region_id in reversed(selected):
        future[region_id]=accumulated.copy()
        accumulated |= nodes[region_id]['mask_array']

    all_layers=[]; report=[]
    for region_id in selected:
        node=nodes[region_id]; target=node['mask_array']
        allowed=target | future[region_id]
        layers,cov=fit_region(region_id,target,allowed,DEFAULT_BUDGET[region_id],node['color_rgb'],node['z'],
                              library,rng,args.candidates,args.refinements)
        all_layers.extend(layers)
        report.append({'regionId':region_id,'budget':DEFAULT_BUDGET[region_id],'used':len(layers),'coverage':round(cov,5)})
        print(f"{region_id:24s} {len(layers):2d}/{DEFAULT_BUDGET[region_id]:2d} cobertura={cov*100:5.1f}%")

    target_small=render_target(nodes,selected,(h,w),background)
    preview_scale=3.0
    target=cv2.resize(target_small,(round(w*preview_scale),round(h*preview_scale)),interpolation=cv2.INTER_NEAREST)
    preview=render_recipe(all_layers,library,(h,w),background,scale=preview_scale)
    Image.fromarray(target).save(args.out/'target_level0.png')
    Image.fromarray(preview).save(args.out/'preview_40_layers.png')
    comparison(target,preview,args.out/'comparison_level0.png')

    recipe_layers=[]
    for index,layer in enumerate(sorted(enumerate(all_layers),key=lambda x:(x[1].z,x[0]))):
        _,item=layer
        recipe_layers.append({
            'index':index,'regionId':item.region_id,'shapeId':item.shape_id,
            'x':item.cx/w,'y':item.cy/h,'width':item.width/w,'height':item.height/h,
            'rotationDeg':item.angle,'color':'#%02X%02X%02X'%item.color,
            'opacity':1.0,'z':item.z,'localScore':item.local_score
        })
    recipe={
        'format':'cpm-region-vinyl-recipe','version':'0.2C','seed':args.seed,
        'canvas':{'width':w,'height':h,'backgroundColor':'#%02X%02X%02X'%background},
        'constraints':{'solidOnly':True,'opacity':1.0,'allowedShapes':SOLID_SHAPES},
        'layers':recipe_layers,'regionReport':report,
        'metrics':{'requestedLayers':sum(DEFAULT_BUDGET.get(i,0) for i in selected),'generatedLayers':len(recipe_layers),
                   'meanRegionCoverage':round(float(np.mean([r['coverage'] for r in report])),5)}
    }
    (args.out/'recipe_level0.json').write_text(json.dumps(recipe,indent=2,ensure_ascii=False),encoding='utf-8')
    (args.out/'coverage_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f"Capas generadas: {len(recipe_layers)} | cobertura regional media: {recipe['metrics']['meanRegionCoverage']*100:.1f}%")


if __name__=='__main__':
    main()
