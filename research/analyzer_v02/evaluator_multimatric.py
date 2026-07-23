"""Evaluador Multi-Métrica para calidad de receta.

Problema anterior: SSIM global como única verdad → resultados engañosos.

Solución: Combinar múltiples métricas ponderadas:
  • Landmark Distance (40%): Distancia euclidiana de ojos, boca, etc.
  • Edge Correlation (30%): Correlación de bordes (Sobel)
  • Color Distribution (20%): Comparación de histogramas LAB
  • Efficiency (10%): Penalización por uso de capas
"""

import cv2
import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

try:
    import mediapipe as mp
except ImportError:
    mp = None
    logger.warning("MediaPipe no instalado para landmark detection")


@dataclass
class EvaluationResult:
    """Resultado de evaluación completo."""
    overall_score: float  # 0-1, más alto = mejor
    landmark_distance: float
    edge_correlation: float
    color_distribution: float
    efficiency_score: float
    per_metric_scores: Dict[str, float]
    interpretation: str  # Descripción legible


class MultiMetricEvaluator:
    """Evaluador multi-métrica de calidad de receta."""

    def __init__(self, layer_budget: int = 280):
        self.layer_budget = layer_budget
        if mp is not None:
            self.mp_face = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1
            )
        else:
            self.mp_face = None
        
        # Pesos de cada métrica
        self.weights = {
            "landmark_distance": 0.40,
            "edge_correlation": 0.30,
            "color_distribution": 0.20,
            "efficiency": 0.10
        }

    def evaluate(
        self,
        result_image: np.ndarray,
        target_image: np.ndarray,
        recipe_layers_count: int
    ) -> EvaluationResult:
        """Evalúa calidad de receta generada.
        
        Args:
            result_image: Imagen generada por el brain
            target_image: Imagen objetivo
            recipe_layers_count: Número de capas en la receta
            
        Returns:
            EvaluationResult con puntuación detallada
        """
        # Asegurar que ambas imágenes tienen el mismo tamaño
        if result_image.shape != target_image.shape:
            target_image = cv2.resize(target_image, (result_image.shape[1], result_image.shape[0]))
        
        # Calcular cada métrica
        landmark_score = self._evaluate_landmarks(result_image, target_image)
        edge_score = self._evaluate_edges(result_image, target_image)
        color_score = self._evaluate_color_distribution(result_image, target_image)
        efficiency_score = self._evaluate_efficiency(recipe_layers_count)
        
        # Calcular puntaje general ponderado
        overall_score = (
            self.weights["landmark_distance"] * landmark_score +
            self.weights["edge_correlation"] * edge_score +
            self.weights["color_distribution"] * color_score +
            self.weights["efficiency"] * efficiency_score
        )
        
        # Clip a [0, 1]
        overall_score = np.clip(overall_score, 0.0, 1.0)
        
        per_metric = {
            "landmark_distance": landmark_score,
            "edge_correlation": edge_score,
            "color_distribution": color_score,
            "efficiency": efficiency_score
        }
        
        # Interpretar resultado
        interpretation = self._interpret_score(overall_score, per_metric)
        
        return EvaluationResult(
            overall_score=overall_score,
            landmark_distance=landmark_score,
            edge_correlation=edge_score,
            color_distribution=color_score,
            efficiency_score=efficiency_score,
            per_metric_scores=per_metric,
            interpretation=interpretation
        )

    def _evaluate_landmarks(self, result_img: np.ndarray, target_img: np.ndarray) -> float:
        """Métrica 1: Distancia de landmarks faciales.
        
        Detecta ojos, nariz, boca en ambas imágenes.
        Calcula distancia euclidiana promedio.
        
        Score: 1.0 - (promedio_distancia / max_distancia_posible)
        """
        if self.mp_face is None:
            logger.warning("MediaPipe no disponible. Landmark score = 0.5 (neutral)")
            return 0.5
        
        try:
            # Detectar landmarks en ambas imágenes
            result_landmarks = self._get_landmarks(result_img)
            target_landmarks = self._get_landmarks(target_img)
            
            if result_landmarks is None or target_landmarks is None:
                return 0.5
            
            if len(result_landmarks) == 0 or len(target_landmarks) == 0:
                return 0.5
            
            # Calcular distancia euclidiana promedio
            # Usar los 4 landmarks principales: ojo izq, ojo der, nariz, boca
            key_indices = [33, 263, 1, 152]  # left eye, right eye, nose, mouth
            
            distances = []
            for idx in key_indices:
                if idx < len(result_landmarks) and idx < len(target_landmarks):
                    dist = np.linalg.norm(
                        result_landmarks[idx] - target_landmarks[idx]
                    )
                    distances.append(dist)
            
            if not distances:
                return 0.5
            
            avg_distance = np.mean(distances)
            
            # Normalizar: distancia < 10 px = máxima similitud
            # distancia > 100 px = mínima similitud
            max_distance = 100.0
            score = 1.0 - (avg_distance / max_distance)
            score = np.clip(score, 0.0, 1.0)
            
            logger.info(f"Landmark score: {score:.3f} (avg distance: {avg_distance:.1f}px)")
            return score
            
        except Exception as e:
            logger.error(f"Error en landmark evaluation: {e}")
            return 0.5

    def _get_landmarks(self, image_bgr: np.ndarray) -> np.ndarray:
        """Extrae landmarks usando MediaPipe."""
        try:
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            results = self.mp_face.process(image_rgb)
            
            if not results.multi_face_landmarks:
                return None
            
            h, w = image_bgr.shape[:2]
            landmarks = results.multi_face_landmarks[0]
            
            points = np.array([
                [lm.x * w, lm.y * h]
                for lm in landmarks.landmark
            ])
            
            return points
        except Exception as e:
            logger.error(f"Error extracting landmarks: {e}")
            return None

    def _evaluate_edges(self, result_img: np.ndarray, target_img: np.ndarray) -> float:
        """Métrica 2: Correlación de bordes (Sobel).
        
        Extrae bordes con Sobel.
        Calcula correlación cruzada normalizada.
        
        Score: correlación (0 a 1)
        """
        try:
            # Convertir a escala de grises
            if len(result_img.shape) == 3:
                result_gray = cv2.cvtColor(result_img, cv2.COLOR_BGR2GRAY)
                target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
            else:
                result_gray = result_img
                target_gray = target_img
            
            # Calcular Sobel en ambas direcciones
            result_edges = self._compute_edges(result_gray)
            target_edges = self._compute_edges(target_gray)
            
            # Correlación cruzada normalizada
            correlation = cv2.matchTemplate(
                result_edges.astype(np.float32),
                target_edges.astype(np.float32),
                cv2.TM_CCOEFF
            )
            
            # Normalizar correlación a [0, 1]
            # (Este es un aproximado; se puede mejorar)
            max_corr = np.max(correlation)
            score = max_corr / (result_edges.size * 255.0)  # Normalizar
            score = np.clip(score, 0.0, 1.0)
            
            logger.info(f"Edge correlation score: {score:.3f}")
            return score
            
        except Exception as e:
            logger.error(f"Error en edge evaluation: {e}")
            return 0.5

    def _compute_edges(self, gray_image: np.ndarray) -> np.ndarray:
        """Calcula bordes con Sobel."""
        sobel_x = cv2.Sobel(gray_image, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray_image, cv2.CV_64F, 0, 1, ksize=3)
        edges = np.sqrt(sobel_x**2 + sobel_y**2).astype(np.uint8)
        return edges

    def _evaluate_color_distribution(self, result_img: np.ndarray, target_img: np.ndarray) -> float:
        """Métrica 3: Distribución de color (histogramas LAB).
        
        Convierte a LAB.
        Calcula histogramas para cada canal.
        Compara con EMD (Earth Mover's Distance) o Bhattacharyya.
        
        Score: 1.0 - distancia_normalizada
        """
        try:
            # Convertir a LAB
            result_lab = cv2.cvtColor(result_img, cv2.COLOR_BGR2LAB)
            target_lab = cv2.cvtColor(target_img, cv2.COLOR_BGR2LAB)
            
            # Calcular histogramas para cada canal
            hist_result = []
            hist_target = []
            
            for i in range(3):  # L, a, b
                h_result = cv2.calcHist([result_lab], [i], None, [256], [0, 256])
                h_target = cv2.calcHist([target_lab], [i], None, [256], [0, 256])
                
                # Normalizar
                h_result = cv2.normalize(h_result, h_result).flatten()
                h_target = cv2.normalize(h_target, h_target).flatten()
                
                # Comparar con chi-square
                distance = cv2.compareHist(h_result, h_target, cv2.HISTCMP_CHISQR)
                hist_result.append(distance)
            
            # Promedio de distancias
            avg_distance = np.mean(hist_result)
            
            # Normalizar: distancia < 1.0 = máxima similitud
            score = 1.0 - np.tanh(avg_distance)  # Función suave
            score = np.clip(score, 0.0, 1.0)
            
            logger.info(f"Color distribution score: {score:.3f} (avg distance: {avg_distance:.3f})")
            return score
            
        except Exception as e:
            logger.error(f"Error en color evaluation: {e}")
            return 0.5

    def _evaluate_efficiency(self, layers_count: int) -> float:
        """Métrica 4: Eficiencia de uso de capas.
        
        Score: 1.0 si layers ≤ 280
        Score decrece linealmente si layers > 280
        Penalidad severa si layers >> 280
        """
        if layers_count <= self.layer_budget:
            # Bonus por usar pocas capas (eficiencia)
            efficiency = 1.0 - (layers_count / self.layer_budget) * 0.2  # Máximo -20%
        else:
            # Penalidad por exceder presupuesto
            excess = layers_count - self.layer_budget
            efficiency = 1.0 - (excess / self.layer_budget) * 1.5  # Penalidad severa
        
        efficiency = np.clip(efficiency, 0.0, 1.0)
        
        logger.info(f"Efficiency score: {efficiency:.3f} (layers: {layers_count}/{self.layer_budget})")
        return efficiency

    def _interpret_score(self, overall_score: float, metrics: Dict[str, float]) -> str:
        """Interpreta puntaje general en texto legible."""
        if overall_score >= 0.85:
            status = "🟢 EXCELLENT"
        elif overall_score >= 0.70:
            status = "🟡 GOOD"
        elif overall_score >= 0.50:
            status = "🟠 ACCEPTABLE"
        else:
            status = "🔴 NEEDS_IMPROVEMENT"
        
        # Identificar métrica débil
        weakest = min(metrics, key=metrics.get)
        weakest_value = metrics[weakest]
        
        if weakest_value < 0.5:
            recommendation = f"⚠️  Improve {weakest}: {weakest_value:.2f} < 0.50"
        else:
            recommendation = "✓ All metrics acceptable"
        
        return f"{status} | Score: {overall_score:.2%} | {recommendation}"


def main():
    """Test del evaluador."""
    print("Evaluador Multi-Métrica")
    print("Uso: from evaluator_multimatric import MultiMetricEvaluator")
    
    # Crear evaluador
    evaluator = MultiMetricEvaluator(layer_budget=280)
    
    # Test dummy
    h, w = 512, 512
    result_img = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    target_img = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    
    evaluation = evaluator.evaluate(result_img, target_img, recipe_layers_count=150)
    
    print(f"\nEvaluation Result:")
    print(f"  Overall Score: {evaluation.overall_score:.3f}")
    print(f"  Per-Metric Scores:")
    for name, score in evaluation.per_metric_scores.items():
        print(f"    {name}: {score:.3f}")
    print(f"\n  {evaluation.interpretation}")


if __name__ == "__main__":
    main()
