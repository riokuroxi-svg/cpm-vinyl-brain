#!/usr/bin/env python3
"""Analizador 0.2B: subdivisión semántica y grafo de profundidad.

Usa las regiones de 0.2A y las divide en piezas que el futuro solucionador de
vinilos podrá tratar por separado. Las etiquetas izquierda/derecha se refieren
a la imagen, no a la anatomía del personaje.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from analyzer import (
    analyze_semantics, bbox, composite, load_rgba, median_color, save_mask
)


@dataclass
class Part:
    id: str
    label: str
    group: str
    mask: np.ndarray
    color: tuple[int, int, int]
    z: int
    confidence: float
    parent: str | None = None


def components(mask: np.ndarray, min_area: int = 1):
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    result = []
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            result.append((i, labels == i, stats[i], centroids[i]))
    return sorted(result, key=lambda item: item[2][cv2.CC_STAT_AREA], reverse=True)


def largest_component(mask: np.ndarray) -> np.ndarray:
    items = components(mask)
    return items[0][1] if items else np.zeros_like(mask)


def dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius*2+1, radius*2+1))
    return cv2.dilate(mask.astype(np.uint8), k) > 0


def part_color(image: np.ndarray, mask: np.ndarray, fallback):
    return median_color(image, mask, fallback)


def pick_eye_components(white: np.ndarray, face_box: list[int], min_area: int):
    x0, y0, x1, y1 = face_box
    candidates = []
    for _, mask, stats, center in components(white, min_area):
        cx, cy = center
        if x0 - 15 <= cx <= x1 + 15 and y0 <= cy <= y0 + (y1-y0)*.62:
            candidates.append((mask, stats, center))
    candidates.sort(key=lambda item: item[2][0])
    return candidates[:2]


def select_component_near(mask: np.ndarray, target: tuple[float, float], min_area=2, max_area=1000):
    best = None
    tx, ty = target
    for _, component, stats, center in components(mask, min_area):
        area = stats[cv2.CC_STAT_AREA]
        if area > max_area:
            continue
        distance = (center[0]-tx)**2 + (center[1]-ty)**2
        score = distance + area * .03
        if best is None or score < best[0]:
            best = (score, component)
    return best[1] if best else np.zeros_like(mask)


def apply_corrections(parts: list[Part], file: Path | None):
    if not file or not file.exists():
        return
    data = json.loads(file.read_text(encoding="utf-8"))
    by_id = {part.id: part for part in parts}
    h, w = parts[0].mask.shape
    for op in data.get("operations", []):
        part = by_id.get(op.get("region"))
        if part is None:
            continue
        action = op.get("action", "add")
        radius = op.get("radius", .02)
        radius_px = max(1, round(radius * max(w, h))) if radius <= 1 else round(radius)
        brush = np.zeros((h, w), np.uint8)
        for point in op.get("points", []):
            px = round(point[0] * w) if 0 <= point[0] <= 1 else round(point[0])
            py = round(point[1] * h) if 0 <= point[1] <= 1 else round(point[1])
            cv2.circle(brush, (px, py), radius_px, 255, -1)
        if action == "remove":
            part.mask &= brush == 0
        else:
            part.mask |= brush > 0


def build_parts(rgb: np.ndarray, alpha: np.ndarray) -> tuple[list[Part], np.ndarray]:
    regions, visible = analyze_semantics(rgb, alpha)
    by_id = {region.id: region for region in regions}
    hair = by_id["hair"].mask
    white = by_id["white_structure"].mask
    skin = by_id["skin"].mask
    clothes = by_id["clothes"].mask
    gray = by_id["gray_structure"].mask
    foreground = alpha > 20
    h, w = alpha.shape
    yy, xx = np.indices((h, w))
    hsv = cv2.cvtColor(visible, cv2.COLOR_RGB2HSV)
    hue, sat, val = cv2.split(hsv)

    parts: list[Part] = []
    def add(id, label, group, mask, color, z, confidence, parent=None):
        if mask.any():
            parts.append(Part(id, label, group, mask.copy(), part_color(visible, mask, color), z, confidence, parent))

    # Fondo.
    add("background", "Fondo", "background", by_id["background"].mask, (24,24,26), 0, 1.0)

    # Cabello: separar accesorio rosa desconectado, flequillo, laterales y fondo.
    hair_cc = components(hair, max(15, int(h*w*.0001)))
    hair_main = hair_cc[0][1] if hair_cc else hair
    pink_ribbon = np.zeros_like(hair)
    for _, component, _, _ in hair_cc[1:]:
        pink_ribbon |= component

    face_component = largest_component(skin)
    face_box = bbox(face_component)
    x0, y0, x1, y1 = face_box
    front_bangs = hair_main & face_component
    side_hair = hair_main & (~front_bangs) & (yy > y0 + (y1-y0)*.18)
    back_hair = hair_main & (~front_bangs) & (~side_hair)

    add("headpiece", "Cofia", "accessory", np.zeros_like(hair), (248,248,247), 10, .90)
    add("hair_back", "Cabello posterior", "hair", back_hair, (231,143,176), 20, .72, "hair")

    # Ropa oscura por componentes: manga izquierda, centro/moño, manga derecha.
    clothes_cc = components(clothes, max(50, int(h*w*.0005)))
    left_sleeve = center_dark = right_sleeve = np.zeros_like(clothes)
    if clothes_cc:
        ordered = sorted(clothes_cc[:4], key=lambda item: item[3][0])
        left_sleeve = ordered[0][1]
        right_sleeve = ordered[-1][1] if len(ordered) > 1 else np.zeros_like(clothes)
        middle = ordered[1:-1]
        for _, component, _, _ in middle:
            center_dark |= component
    add("sleeve_left_image", "Manga izquierda en imagen", "clothes", left_sleeve, (55,56,58), 30, .86, "clothes")
    add("sleeve_right_image", "Manga derecha en imagen", "clothes", right_sleeve, (55,56,58), 30, .86, "clothes")
    add("bow_dark", "Moño/ropa central oscura", "clothes", center_dark, (45,46,47), 46, .72, "clothes")

    # Blancos: cofia superior, ojos y estructura corporal.
    white_cc = components(white, max(20, int(h*w*.00005)))
    headpiece = np.zeros_like(white)
    for _, component, stats, center in white_cc:
        if center[1] < h*.34 and stats[cv2.CC_STAT_AREA] > h*w*.01:
            headpiece |= component
    # Sustituir la parte placeholder de la cofia.
    parts = [p for p in parts if p.id != "headpiece"]
    add("headpiece", "Cofia", "accessory", headpiece, (248,248,247), 10, .91)

    eye_candidates = pick_eye_components(white, face_box, max(20, int(h*w*.00025)))
    eye_union = np.zeros_like(white)
    eye_specs = []
    for index, (eye_white, stats, center) in enumerate(eye_candidates):
        side = "left_image" if index == 0 else "right_image"
        eye_union |= eye_white
        roi = dilate(eye_white, max(6, round(w*.018)))
        # Extender hacia arriba para capturar pestaña.
        ex0, ey0, ew, eh = stats[:4]
        roi[max(0,ey0-round(eh*.45)):ey0+eh, max(0,ex0-round(ew*.18)):min(w,ex0+ew+round(ew*.18))] = True
        dark = roi & foreground & (val < 125) & (~hair)
        cyan = roi & foreground & (hue >= 78) & (hue <= 108) & (sat >= 38) & (val > 105)
        highlight = eye_white & (val > 215)
        eye_specs.append((side, eye_white, dark, cyan, highlight, stats, center))

    body_white = white & (~headpiece) & (~eye_union)
    cuff_left = body_white & (yy > h*.77) & (xx < w*.58)
    cuff_right = body_white & (yy > h*.75) & (xx > w*.72)
    shoulder_frills = body_white & (yy < h*.69) & ((xx < x0 + (x1-x0)*.15) | (xx > x1 - (x1-x0)*.05))
    apron = body_white & (~cuff_left) & (~cuff_right) & (~shoulder_frills)
    add("apron", "Delantal/blanco central", "clothes", apron, (247,247,246), 35, .79, "white_structure")
    add("shoulder_frills", "Volantes de hombro", "clothes", shoulder_frills, (248,248,247), 36, .62, "white_structure")
    add("cuff_left_image", "Puño izquierdo en imagen", "clothes", cuff_left, (248,248,247), 40, .82, "white_structure")
    add("cuff_right_image", "Puño derecho en imagen", "clothes", cuff_right, (248,248,247), 40, .82, "white_structure")

    # Piel: rostro, cuello y brazos visibles.
    face_neck = face_component
    neck_start = y0 + round((y1-y0)*.86)
    neck = face_neck & (yy >= neck_start)
    face = face_neck & (~neck)
    remaining_skin = skin & (~face_neck)
    arm_cc = components(remaining_skin, max(10, int(h*w*.00005)))
    add("neck", "Cuello", "skin", neck, (232,194,176), 42, .66, "skin")
    add("face", "Rostro", "skin", face, (244,235,224), 44, .90, "skin")
    for idx, (_, component, _, center) in enumerate(sorted(arm_cc, key=lambda item:item[3][0])):
        side = "left_image" if center[0] < w/2 else "right_image"
        add(f"arm_{side}", f"Brazo/piel {side}", "skin", component, (235,205,190), 41, .55, "skin")

    # Ojos por subcapas.
    facial_union = np.zeros_like(face)
    for side, eye_white, dark, cyan, highlight, stats, center in eye_specs:
        add(f"eye_white_{side}", f"Blanco ojo {side}", "face_detail", eye_white, (250,250,248), 50, .92, "eyes")
        add(f"eye_dark_{side}", f"Pestaña/iris oscuro {side}", "face_detail", dark, (28,31,41), 51, .78, "eyes")
        add(f"eye_cyan_{side}", f"Iris celeste {side}", "face_detail", cyan, (90,190,210), 52, .82, "eyes")
        add(f"eye_highlight_{side}", f"Reflejo ojo {side}", "face_detail", highlight, (250,250,248), 53, .70, "eyes")
        facial_union |= eye_white | dark | cyan | highlight

        # Ceja: franja oscura por encima del ojo.
        ex, ey, ew, eh = stats[:4]
        brow_box = np.zeros_like(face)
        bx0=max(0,ex-round(ew*.35)); bx1=min(w,ex+ew+round(ew*.35))
        by0=max(0,ey-round(eh*.75)); by1=min(h,ey+round(eh*.08))
        brow_box[by0:by1,bx0:bx1]=True
        brow = brow_box & foreground & (val < 145) & (~hair)
        add(f"brow_{side}", f"Ceja {side}", "face_detail", brow, (45,35,39), 54, .48, "eyes")
        facial_union |= brow

    # Boca y nariz/detalle pequeño en la mitad inferior del rostro.
    lower_face = face & (yy > y0 + (y1-y0)*.55)
    mouth_color = lower_face & (sat > 12) & (((hue >= 150) | (hue <= 12))) & (val < 195)
    mouth = select_component_near(mouth_color, ((x0+x1)/2, y0+(y1-y0)*.72), 3, 700)
    add("mouth", "Boca", "face_detail", mouth, (125,70,80), 55, .63, "face")
    facial_union |= mouth
    nose_candidates = lower_face & (~mouth) & (val < 95)
    nose = select_component_near(nose_candidates, ((x0+x1)/2, y0+(y1-y0)*.48), 1, 80)
    add("nose_detail", "Nariz/detalle central", "face_detail", nose, (40,35,34), 55, .35, "face")
    facial_union |= nose

    # Cabello frontal y lateral vuelven encima del rostro/ojos.
    add("hair_front", "Flequillo frontal", "hair", front_bangs, (239,157,183), 60, .80, "hair")
    add("hair_side", "Mechones laterales", "hair", side_hair, (232,145,174), 61, .68, "hair")

    # Accesorios por color y cinta rosa desconectada.
    blue = foreground & (hue >= 78) & (hue <= 115) & (sat >= 40) & (~facial_union)
    yellow = foreground & (hue >= 14) & (hue <= 40) & (sat >= 55)
    add("accessory_blue", "Accesorio azul", "accessory", blue, (90,165,205), 65, .72, "accents")
    add("accessory_yellow", "Accesorio amarillo", "accessory", yellow, (225,190,80), 66, .76, "accents")
    add("accessory_pink_ribbon", "Cinta rosa lateral", "accessory", pink_ribbon, (235,145,180), 67, .70, "hair")
    add("headpiece_gray", "Sombras/adornos de cofia", "accessory", gray & (yy < h*.35), (180,180,180), 68, .45, "gray_structure")

    return sorted(parts, key=lambda p: (p.z, p.id)), visible


def save_debug_overlay(image: np.ndarray, parts: list[Part], path: Path, groups: set[str] | None = None):
    colors = [
        (80,80,85),(250,250,250),(215,105,160),(60,90,160),(245,190,145),
        (60,205,230),(255,205,55),(170,80,220),(70,190,115),(235,85,90),
        (140,190,255),(255,135,60),(210,210,215),(35,40,52)
    ]
    overlay = np.zeros_like(image)
    overlay[:] = (25,27,32)
    selected = [p for p in parts if groups is None or p.group in groups]
    for i, part in enumerate(selected):
        overlay[part.mask] = colors[i % len(colors)]
    mixed = cv2.addWeighted(image, .18, overlay, .82, 0)
    Image.fromarray(mixed).save(path)


def render_flat(parts: list[Part], shape: tuple[int,int]) -> np.ndarray:
    h,w=shape
    out=np.full((h,w,3),(24,24,26),np.uint8)
    for part in sorted(parts,key=lambda p:p.z):
        out[part.mask]=part.color
    return out


def contact_sheet(files: list[tuple[str,Path]], output: Path):
    cols=3; cellw,cellh=470,700; top=82
    sheet=Image.new("RGB",(cols*cellw,top+2*cellh),(20,23,28));d=ImageDraw.Draw(sheet)
    try:
        title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',29)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',18)
    except OSError: title=font=ImageFont.load_default()
    d.text((24,20),"ANALIZADOR 0.2B · SUBPARTES Y PROFUNDIDAD",font=title,fill='white')
    for i,(label,path) in enumerate(files):
        im=Image.open(path).convert('RGB'); im.thumbnail((420,610),Image.Resampling.LANCZOS)
        x=(i%cols)*cellw+(cellw-im.width)//2; y=top+(i//cols)*cellh+8
        sheet.paste(im,(x,y));d.rectangle((x,y,x+im.width-1,y+im.height-1),outline=(75,83,95),width=2)
        d.text(((i%cols)*cellw+18,top+(i//cols)*cellh+635),label,font=font,fill='white')
    sheet.save(output,optimize=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--max-side',type=int,default=768)
    ap.add_argument('--corrections',type=Path)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    masks_dir=args.out/'masks_0_2B';masks_dir.mkdir(exist_ok=True)

    rgb,alpha=load_rgba(args.input,args.max_side)
    parts,visible=build_parts(rgb,alpha)
    apply_corrections(parts,args.corrections)

    # Exportar máscaras y nodos.
    nodes=[]
    for index,part in enumerate(parts):
        file=f"masks_0_2B/{index:02d}_{part.id}.png"
        save_mask(part.mask,args.out/file)
        nodes.append({
            'id':part.id,'label':part.label,'group':part.group,
            'parent':part.parent,'color':'#%02X%02X%02X'%part.color,
            'z':part.z,'confidence':part.confidence,'areaPixels':int(part.mask.sum()),
            'areaFraction':round(float(part.mask.mean()),6),'bbox':bbox(part.mask),'mask':file
        })

    edges=[
        ["background","headpiece"],["background","hair_back"],["headpiece","hair_back"],
        ["hair_back","face"],["hair_back","neck"],["hair_back","sleeve_left_image"],
        ["hair_back","sleeve_right_image"],["sleeve_left_image","apron"],
        ["sleeve_right_image","apron"],["apron","bow_dark"],["neck","face"],
        ["face","eye_white_left_image"],["face","eye_white_right_image"],
        ["eye_white_left_image","eye_dark_left_image"],["eye_white_right_image","eye_dark_right_image"],
        ["eye_dark_left_image","eye_cyan_left_image"],["eye_dark_right_image","eye_cyan_right_image"],
        ["eye_cyan_left_image","eye_highlight_left_image"],["eye_cyan_right_image","eye_highlight_right_image"],
        ["face","mouth"],["face","brow_left_image"],["face","brow_right_image"],
        ["face","hair_front"],["eye_white_left_image","hair_front"],
        ["eye_white_right_image","hair_front"],["sleeve_left_image","hair_side"],
        ["sleeve_right_image","hair_side"],["hair_back","accessory_blue"],
        ["hair_back","accessory_yellow"],["hair_back","accessory_pink_ribbon"]
    ]
    existing={p.id for p in parts}
    edges=[edge for edge in edges if edge[0] in existing and edge[1] in existing]
    graph={
        'format':'cpm-layer-graph','version':'0.2B','width':int(alpha.shape[1]),'height':int(alpha.shape[0]),
        'coordinateConvention':'left/right refer to image coordinates','nodes':nodes,
        'edgesBehindToFront':edges,'renderOrder':[p.id for p in parts],
        'notes':['masks may overlap to encode occlusion','z is provisional until human review','point corrections are optional']
    }
    (args.out/'layer_graph.json').write_text(json.dumps(graph,indent=2,ensure_ascii=False),encoding='utf-8')
    template={
        'format':'cpm-mask-corrections','version':'0.2B',
        'operations':[
            {'region':'hair_front','action':'add','points':[[.50,.30]],'radius':.02},
            {'region':'hair_front','action':'remove','points':[[.20,.80]],'radius':.015}
        ],
        'instructions':'points may be normalized 0..1; delete example operations before use'
    }
    (args.out/'corrections_template.json').write_text(json.dumps(template,indent=2,ensure_ascii=False),encoding='utf-8')

    Image.fromarray(visible).save(args.out/'00_original.png')
    save_debug_overlay(visible,parts,args.out/'01_hair_split.png',{'hair'})
    save_debug_overlay(visible,parts,args.out/'02_body_split.png',{'clothes','skin','accessory'})
    save_debug_overlay(visible,parts,args.out/'03_face_parts.png',{'face_detail','skin'})
    save_debug_overlay(visible,parts,args.out/'04_all_parts.png',None)
    Image.fromarray(render_flat(parts,alpha.shape)).save(args.out/'05_flat_depth_preview.png')
    contact_sheet([
        ('ORIGINAL',args.out/'00_original.png'),('CABELLO: FONDO/FRENTE/LATERAL',args.out/'01_hair_split.png'),
        ('CUERPO, ROPA Y ACCESORIOS',args.out/'02_body_split.png'),('ROSTRO Y RASGOS',args.out/'03_face_parts.png'),
        ('TODAS LAS SUBPARTES',args.out/'04_all_parts.png'),('PREVISUALIZACIÓN POR Z',args.out/'05_flat_depth_preview.png')
    ],args.out/'VISTA_PREVIA_0_2B.png')

    print(f"Analizador 0.2B completado: {args.out}")
    print(f"Subpartes: {len(parts)} | Relaciones de profundidad: {len(edges)}")
    for p in parts:
        print(f"{p.z:02d} {p.id:28s} {p.mask.mean()*100:6.2f}%")


if __name__=='__main__':
    main()
