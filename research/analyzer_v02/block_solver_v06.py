"""BlockSolver v06 — Arquitectura modular por bloques.

Arquitectura:
  • LineArtBlock: Bordes usando glifo real "(" con optimización diferenciable
  • EyeBlock: Cada ojo (blanco, iris, pupila, pestañas)
  • HairBlock: Cabello con gradientes y sombras
  • ClothingBlock: Ropa con color calibrado
  • Ensamblador: Agrupa bloques, valida presupuesto 280 capas

Modelo de ejecución:
  1. Parser → regiones semánticas
  2. BlockSolver procesa cada bloque independiente
  3. Ensamblador crea receta final
  4. Evaluación multi-métrica
"""

import numpy as np
import cv2
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class BlendMode(Enum):
    """Modos de mezcla CPM."""
    NORMAL = "normal"  # Opacidad 1.0
    ADD = "add"        # Suma
    CUT = "cut"        # Sustrae


@dataclass
class Layer:
    """Representa una capa en la receta."""
    shape_id: str           # ID del catálogo (ej: "circle_24")
    x: float                # Posición X
    y: float                # Posición Y
    scale_x: float          # Escala X
    scale_y: float          # Escala Y
    rotation: float         # Rotación en grados
    color_bgr: Tuple[int, int, int]  # Color BGR
    blend_mode: BlendMode
    opacity: float          # 0.0-1.0 (discretizado a 1.0 en CPM)
    z_index: int            # Orden de renderizado
    block_id: str           # ID del bloque que la generó


@dataclass
class BlockRecipe:
    """Receta de un bloque (conjunto de capas)."""
    block_name: str
    layers: List[Layer] = field(default_factory=list)
    confidence: float = 1.0
    budget_used: int = 0    # Capas utilizadas
    budget_max: int = 280   # Presupuesto máximo
    status: str = "OK"      # OK, WARNING, INVALID

    def is_valid(self) -> bool:
        """Valida que el bloque sea procesable."""
        return self.status == "OK" and len(self.layers) > 0


class LineArtBlock:
    """Solver de line art usando glifo real '('.
    
    Target: Bordes de imagen (Sobel).
    Estrategia: Optimización diferenciable de posición/rotación/escala del glifo.
    """

    def __init__(self, glyph_template: Optional[np.ndarray] = None):
        self.glyph = glyph_template or self._create_synthetic_glyph()
        self.budget = 50  # Máx capas para line art

    def _create_synthetic_glyph(self) -> np.ndarray:
        """Crea glifo sintético '(' para prototipo.
        
        En producción: usar captura real de CPM Android.
        """
        size = 64
        glyph = np.zeros((size, size), dtype=np.uint8)
        # Dibujar ( como arco
        center = (size // 2, size // 2)
        cv2.ellipse(glyph, center, (12, 20), 0, -90, 90, 255, 2)
        return glyph

    def solve(
        self,
        target_region: np.ndarray,
        allowed_mask: Optional[np.ndarray] = None
    ) -> BlockRecipe:
        """Resuelve line art para una región.
        
        Args:
            target_region: Región semántica (ej: cabello)
            allowed_mask: Máscara de área permitida (opcional)
            
        Returns:
            BlockRecipe con capas de line art
        """
        recipe = BlockRecipe(
            block_name="line_art",
            budget_max=self.budget
        )

        # Calcular bordes del target
        if len(target_region.shape) == 3:
            gray = cv2.cvtColor(target_region, cv2.COLOR_BGR2GRAY)
        else:
            gray = target_region
        
        edges = cv2.Canny(gray, 50, 150)
        
        if np.sum(edges) < 10:
            recipe.status = "INVALID"
            recipe.confidence = 0.0
            return recipe
        
        # Encontrar contornos y generar capas
        # NOTA: En producción usar optimización diferenciable (PyTorch)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        layer_count = 0
        for contour in contours[:self.budget]:  # Limitar a presupuesto
            if cv2.contourArea(contour) < 5:
                continue
            
            # Aproximar contorno a puntos de control
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Calcular estadísticas del contorno
            moments = cv2.moments(contour)
            if moments['m00'] > 0:
                cx = int(moments['m10'] / moments['m00'])
                cy = int(moments['m01'] / moments['m00'])
                
                # Crear capa
                layer = Layer(
                    shape_id="line_art_parenthesis_synthetic",  # TODO: usar glifo real
                    x=float(cx),
                    y=float(cy),
                    scale_x=1.0,
                    scale_y=1.0,
                    rotation=0.0,
                    color_bgr=(0, 0, 0),  # Negro para line art
                    blend_mode=BlendMode.NORMAL,
                    opacity=1.0,
                    z_index=100 + layer_count,  # Line art al fondo
                    block_id="line_art"
                )
                recipe.layers.append(layer)
                layer_count += 1
        
        recipe.budget_used = layer_count
        recipe.confidence = min(1.0, len(recipe.layers) / 20)  # Heurística
        recipe.status = "OK" if recipe.is_valid() else "INVALID"
        
        return recipe


class EyeBlock:
    """Solver de ojos.
    
    Template: blanco, iris, pupila, pestañas, reflejo.
    Entrada: Landmarks de ojo + target visual.
    """

    def __init__(self):
        self.budget = 40  # Máx capas por ojo (×2 ojos = 80)

    def solve(
        self,
        eye_region: np.ndarray,
        eye_landmarks: np.ndarray,
        target_color: Tuple[int, int, int]
    ) -> BlockRecipe:
        """Resuelve un ojo.
        
        Args:
            eye_region: ROI del ojo
            eye_landmarks: Puntos 2D del ojo (MediaPipe)
            target_color: Color del iris (BGR)
            
        Returns:
            BlockRecipe con capas del ojo
        """
        recipe = BlockRecipe(
            block_name="eye",
            budget_max=self.budget
        )
        
        if eye_region.size == 0 or len(eye_landmarks) == 0:
            recipe.status = "INVALID"
            return recipe
        
        # Centro del ojo
        center = eye_landmarks.mean(axis=0)
        cx, cy = int(center[0]), int(center[1])
        
        # Estimación de tamaño
        distances = np.linalg.norm(eye_landmarks - center, axis=1)
        radius = distances.max()
        
        # Capa 1: Blanco del ojo (esclerótica)
        layer_white = Layer(
            shape_id="circle_large",
            x=float(cx),
            y=float(cy),
            scale_x=radius * 2.0,
            scale_y=radius * 2.0,
            rotation=0.0,
            color_bgr=(255, 255, 255),
            blend_mode=BlendMode.NORMAL,
            opacity=1.0,
            z_index=200,
            block_id="eye"
        )
        recipe.layers.append(layer_white)
        
        # Capa 2: Iris (color)
        layer_iris = Layer(
            shape_id="circle_medium",
            x=float(cx),
            y=float(cy - radius * 0.2),  # Ligeramente arriba
            scale_x=radius * 1.2,
            scale_y=radius * 1.2,
            rotation=0.0,
            color_bgr=target_color,
            blend_mode=BlendMode.NORMAL,
            opacity=1.0,
            z_index=210,
            block_id="eye"
        )
        recipe.layers.append(layer_iris)
        
        # Capa 3: Pupila (negro)
        layer_pupil = Layer(
            shape_id="circle_small",
            x=float(cx),
            y=float(cy - radius * 0.2),
            scale_x=radius * 0.5,
            scale_y=radius * 0.5,
            rotation=0.0,
            color_bgr=(0, 0, 0),
            blend_mode=BlendMode.NORMAL,
            opacity=1.0,
            z_index=220,
            block_id="eye"
        )
        recipe.layers.append(layer_pupil)
        
        # Capa 4: Reflejo (blanco pequeño)
        layer_reflection = Layer(
            shape_id="circle_tiny",
            x=float(cx - radius * 0.2),
            y=float(cy - radius * 0.3),
            scale_x=radius * 0.25,
            scale_y=radius * 0.25,
            rotation=0.0,
            color_bgr=(255, 255, 255),
            blend_mode=BlendMode.NORMAL,
            opacity=1.0,
            z_index=230,
            block_id="eye"
        )
        recipe.layers.append(layer_reflection)
        
        recipe.budget_used = len(recipe.layers)
        recipe.confidence = 0.8  # Confianza del template
        recipe.status = "OK"
        
        return recipe


class HairBlock:
    """Solver de cabello.
    
    Estrategia: Color base + gradientes (ADD/CUT capas) + sombras.
    """

    def __init__(self):
        self.budget = 80

    def solve(
        self,
        hair_region: np.ndarray,
        hair_color: Tuple[int, int, int]
    ) -> BlockRecipe:
        """Resuelve cabello.
        
        Args:
            hair_region: Máscara de región de cabello
            hair_color: Color dominante (BGR)
            
        Returns:
            BlockRecipe con capas de cabello
        """
        recipe = BlockRecipe(
            block_name="hair",
            budget_max=self.budget
        )
        
        if np.sum(hair_region) < 10:
            recipe.status = "INVALID"
            return recipe
        
        # Obtener bounding box
        y, x = np.where(hair_region > 0)
        if len(x) == 0:
            recipe.status = "INVALID"
            return recipe
        
        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()
        
        cx, cy = (x_min + x_max) // 2, (y_min + y_max) // 2
        width = x_max - x_min
        height = y_max - y_min
        
        # Capa base: rectángulo con color principal
        layer_base = Layer(
            shape_id="rectangle",
            x=float(cx),
            y=float(cy),
            scale_x=float(width),
            scale_y=float(height),
            rotation=0.0,
            color_bgr=hair_color,
            blend_mode=BlendMode.NORMAL,
            opacity=1.0,
            z_index=150,
            block_id="hair"
        )
        recipe.layers.append(layer_base)
        
        # Capas de gradiente (simuladas con ADD/CUT)
        # Generar sombras más oscuras
        dark_color = tuple(int(c * 0.6) for c in hair_color)
        light_color = tuple(int(min(255, c * 1.3)) for c in hair_color)
        
        # Sombra lateral izquierda
        layer_shadow_left = Layer(
            shape_id="rectangle_thin",
            x=float(x_min + width * 0.25),
            y=float(cy),
            scale_x=float(width * 0.3),
            scale_y=float(height),
            rotation=0.0,
            color_bgr=dark_color,
            blend_mode=BlendMode.CUT,
            opacity=0.5,
            z_index=151,
            block_id="hair"
        )
        recipe.layers.append(layer_shadow_left)
        
        # Highlight derecha
        layer_highlight = Layer(
            shape_id="rectangle_thin",
            x=float(x_max - width * 0.25),
            y=float(cy),
            scale_x=float(width * 0.2),
            scale_y=float(height * 0.7),
            rotation=0.0,
            color_bgr=light_color,
            blend_mode=BlendMode.ADD,
            opacity=0.3,
            z_index=152,
            block_id="hair"
        )
        recipe.layers.append(layer_highlight)
        
        recipe.budget_used = len(recipe.layers)
        recipe.confidence = 0.75
        recipe.status = "OK"
        
        return recipe


class ClothingBlock:
    """Solver de ropa.
    
    Similar a Hair: color base + detalles.
    """

    def __init__(self):
        self.budget = 40

    def solve(
        self,
        clothing_region: np.ndarray,
        clothing_color: Tuple[int, int, int]
    ) -> BlockRecipe:
        """Resuelve ropa."""
        recipe = BlockRecipe(
            block_name="clothing",
            budget_max=self.budget
        )
        
        if np.sum(clothing_region) < 10:
            recipe.status = "INVALID"
            return recipe
        
        # Bounding box
        y, x = np.where(clothing_region > 0)
        if len(x) == 0:
            recipe.status = "INVALID"
            return recipe
        
        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()
        
        cx, cy = (x_min + x_max) // 2, (y_min + y_max) // 2
        width = x_max - x_min
        height = y_max - y_min
        
        # Capa base
        layer_base = Layer(
            shape_id="rectangle",
            x=float(cx),
            y=float(cy),
            scale_x=float(width),
            scale_y=float(height),
            rotation=0.0,
            color_bgr=clothing_color,
            blend_mode=BlendMode.NORMAL,
            opacity=1.0,
            z_index=120,
            block_id="clothing"
        )
        recipe.layers.append(layer_base)
        
        recipe.budget_used = len(recipe.layers)
        recipe.confidence = 0.7
        recipe.status = "OK"
        
        return recipe


class BlockAssembler:
    """Ensambla bloques en receta final.
    
    Restricciones:
      • Total de capas ≤ 280
      • Máximo 25 correcciones globales
      • Bloques inválidos detienen pipeline
    """

    def __init__(self, layer_budget: int = 280, max_corrections: int = 25):
        self.layer_budget = layer_budget
        self.max_corrections = max_corrections

    def assemble(
        self,
        line_art_recipe: BlockRecipe,
        eye_left_recipe: BlockRecipe,
        eye_right_recipe: BlockRecipe,
        hair_recipe: BlockRecipe,
        clothing_recipe: BlockRecipe
    ) -> Dict:
        """Ensambla bloques en receta JSON.
        
        Returns:
            Dict con estructura: {"layers": [...], "metadata": {...}}
        """
        # Validar que ningún bloque crítico falle
        critical_blocks = [
            ("line_art", line_art_recipe),
            ("eye_left", eye_left_recipe),
            ("eye_right", eye_right_recipe),
            ("hair", hair_recipe),
            ("clothing", clothing_recipe)
        ]
        
        for name, recipe in critical_blocks:
            if recipe.status == "INVALID":
                return {
                    "status": "FAILED",
                    "reason": f"Critical block '{name}' is INVALID",
                    "layers": [],
                    "metadata": {}
                }
        
        # Recolectar todas las capas
        all_layers = []
        all_layers.extend(line_art_recipe.layers)
        all_layers.extend(eye_left_recipe.layers)
        all_layers.extend(eye_right_recipe.layers)
        all_layers.extend(hair_recipe.layers)
        all_layers.extend(clothing_recipe.layers)
        
        # Validar presupuesto
        total_layers = len(all_layers)
        if total_layers > self.layer_budget:
            return {
                "status": "FAILED",
                "reason": f"Layer budget exceeded: {total_layers} > {self.layer_budget}",
                "layers": [],
                "metadata": {}
            }
        
        # Sortear por z_index
        all_layers.sort(key=lambda l: l.z_index)
        
        # Convertir a dict para JSON
        layers_dict = []
        for layer in all_layers:
            layers_dict.append({
                "shape_id": layer.shape_id,
                "x": layer.x,
                "y": layer.y,
                "scale_x": layer.scale_x,
                "scale_y": layer.scale_y,
                "rotation": layer.rotation,
                "color_bgr": layer.color_bgr,
                "blend_mode": layer.blend_mode.value,
                "opacity": layer.opacity,
                "z_index": layer.z_index,
                "block_id": layer.block_id
            })
        
        return {
            "status": "OK",
            "reason": None,
            "layers": layers_dict,
            "metadata": {
                "total_layers": total_layers,
                "layer_budget": self.layer_budget,
                "usage_percent": (total_layers / self.layer_budget) * 100,
                "line_art_layers": len(line_art_recipe.layers),
                "eye_left_layers": len(eye_left_recipe.layers),
                "eye_right_layers": len(eye_right_recipe.layers),
                "hair_layers": len(hair_recipe.layers),
                "clothing_layers": len(clothing_recipe.layers),
                "blocks_confidence": {
                    "line_art": line_art_recipe.confidence,
                    "eye_left": eye_left_recipe.confidence,
                    "eye_right": eye_right_recipe.confidence,
                    "hair": hair_recipe.confidence,
                    "clothing": clothing_recipe.confidence
                }
            }
        }


if __name__ == "__main__":
    print("BlockSolver v06 — Módulo de arquitectura por bloques")
    print("Uso: from block_solver_v06 import LineArtBlock, EyeBlock, etc.")
