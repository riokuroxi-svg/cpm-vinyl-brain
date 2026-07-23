#!/usr/bin/env python3
"""Analizador semántico progresivo 0.2A.

Prototipo de investigación: separa una ilustración anime de colores planos en
máscaras semánticas aproximadas y genera objetivos coarse-to-fine. No coloca
vinilos todavía.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from sklearn.cluster import MiniBatchKMeans


@dataclass
class Region:
    id: str
    label: str
    color: tuple[int, int, int]
    mask: np.ndarray
    suggested_z: int
    confidence: float
    source: str = "color-heuristic-v0.2A"


def load_rgba(path: Path, max_side: int) -> tuple[np.ndarray, np.ndarray]:
    image = Image.open(path).convert("RGBA")
    scale = min(1.0, max_side / max(image.size))
    if scale < 1:
        image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    rgba = np.asarray(image, dtype=np.uint8)
    return rgba[:, :, :3], rgba[:, :, 3]


def composite(rgb: np.ndarray, alpha: np.ndarray, bg=(24, 24, 26)) -> np.ndarray:
    a = alpha.astype(np.float32)[..., None] / 255.0
    background = np.full_like(rgb, bg, dtype=np.float32)
    return np.clip(rgb.astype(np.float32) * a + background * (1 - a), 0, 255).astype(np.uint8)


def clean(mask: np.ndarray, radius: int = 3, min_area: int = 0) -> np.ndarray:
    m = (mask.astype(np.uint8) * 255)
    if radius > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    if min_area > 0:
        n, labels, stats, _ = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8), 8)
        kept = np.zeros_like(m)
        for i in range(1, n):
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                kept[labels == i] = 255
        m = kept
    return m > 0


def fill_external_components(mask: np.ndarray, min_area: int) -> np.ndarray:
    contours, _ = cv2.findContours((mask.astype(np.uint8) * 255), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros(mask.shape, np.uint8)
    for contour in contours:
        if cv2.contourArea(contour) >= min_area:
            cv2.drawContours(out, [contour], -1, 255, -1)
    return out > 0


def solidify_main_face(mask: np.ndarray, min_area: int) -> np.ndarray:
    """Cierra ojos/boca del componente principal sin conocer aún sus etiquetas.

    El casco convexo actúa como rostro base. El cabello visible se vuelve a pintar
    después, por lo que los mechones recuperan su oclusión natural.
    """
    binary = mask.astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    out = (fill_external_components(mask, min_area).astype(np.uint8) * 255)
    candidates = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= min_area]
    if candidates:
        # Favorecer el componente grande situado en la mitad superior: normalmente el rostro.
        candidates.sort(key=lambda i: (stats[i, cv2.CC_STAT_AREA] * (1.4 if stats[i, cv2.CC_STAT_TOP] < mask.shape[0]*.65 else 1.0)), reverse=True)
        main = (labels == candidates[0]).astype(np.uint8) * 255
        contours, _ = cv2.findContours(main, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(contour)
            # Los ojos suelen abrir el contorno de piel hacia el cabello. Dos puntos
            # superiores reconstruyen la frente; el cabello se pinta después y recorta
            # nuevamente el flequillo visible.
            top_y = max(0, round(y - h * .42))
            anchors = np.array([[[round(x + w*.10), top_y]], [[round(x + w*.90), top_y]]], np.int32)
            hull = cv2.convexHull(np.vstack([contour, anchors]))
            cv2.drawContours(out, [hull], -1, 255, -1)
    return out > 0


def median_color(rgb: np.ndarray, mask: np.ndarray, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    pixels = rgb[mask]
    if len(pixels) == 0:
        return fallback
    value = np.median(pixels, axis=0).round().astype(int)
    return tuple(map(int, value))


def bbox(mask: np.ndarray) -> list[int]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return [0, 0, 0, 0]
    return [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]


def analyze_semantics(rgb: np.ndarray, alpha: np.ndarray) -> tuple[list[Region], np.ndarray]:
    h, w = alpha.shape
    total = h * w
    foreground = alpha > 20
    visible = composite(rgb, alpha)
    hsv = cv2.cvtColor(visible, cv2.COLOR_RGB2HSV)
    hue, sat, val = cv2.split(hsv)
    r, g, b = [visible[:, :, i].astype(np.int16) for i in range(3)]

    # La transparencia del PNG nos da un fondo confiable para esta primera prueba.
    background = ~foreground

    # Rosa/rojo magenta: masa principal de cabello. Se conservan solo componentes grandes.
    hair_raw = foreground & (((hue >= 155) | (hue <= 4)) & (sat >= 25) & (r > g + 12) & (r > b + 3))
    hair = clean(hair_raw, radius=2, min_area=max(40, int(total * 0.0007)))

    # Piel antes que blanco: ambos tienen baja saturación, pero la piel conserva
    # una diferencia cálida R-B. Esta prioridad evita clasificar el rostro como delantal.
    skin_raw = foreground & (~hair) & (hue <= 32) & (sat >= 6) & (sat < 82) & (val > 135)
    skin_raw &= (r - b >= 9) & (r >= g) & (g >= b - 18)
    skin = clean(skin_raw, radius=3, min_area=max(50, int(total * 0.0008)))

    # Blanco y grises claros estructurales (cofia, delantal, puños). Los blancos
    # de los ojos se cubrirán con la máscara sólida del rostro en el Nivel 0.
    white_raw = foreground & (~skin) & (sat < 42) & (val > 188)
    white = clean(white_raw, radius=2, min_area=max(60, int(total * 0.0012)))

    # Rellenar huecos internos de las regiones de piel elimina ojos/boca en el Nivel 0.
    skin_base = solidify_main_face(skin, min_area=max(100, int(total * 0.0015)))

    # Ropa oscura: píxeles opacos oscuros; el fondo transparente ya quedó fuera.
    clothes_raw = foreground & (val < 112) & (~hair)
    clothes = clean(clothes_raw, radius=3, min_area=max(100, int(total * 0.0025)))

    # Grises medios estructurales (sombras, delantal gris).
    gray_raw = foreground & (sat < 52) & (val >= 75) & (val <= 205) & (~skin_base) & (~hair) & (~clothes)
    gray = clean(gray_raw, radius=2, min_area=max(80, int(total * 0.0015)))

    # Colores pequeños intensos: ojos azules y accesorios amarillos/azules.
    accents_raw = foreground & (sat >= 45) & (~hair) & (~skin_base) & (~clothes)
    accents = clean(accents_raw, radius=1, min_area=max(20, int(total * 0.00015)))

    # Todo lo visible que queda se registra como detalle/desconocido.
    occupied = background | hair | white | skin_base | clothes | gray | accents
    details = foreground & (~occupied)

    # Evitar doble asignación con una prioridad explícita para la salida de máscaras.
    white &= ~hair
    clothes &= ~(hair | skin_base | white)
    gray &= ~(hair | skin_base | white | clothes)
    accents &= ~(hair | skin_base | white | clothes | gray)
    details &= ~(hair | skin_base | white | clothes | gray | accents)

    regions = [
        Region("background", "Fondo", (24, 24, 26), background, 0, 1.00, "alpha"),
        Region("white_structure", "Cofia/delantal/blancos", median_color(visible, white, (245,245,245)), white, 1, .78),
        Region("hair", "Cabello", median_color(visible, hair, (233,145,177)), hair, 2, .88),
        Region("clothes", "Ropa oscura", median_color(visible, clothes, (38,39,40)), clothes, 3, .82),
        Region("gray_structure", "Grises estructurales", median_color(visible, gray, (190,190,190)), gray, 4, .62),
        Region("skin", "Piel/rostro", median_color(visible, skin, (242,226,215)), skin_base, 5, .83),
        Region("accents", "Ojos/accesorios de color", median_color(visible, accents, (90,160,190)), accents, 6, .55),
        Region("details", "Detalles por clasificar", median_color(visible, details, (80,80,80)), details, 7, .35),
    ]
    return regions, visible


def quantize_lab(image: np.ndarray, foreground: np.ndarray, colors: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    pixels = lab[foreground]
    if len(pixels) == 0:
        return image.copy(), np.zeros(image.shape[:2], np.int32)
    rng = np.random.default_rng(seed)
    count = min(60000, len(pixels))
    sample = pixels[rng.choice(len(pixels), count, replace=False)]
    model = MiniBatchKMeans(n_clusters=colors, random_state=seed, batch_size=4096, n_init=3, max_iter=120)
    model.fit(sample)
    labels = np.full(image.shape[:2], -1, np.int32)
    labels[foreground] = model.predict(pixels)
    centers = np.clip(model.cluster_centers_, 0, 255).astype(np.uint8)
    quant_lab = np.zeros_like(lab)
    quant_lab[foreground] = centers[labels[foreground]]
    quant_rgb = cv2.cvtColor(quant_lab, cv2.COLOR_LAB2RGB)
    quant_rgb[~foreground] = image[~foreground]
    return quant_rgb, labels


def render_base(regions: list[Region], shape: tuple[int, int]) -> np.ndarray:
    h, w = shape
    canvas = np.full((h, w, 3), (24, 24, 26), np.uint8)
    by_id = {r.id: r for r in regions}
    # Mapa visible plano. La división frente/atrás se añadirá en 0.2B.
    for key in ["white_structure", "clothes", "gray_structure", "skin", "hair"]:
        region = by_id[key]
        canvas[region.mask] = region.color
    return canvas


def component_detail_masks(labels: np.ndarray, foreground: np.ndarray, min_fraction: float) -> np.ndarray:
    total = labels.size
    keep = np.zeros(labels.shape, bool)
    for label in np.unique(labels[foreground]):
        cluster = labels == label
        n, cc, stats, _ = cv2.connectedComponentsWithStats(cluster.astype(np.uint8), 8)
        for i in range(1, n):
            if stats[i, cv2.CC_STAT_AREA] >= total * min_fraction:
                keep[cc == i] = True
    return keep


def save_mask(mask: np.ndarray, path: Path) -> None:
    rgba = np.zeros((*mask.shape, 4), np.uint8)
    rgba[mask, :3] = 255
    rgba[mask, 3] = 255
    Image.fromarray(rgba, "RGBA").save(path)


def save_overlay(image: np.ndarray, regions: list[Region], path: Path) -> None:
    palette = {
        "background": (35, 35, 38), "white_structure": (245, 245, 245),
        "hair": (255, 85, 150), "clothes": (45, 55, 70),
        "gray_structure": (170, 170, 180), "skin": (255, 205, 155),
        "accents": (40, 210, 255), "details": (255, 210, 40),
    }
    overlay = np.zeros_like(image)
    by_id = {r.id: r for r in regions}
    # Orden de visualización aproximado: la piel tapa rasgos antiguos y el
    # cabello vuelve a colocarse encima como flequillo visible.
    for key in ["background", "white_structure", "clothes", "gray_structure", "skin", "hair", "accents", "details"]:
        region = by_id[key]
        overlay[region.mask] = palette[region.id]
    mixed = cv2.addWeighted(image, .35, overlay, .65, 0)
    Image.fromarray(mixed).save(path)


def make_contact_sheet(files: list[tuple[str, Path]], path: Path) -> None:
    thumbs = []
    for label, file in files:
        im = Image.open(file).convert("RGB")
        im.thumbnail((420, 620), Image.Resampling.LANCZOS)
        thumbs.append((label, im))
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    cell_w, cell_h = 460, 700
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h + 82), (20, 23, 28))
    draw = ImageDraw.Draw(sheet)
    try:
        title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 19)
    except OSError:
        title = font = ImageFont.load_default()
    draw.text((24, 22), "ANALIZADOR 0.2A · DESCOMPOSICIÓN PROGRESIVA", fill="white", font=title)
    for i, (label, im) in enumerate(thumbs):
        x = (i % cols) * cell_w + (cell_w - im.width) // 2
        y0 = 82 + (i // cols) * cell_h
        y = y0 + 10
        sheet.paste(im, (x, y))
        draw.text(((i % cols) * cell_w + 20, y0 + 642), label, fill="white", font=font)
    sheet.save(path, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-side", type=int, default=768)
    parser.add_argument("--colors", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260720)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    masks_dir = args.out / "masks"
    masks_dir.mkdir(exist_ok=True)

    rgb, alpha = load_rgba(args.input, args.max_side)
    regions, visible = analyze_semantics(rgb, alpha)
    foreground = alpha > 20
    quantized, labels = quantize_lab(visible, foreground, args.colors, args.seed)
    base = render_base(regions, alpha.shape)

    by_id = {r.id: r for r in regions}
    # Detalle progresivo: componentes grandes fuera del rostro, luego medianos y finalmente todo.
    large = component_detail_masks(labels, foreground, .0045)
    medium = component_detail_masks(labels, foreground, .00065)
    face = by_id["skin"].mask
    level1_mask = large & (~face)
    level2_mask = medium
    level1 = base.copy(); level1[level1_mask] = quantized[level1_mask]
    level2 = base.copy(); level2[level2_mask] = quantized[level2_mask]
    level3 = quantized

    Image.fromarray(visible).save(args.out / "00_original_compuesto.png")
    Image.fromarray(base).save(args.out / "01_nivel_base.png")
    Image.fromarray(level1).save(args.out / "02_nivel_estructura.png")
    Image.fromarray(level2).save(args.out / "03_nivel_rasgos.png")
    Image.fromarray(level3).save(args.out / "04_nivel_cuantizado.png")
    save_overlay(visible, regions, args.out / "05_mapa_semantico.png")

    metadata = {
        "format": "cpm-semantic-regions",
        "version": "0.2A",
        "input": str(args.input),
        "width": int(alpha.shape[1]),
        "height": int(alpha.shape[0]),
        "paletteSize": args.colors,
        "seed": args.seed,
        "regions": [],
        "suggestedOrder": ["background", "white_structure", "hair_back", "clothes", "skin", "facial_features", "hair_front", "accents"],
        "notes": [
            "hair_back/hair_front aún no se separan automáticamente en 0.2A",
            "las etiquetas provienen de heurísticas de color; el backend AnimeSeg será conectable",
            "las máscaras están listas para corrección humana y ajuste de vinilos"
        ]
    }
    for index, region in enumerate(regions):
        save_mask(region.mask, masks_dir / f"{index:02d}_{region.id}.png")
        metadata["regions"].append({
            "id": region.id,
            "label": region.label,
            "color": "#%02X%02X%02X" % region.color,
            "areaPixels": int(region.mask.sum()),
            "areaFraction": round(float(region.mask.mean()), 6),
            "bbox": bbox(region.mask),
            "suggestedZ": region.suggested_z,
            "confidence": region.confidence,
            "source": region.source,
            "mask": f"masks/{index:02d}_{region.id}.png"
        })
    (args.out / "regions.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    make_contact_sheet([
        ("ORIGINAL", args.out / "00_original_compuesto.png"),
        ("NIVEL 0 · BASE", args.out / "01_nivel_base.png"),
        ("NIVEL 1 · ESTRUCTURA", args.out / "02_nivel_estructura.png"),
        ("NIVEL 2 · RASGOS", args.out / "03_nivel_rasgos.png"),
        ("NIVEL 3 · CUANTIZADO", args.out / "04_nivel_cuantizado.png"),
        ("MAPA SEMÁNTICO", args.out / "05_mapa_semantico.png"),
    ], args.out / "VISTA_PREVIA_ANALIZADOR.png")

    print(f"Analizador 0.2A completado: {args.out}")
    for region in regions:
        print(f"- {region.id:18s} {region.mask.mean()*100:6.2f}%  {region.color}")


if __name__ == "__main__":
    main()
