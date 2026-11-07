"""
Enterprise ATS-friendly PDF Generator using ReportLab Platypus.
"""

import io
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas:
    """Canvas callback to render page numbers dynamically."""
    pass


class ResumePDFGenerator:
    """Generates clean, ATS-compliant, print-ready PDF resumes."""

    PRIMARY_COLOR = colors.HexColor("#1e3a8a")       # Deep Professional Navy
    TEXT_COLOR = colors.HexColor("#1e293b")          # Slate 800
    MUTED_COLOR = colors.HexColor("#64748b")         # Slate 500
    BORDER_COLOR = colors.HexColor("#cbd5e1")        # Slate 300

    def __init__(self, resume):
        self.resume = resume
        self.buffer = io.BytesIO()

    def _setup_styles(self):
        styles = getSampleStyleSheet()

        name_style = ParagraphStyle(
            'ResumeName',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=self.PRIMARY_COLOR,
            alignment=TA_CENTER,
            spaceAfter=3,
        )

        contact_style = ParagraphStyle(
            'ResumeContact',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=self.MUTED_COLOR,
            alignment=TA_CENTER,
            spaceAfter=8,
        )

        section_heading = ParagraphStyle(
            'ResumeSectionHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=13,
            textColor=self.PRIMARY_COLOR,
            textTransform='uppercase',
            spaceBefore=8,
            spaceAfter=2,
            keepWithNext=True,
        )

        body_style = ParagraphStyle(
            'ResumeBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12.5,
            textColor=self.TEXT_COLOR,
            alignment=TA_LEFT,
            spaceAfter=4,
        )

        body_bold = ParagraphStyle(
            'ResumeBodyBold',
            parent=body_style,
            fontName='Helvetica-Bold',
        )

        body_right = ParagraphStyle(
            'ResumeBodyRight',
            parent=body_style,
            fontName='Helvetica',
            textColor=self.MUTED_COLOR,
            alignment=TA_RIGHT,
        )

        bullet_style = ParagraphStyle(
            'ResumeBullet',
            parent=body_style,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=2,
        )

        return {
            'name': name_style,
            'contact': contact_style,
            'heading': section_heading,
            'body': body_style,
            'body_bold': body_bold,
            'body_right': body_right,
            'bullet': bullet_style,
        }

    def generate(self) -> bytes:
        """Builds and returns raw PDF byte stream."""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            leftMargin=36,       # 0.5 inch margins
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = self._setup_styles()
        story = []

        # 1. Header: Name & Contact Info
        name = self.resume.full_name or self.resume.profile.user.full_name
        story.append(Paragraph(name, styles['name']))

        # Build contact string
        contact_parts = []
        if self.resume.email:
            contact_parts.append(self.resume.email)
        if self.resume.phone:
            contact_parts.append(self.resume.phone)
        if self.resume.location:
            contact_parts.append(self.resume.location)
        if self.resume.linkedin_url:
            contact_parts.append("LinkedIn")
        if self.resume.github_url:
            contact_parts.append("GitHub")
        if self.resume.portfolio_url:
            contact_parts.append("Portfolio")

        contact_line = " &bull; ".join(contact_parts)
        if contact_line:
            story.append(Paragraph(contact_line, styles['contact']))

        story.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY_COLOR, spaceAfter=6))

        # 2. Professional Summary
        if self.resume.professional_summary:
            story.append(Paragraph("Professional Summary", styles['heading']))
            story.append(HRFlowable(width="100%", thickness=0.5, color=self.BORDER_COLOR, spaceAfter=4))
            story.append(Paragraph(self.resume.professional_summary.replace('\n', '<br/>'), styles['body']))
            story.append(Spacer(1, 4))

        # 3. Technical & Professional Skills
        skills = self.resume.skills_list
        if skills:
            story.append(Paragraph("Core Competencies & Skills", styles['heading']))
            story.append(HRFlowable(width="100%", thickness=0.5, color=self.BORDER_COLOR, spaceAfter=4))
            formatted_skills = " &bull; ".join(skills)
            story.append(Paragraph(formatted_skills, styles['body']))
            story.append(Spacer(1, 4))

        # 4. Work & Internship Experience
        experiences = self.resume.experiences.all()
        if experiences.exists():
            story.append(Paragraph("Professional Experience", styles['heading']))
            story.append(HRFlowable(width="100%", thickness=0.5, color=self.BORDER_COLOR, spaceAfter=4))

            for exp in experiences:
                left_text = f"<b>{exp.position}</b> &mdash; <i>{exp.company}</i>"
                if exp.location:
                    left_text += f" <font color='#64748b'>({exp.location})</font>"

                date_text = f"{exp.start_date} &ndash; {exp.end_date or 'Present'}"

                table_data = [[
                    Paragraph(left_text, styles['body']),
                    Paragraph(date_text, styles['body_right'])
                ]]
                t = Table(table_data, colWidths=[400, 140])
                t.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(t)

                if exp.description:
                    for line in exp.description.splitlines():
                        clean_line = line.strip('•- \t')
                        if clean_line:
                            story.append(Paragraph(f"&bull; {clean_line}", styles['bullet']))
                story.append(Spacer(1, 4))

        # 5. Notable Projects
        projects = self.resume.projects.all()
        if projects.exists():
            story.append(Paragraph("Key Projects", styles['heading']))
            story.append(HRFlowable(width="100%", thickness=0.5, color=self.BORDER_COLOR, spaceAfter=4))

            for proj in projects:
                left_text = f"<b>{proj.title}</b>"
                if proj.tech_stack:
                    left_text += f" <font color='#64748b'>| {proj.tech_stack}</font>"

                link_text = ""
                if proj.github_link or proj.live_link:
                    link_text = "Project Link"

                table_data = [[
                    Paragraph(left_text, styles['body']),
                    Paragraph(link_text, styles['body_right'])
                ]]
                t = Table(table_data, colWidths=[400, 140])
                t.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(t)

                if proj.description:
                    for line in proj.description.splitlines():
                        clean_line = line.strip('•- \t')
                        if clean_line:
                            story.append(Paragraph(f"&bull; {clean_line}", styles['bullet']))
                story.append(Spacer(1, 4))

        # 6. Education
        educations = self.resume.educations.all()
        if educations.exists():
            story.append(Paragraph("Education", styles['heading']))
            story.append(HRFlowable(width="100%", thickness=0.5, color=self.BORDER_COLOR, spaceAfter=4))

            for edu in educations:
                left_text = f"<b>{edu.degree} in {edu.field_of_study}</b> &mdash; {edu.institution}"
                if edu.grade:
                    left_text += f" <font color='#64748b'>(Grade: {edu.grade})</font>"

                date_text = f"{edu.start_date} &ndash; {edu.end_date or 'Present'}"

                table_data = [[
                    Paragraph(left_text, styles['body']),
                    Paragraph(date_text, styles['body_right'])
                ]]
                t = Table(table_data, colWidths=[400, 140])
                t.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(t)
                story.append(Spacer(1, 3))

        # Build document
        doc.build(story)
        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()
        return pdf_bytes
