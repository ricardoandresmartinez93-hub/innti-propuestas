"""
Servicio de generación de documentos Word y PDF.
Genera propuestas comerciales y anexos técnicos con la estructura estándar de Quipux.
"""
from pathlib import Path
from typing import List, Optional
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

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
    # PLACEHOLDER – Reemplazar con texto oficial de Jurídica cuando lo entregue el área legal
    IP_SUPPORT_MAINTENANCE = (
        "Las soluciones objeto de soporte y mantenimiento son propiedad intelectual de Quipux S.A.S. "
        "El cliente tiene derecho a recibir las actualizaciones y parches incluidos en el contrato. "
        "La prestación del servicio de soporte no transfiere ningún derecho de propiedad intelectual "
        "sobre el software base al cliente."
    )
    # PLACEHOLDER – Reemplazar con texto oficial de Jurídica cuando lo entregue el área legal
    IP_SAAS = (
        "El software es provisto bajo la modalidad de Software como Servicio (SaaS) hospedado en la "
        "infraestructura de Quipux S.A.S. El cliente accede al uso de la plataforma a través de internet "
        "sin necesidad de instalación local. Quipux retiene todos los derechos de propiedad intelectual "
        "sobre la plataforma, bases de datos y herramientas relacionadas."
    )

    def _add_page_number(self, paragraph):
        """Añade numeración de página al párrafo."""
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Inicia el campo
        run = paragraph.add_run()
        fldChar = OxmlElement('w:fldChar')
        fldChar.set(qn('w:fldCharType'), 'begin')
        run._r.append(fldChar)

        # Añade el comando PAGE
        run = paragraph.add_run()
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = "PAGE"
        run._r.append(instrText)

        # Cierra el campo
        run = paragraph.add_run()
        fldChar = OxmlElement('w:fldChar')
        fldChar.set(qn('w:fldCharType'), 'end')
        run._r.append(fldChar)

    @classmethod
    def get_payment_type_from_scheme(cls, scheme_type: str) -> str:
        """Mapea el tipo de esquema a un tipo de pago en español."""
        mapping = {
            "licensing": "pago único",
            "services": "pago mensual",
            "support_maintenance": "pago anual"
        }
        return mapping.get(scheme_type.lower(), "por definir")

    def _add_economic_conditions_table(self, doc, payment_type: str):
        """
        Agrega una tabla de condiciones económicas con el formato estándar de Quipux.
        """
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        
        # Encabezado
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Concepto'
        hdr_cells[1].text = 'Valor'
        
        # Aplicar estilo al encabezado (Azul Quipux #1a365d, texto blanco)
        for cell in hdr_cells:
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            shd = OxmlElement('w:shd')
            shd.set(qn('w:fill'), '1A365D')
            tcPr.append(shd)
            
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.runs[0]
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        # 3 filas vacías con placeholders
        for _ in range(3):
            row_cells = table.add_row().cells
            row_cells[0].text = '[Concepto]'
            row_cells[1].text = '$0'

        # Totales
        totals = [
            ("Subtotal", "$0"),
            ("IVA (19%)", "$0"),
            ("Total", "$0")
        ]
        
        for label, val in totals:
            row_cells = table.add_row().cells
            row_cells[0].text = label
            row_cells[1].text = val
            row_cells[0].paragraphs[0].runs[0].font.bold = True

        # Párrafo de forma de pago
        p = doc.add_paragraph()
        p.add_run(f"\nForma de Pago: {payment_type}")

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
        payment_frequency: Optional[str] = None,
    ) -> Document:
        """
        Genera el documento Word de la propuesta comercial con formato profesional Quipux.

        Returns:
            Objeto Document de python-docx listo para guardar.
        """
        doc = Document()

        # --- Configuración de Márgenes ---
        section = doc.sections[0]
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.5)

        # --- Configurar estilos ---
        # Normal: Calibri 11pt, Justificado, Interlineado 1.15
        style = doc.styles["Normal"]
        font = style.font
        font.name = "Calibri"
        font.size = Pt(11)
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        style.paragraph_format.line_spacing = 1.15
        style.paragraph_format.space_after = Pt(10)

        # Heading 1: Azul Quipux #1a365d, 16pt
        h1 = doc.styles["Heading 1"]
        h1.font.name = "Calibri"
        h1.font.size = Pt(16)
        h1.font.bold = True
        h1.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
        h1.paragraph_format.space_before = Pt(18)
        h1.paragraph_format.space_after = Pt(12)

        # Heading 2: Gris Quipux #2d3748, 13pt
        h2 = doc.styles["Heading 2"]
        h2.font.name = "Calibri"
        h2.font.size = Pt(13)
        h2.font.bold = True
        h2.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
        h2.paragraph_format.space_before = Pt(14)
        h2.paragraph_format.space_after = Pt(8)

        # --- PORTADA ---
        doc.add_paragraph("\n\n\n")
        
        # Logo placeholder
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_logo = p_logo.add_run("[LOGO QUIPUX]")
        run_logo.bold = True
        run_logo.font.size = Pt(12)
        
        doc.add_paragraph("\n\n")
        
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("PROPUESTA COMERCIAL")
        run.bold = True
        run.font.size = Pt(26)
        run.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title.upper())
        run.font.size = Pt(18)
        run.bold = True

        doc.add_paragraph("\n\n\n")

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"Presentada a:\n{client_entity}")
        run.font.size = Pt(14)
        
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"\n{client_name}\n{client_position}")
        run.font.size = Pt(12)

        doc.add_page_break()

        # --- TABLA DE CONTENIDO ---
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("TABLA DE CONTENIDO")
        run.bold = True
        run.font.size = Pt(14)
        doc.add_paragraph("\n[El índice se genera automáticamente al actualizar campos en Word]")
        
        doc.add_page_break()

        # --- CARTA DE PRESENTACIÓN ---
        doc.add_paragraph(f"{client_city}, [FECHA]")
        doc.add_paragraph("")
        p = doc.add_paragraph("Señor(a)")
        p.paragraph_format.space_after = Pt(0)
        p = doc.add_paragraph(f"{client_name}")
        p.paragraph_format.space_after = Pt(0)
        p = doc.add_paragraph(f"{client_position}")
        p.paragraph_format.space_after = Pt(0)
        p = doc.add_paragraph(f"{client_entity}")
        
        doc.add_paragraph("")
        p = doc.add_paragraph()
        run = p.add_run(f"Asunto: {title}")
        run.bold = True
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
        p = doc.add_paragraph("Vicepresidente de Nuevos Negocios")
        p.paragraph_format.space_after = Pt(0)
        doc.add_paragraph("Quipux S.A.S.")

        doc.add_page_break()

        # --- CUERPO DEL DOCUMENTO ---
        # CONTEXTO
        doc.add_heading("1. CONTEXTO", level=1)
        doc.add_paragraph(context_text or "")

        # ALCANCE
        doc.add_heading("2. ALCANCE", level=1)
        doc.add_paragraph(scope_text or "")

        if products:
            doc.add_paragraph(
                "El alcance incluye las siguientes soluciones y/o componentes:"
            )
            for product in products:
                doc.add_paragraph(product.name, style="List Bullet")

        doc.add_paragraph(
            "Nota: Invitamos a leer los anexos técnicos para identificar y comprender "
            "el alcance de cada uno de los componentes relacionados en la propuesta comercial."
        )

        # CONDICIONES ECONÓMICAS
        doc.add_heading("3. CONDICIONES ECONÓMICAS", level=1)
        if economic_conditions:
            doc.add_paragraph(economic_conditions)
        else:
            p_type = self.get_payment_type_from_scheme(scheme_types[0] if scheme_types else "")
            self._add_economic_conditions_table(doc, p_type)

        if payment_terms:
            doc.add_heading("Forma de Pago", level=2)
            doc.add_paragraph(payment_terms)

        # SERVICIOS EXCLUIDOS
        doc.add_heading("4. SERVICIOS EXCLUIDOS", level=1)
        is_licensing = any("licensing" in s.lower() for s in scheme_types)
        excluded = (
            self.EXCLUDED_SERVICES_LICENSING if is_licensing
            else self.EXCLUDED_SERVICES_SUPPORT
        )
        doc.add_paragraph("La presente propuesta no incluye los siguientes servicios:")
        for item in excluded:
            doc.add_paragraph(item, style="List Bullet")

        # PROPIEDAD INTELECTUAL Y LEGAL
        doc.add_heading("5. ESQUEMA DE LICENCIAMIENTO Y PRESTACIÓN DE SERVICIO", level=1)
        
        doc.add_heading("5.1. Propiedad Intelectual", level=2)
        
        added_ips = set()
        for scheme in scheme_types:
            scheme_lower = scheme.lower()
            if "licensing" in scheme_lower and "IP_LICENSING" not in added_ips:
                if len(scheme_types) > 1:
                    p = doc.add_paragraph()
                    p.add_run("Licenciamiento:").bold = True
                doc.add_paragraph(self.IP_LICENSING)
                added_ips.add("IP_LICENSING")
            
            elif "support_maintenance" in scheme_lower and "IP_SUPPORT" not in added_ips:
                if len(scheme_types) > 1:
                    p = doc.add_paragraph()
                    p.add_run("Soporte y Mantenimiento:").bold = True
                doc.add_paragraph(self.IP_SUPPORT_MAINTENANCE)
                added_ips.add("IP_SUPPORT")
            
            elif "services" in scheme_lower and "IP_SERVICES" not in added_ips:
                if len(scheme_types) > 1:
                    p = doc.add_paragraph()
                    p.add_run("Prestación de Servicios:").bold = True
                
                # Decidir si es SaaS o Servicios estándar
                if payment_frequency == "mensual":
                    doc.add_paragraph(self.IP_SAAS)
                else:
                    doc.add_paragraph(self.IP_SERVICES)
                added_ips.add("IP_SERVICES")

        doc.add_heading("5.2. Confidencialidad", level=2)
        doc.add_paragraph(self.CONFIDENTIALITY_TEXT)

        doc.add_heading("5.3. Transparencia y Ética Empresarial", level=2)
        doc.add_paragraph(self.ETHICS_TEXT)

        # --- PIE DE PÁGINA (Numeración) ---
        footer = section.footer
        p_footer = footer.paragraphs[0]
        self._add_page_number(p_footer)

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

    def convert_docx_to_pdf(self, docx_path: str, pdf_path: str) -> str:
        """
        Convierte un archivo .docx a PDF.
        En Windows usa docx2pdf (requiere Word).
        En otros sistemas intenta usar LibreOffice.

        Args:
            docx_path: Ruta al archivo .docx
            pdf_path: Ruta donde se guardará el PDF

        Returns:
            Ruta del PDF generado.
        """
        import os
        import platform

        docx_file = Path(docx_path)
        if not docx_file.exists():
            raise DocumentGeneratorError(f"El archivo no existe: {docx_path}")

        try:
            if platform.system() == "Windows":
                from docx2pdf import convert
                # docx2pdf puede fallar si no hay Word instalado, pero es lo estándar en Windows
                convert(docx_path, pdf_path)
            else:
                import subprocess
                pdf_dir = Path(pdf_path).parent
                pdf_dir.mkdir(parents=True, exist_ok=True)

                result = subprocess.run(
                    [
                        "libreoffice",
                        "--headless",
                        "--convert-to", "pdf",
                        "--outdir", str(pdf_dir),
                        str(docx_path)
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode != 0:
                    raise DocumentGeneratorError(
                        f"LibreOffice error: {result.stderr}"
                    )

                # LibreOffice genera el PDF con el mismo nombre pero extensión .pdf
                generated_pdf = docx_file.with_suffix(".pdf")

                # Si el nombre del PDF es diferente, renombrarlo
                import shutil
                if generated_pdf.exists() and str(generated_pdf) != str(pdf_path):
                    shutil.move(str(generated_pdf), str(pdf_path))

            if not Path(pdf_path).exists():
                raise DocumentGeneratorError(
                    f"El PDF no fue generado correctamente"
                )

            return str(pdf_path)

        except Exception as e:
            raise DocumentGeneratorError(f"Error al convertir DOCX a PDF: {str(e)}")
