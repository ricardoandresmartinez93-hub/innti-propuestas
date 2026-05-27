"""
Servicio de integración con Innti (IA Corporativa de Quipux).
Utiliza el SDK de OpenAI apuntando al endpoint LiteLLM de Quipux.
"""
from typing import Optional, List
from openai import OpenAI

from app.config import get_settings


class InntiServiceError(Exception):
    """Error en la comunicación con Innti."""
    pass


class InntiService:
    """Servicio para generar texto usando Innti vía LiteLLM."""

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(
            base_url=settings.innti_api_base,
            api_key=settings.innti_api_key,
            timeout=30.0,  # Evitar que cuelgue indefinidamente (default SDK = 600 s)
        )
        self.model = settings.innti_model

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Genera texto usando Innti.

        Args:
            system_prompt: Contexto y rol del asistente.
            user_prompt: Instrucción específica del usuario.
            max_tokens: Máximo de tokens en la respuesta.
            temperature: Creatividad (0.0 = determinista, 1.0 = creativo).

        Returns:
            Texto generado por Innti.

        Raises:
            InntiServiceError: Si hay error en la comunicación.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise InntiServiceError(f"Error al comunicarse con Innti: {str(e)}") from e

    def generate_context_section(self, client_entity: str, proposal_title: str) -> str:
        """Genera la sección de contexto/introducción de la propuesta."""
        system_prompt = (
            "Eres un redactor de propuestas comerciales de Quipux S.A.S., empresa de tecnología "
            "especializada en soluciones de gestión de tránsito, transporte y movilidad para "
            "entidades gubernamentales. Escribe en español formal y profesional."
        )
        user_prompt = (
            f"Genera la sección de CONTEXTO/INTRODUCCIÓN para una propuesta comercial dirigida a "
            f"'{client_entity}' con título '{proposal_title}'. "
            f"La sección debe describir la visión de transformación digital de Quipux, "
            f"la importancia de la tecnología en la gestión de tránsito y movilidad, y cómo "
            f"la propuesta busca construir un gobierno más eficiente y conectado. "
            f"Extensión: 3-4 párrafos. No incluir título de sección."
        )
        return self.generate_text(system_prompt, user_prompt)

    def generate_scope_section(
        self, products: List[str], scheme_type: str
    ) -> str:
        """Genera la sección de alcance basada en los productos seleccionados."""
        system_prompt = (
            "Eres un redactor de propuestas comerciales de Quipux S.A.S. "
            "Escribe en español formal y profesional."
        )
        products_list = "\n".join(f"- {p}" for p in products)
        user_prompt = (
            f"Genera la sección de ALCANCE para una propuesta de tipo '{scheme_type}'. "
            f"Los productos/servicios incluidos son:\n{products_list}\n\n"
            f"Describe brevemente el alcance general de la propuesta, indicando que el detalle "
            f"técnico se encuentra en el anexo técnico. No incluir título de sección."
        )
        return self.generate_text(system_prompt, user_prompt)

    def generate_cover_letter(
        self,
        client_name: str,
        client_position: str,
        client_entity: str,
        proposal_subject: str,
    ) -> str:
        """Genera la carta de presentación de la propuesta."""
        system_prompt = (
            "Eres un redactor de propuestas comerciales de Quipux S.A.S. "
            "Escribe en español formal y profesional. La carta debe ser breve y profesional."
        )
        user_prompt = (
            f"Genera una carta de presentación para una propuesta comercial con los siguientes datos:\n"
            f"- Destinatario: {client_name}, {client_position}\n"
            f"- Entidad: {client_entity}\n"
            f"- Asunto: {proposal_subject}\n\n"
            f"La carta debe mencionar el compromiso de Quipux con la innovación y los excelentes "
            f"niveles de servicio. Debe indicar que la propuesta está ajustada a las expectativas "
            f"del proyecto. Firmar como 'Juan Pablo Ramírez Madrid, Vicepresidente de Nuevos Negocios'. "
            f"No incluir fecha ni encabezados de carta (solo el cuerpo)."
        )
        return self.generate_text(system_prompt, user_prompt, max_tokens=500, temperature=0.5)

    def enrich_product_description(
        self, product_name: str, base_description: str
    ) -> str:
        """Enriquece la descripción técnica de un producto para el anexo técnico."""
        system_prompt = (
            "Eres un redactor técnico de Quipux S.A.S. especializado en soluciones de "
            "tránsito y movilidad. Escribe descripciones técnicas claras y profesionales."
        )
        user_prompt = (
            f"Toma la siguiente descripción del producto '{product_name}' y redáctala de forma "
            f"más completa y profesional para incluir en un anexo técnico de una propuesta comercial:\n\n"
            f"Descripción base: {base_description}\n\n"
            f"Genera una descripción técnica de 2-3 párrafos que sea clara, profesional y destaque "
            f"los beneficios y capacidades de la solución. No inventar funcionalidades que no estén "
            f"implícitas en la descripción base."
        )
        return self.generate_text(system_prompt, user_prompt, max_tokens=800)
