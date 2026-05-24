"""
Servicio de generación de documentos Word y PDF.
Genera propuestas comerciales y anexos técnicos con la estructura estándar de Quipux.
"""
from pathlib import Path
from typing import List, Optional
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.services.portfolio_service import PortfolioProduct


class DocumentGeneratorError(Exception):
    """Error en la generación de documentos."""
    pass


class DocumentGenerator:
    """Genera documentos Word con la estructura estándar de propuestas Quipux."""

    # Textos fijos (constantes de la empresa)
    CONFIDENTIALITY_TEXT = (
        "Las partes se obligan a mantener la más estricta confidencialidad sobre toda "
        "la información que se intercambie con ocasión de la presente propuesta, incluyendo "
        "pero sin limitarse a información técnica, comercial, financiera y estratégica."
    )
    ETHICS_TEXT = (
        "Quipux S.A.S. declara que en el desarrollo de sus actividades actúa con transparencia "
        "y ética empresarial, cumpliendo con todas las normas anticorrupción y de prevención "
        "de actividades delictivas aplicables."
    )

    EXCLUDED_SERVICES_LICENSING = [
        "Desarrollos a la medida o funcionalidades nuevas no contempladas en el alcance.",
        "Actualización de motores de bases de datos.",
        "Migración de datos de sistemas legacy.",
        "Infraestructura tecnológica (servidores, redes, conectividad).",
        "Capacitación presencial en sitio (se ofrece capacitación virtual).",
    ]
    EXCLUDED_SERVICES_SUPPORT = [
        "Desarrollos a la medida o funcionalidades nuevas.",
        "Actualización de motores de bases de datos.",
        "Soporte a componentes de infraestructura no provistos por Quipux.",
        "Atención a incidentes causados por modificaciones no autorizadas.",
    ]

    IP_LICENSING = (
        "El cliente no será propietario de ninguna clase de derechos de autor ni de propiedad "
        "industrial sobre las soluciones licenciadas. Se otorga licencia de uso no exclusiva, "
        "no transferible, para las soluciones descritas en el alcance de la presente propuesta."
    )
    IP_SERVICES = (
        "Las soluciones y componentes provistos bajo este esquema de prestación de servicios "
        "son propiedad intelectual de Quipux S.A.S. El cliente tendrá derecho de uso durante "
        "la vigencia del contrato."
    )

    def generate_proposal_docx(
        self,
        title: str,
        client_name: str,
        client_position: str,
        client_entity: str,
        client_city: str,
        scheme_types: List[str],
        products: List[PortfolioProduct],
        context_text: str,
        scope_text: str,
        letter_text: str,
        economic_conditions: Optional[str] = None,
        payment_terms: Optional[str] = None,
    ) -> Document:
        """
        Genera el documento Word de la propuesta comercial.

        Returns:
            Objeto Document de python-docx listo para guardar.
        """
        doc = Document()

        # --- Configurar estilos ---
        style = doc.styles["Normal"]
        font = style.font
        font.name = "Calibri"
        font.size = Pt(11)

        # --- PORTADA ---
        doc.add_paragraph("")  # Espaciado
        doc.add_paragraph("")
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("PROPUESTA COMERCIAL")
        run.bold = True
        run.font.size = Pt(24)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title)
        run.font.size = Pt(16)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"\n\nPresentada a: {client_entity}")
        run.font.size = Pt(14)

        doc.add_page_break()

        # --- CARTA DE PRESENTACIÓN ---
        doc.add_paragraph(f"{client_city}, [FECHA]")
        doc.add_paragraph("")
        doc.add_paragraph(f"Señor(a)")
        doc.add_paragraph(f"{client_name}")
        doc.add_paragraph(f"{client_position}")
        doc.add_paragraph(f"{client_entity}")
        doc.add_paragraph("")
        doc.add_paragraph(f"Asunto: {title}")
        doc.add_paragraph("")

        if letter_text:
            doc.add_paragraph(letter_text)
        else:
            doc.add_paragraph(
                "Estamos presentando la propuesta comercial descrita en el asunto. "
                "Esperamos que esté ajustada a las expectativas y necesidades del proyecto."
            )

        doc.add_paragraph("")
        doc.add_paragraph("Atentamente,")
        doc.add_paragraph("")
        p = doc.add_paragraph()
        run = p.add_run("Juan Pablo Ramírez Madrid")
        run.bold = True
        doc.add_paragraph("Vicepresidente de Nuevos Negocios")

        doc.add_page_break()

        # --- CONTEXTO ---
        doc.add_heading("CONTEXTO", level=1)
        doc.add_paragraph(context_text or "")

        # --- ALCANCE ---
        doc.add_heading("ALCANCE", level=1)
        doc.add_paragraph(scope_text or "")

        # Lista de productos
        if products:
            doc.add_paragraph(
                "El alcance incluye las siguientes soluciones y/o componentes:"
            )
            for product in products:
                doc.add_paragraph(product.name, style="List Bullet")

        doc.add_paragraph(
            "\nNota: Invitamos a leer los anexos técnicos para identificar y comprender "
            "el alcance de cada uno de los componentes relacionados en la propuesta comercial."
        )

        # --- CONDICIONES ECONÓMICAS ---
        doc.add_heading("CONDICIONES ECONÓMICAS", level=1)
        if economic_conditions:
            doc.add_paragraph(economic_conditions)
        else:
            doc.add_paragraph(
                "[SECCIÓN DE EDICIÓN MANUAL - Agregar tablas de valorización, "
                "subtotales, IVA, valor total y formas de pago]"
            )

        if payment_terms:
            doc.add_heading("Forma de Pago", level=2)
            doc.add_paragraph(payment_terms)

        # --- SERVICIOS EXCLUIDOS ---
        doc.add_heading("SERVICIOS EXCLUIDOS", level=1)
        is_licensing = any("licensing" in s.lower() for s in scheme_types)
        excluded = (
            self.EXCLUDED_SERVICES_LICENSING if is_licensing
            else self.EXCLUDED_SERVICES_SUPPORT
        )
        doc.add_paragraph(
            "La presente propuesta no incluye los siguientes servicios:"
        )
        for item in excluded:
            doc.add_paragraph(item, style="List Bullet")

        # --- PROPIEDAD INTELECTUAL ---
        doc.add_heading(
            "ESQUEMA DE LICENCIAMIENTO Y PRESTACIÓN DE SERVICIO", level=1
        )
        doc.add_heading("Propiedad Intelectual", level=2)
        ip_text = self.IP_LICENSING if is_licensing else self.IP_SERVICES
        doc.add_paragraph(ip_text)

        # --- CONFIDENCIALIDAD ---
        doc.add_heading("Confidencialidad", level=2)
        doc.add_paragraph(self.CONFIDENTIALITY_TEXT)

        # --- ÉTICA EMPRESARIAL ---
        doc.add_heading("Transparencia y Ética Empresarial", level=2)
        doc.add_paragraph(self.ETHICS_TEXT)

        return doc

    def generate_technical_annex(
        self, products: List[PortfolioProduct]
    ) -> Document:
        """
        Genera el anexo técnico con las descripciones de los productos.

        Returns:
            Objeto Document de python-docx.
        """
        doc = Document()

        style = doc.styles["Normal"]
        font = style.font
        font.name = "Calibri"
        font.size = Pt(11)

        doc.add_heading("ANEXO TÉCNICO", level=0)
        doc.add_paragraph(
            "Descripción detallada de las soluciones y componentes "
            "incluidos en el alcance de la propuesta comercial."
        )

        for i, product in enumerate(products, 1):
            doc.add_heading(f"{i}. {product.name}", level=1)
            doc.add_paragraph(f"Tipo: {product.product_type}")
            doc.add_paragraph("")
            if product.description:
                doc.add_paragraph(product.description)
            else:
                doc.add_paragraph("[Descripción pendiente de completar]")

        return doc

    def save_document(self, doc: Document, output_path: str) -> str:
        """Guarda el documento Word en la ruta especificada."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(path))
        return str(path)
