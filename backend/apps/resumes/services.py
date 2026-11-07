"""
Service layer for Resume creation, AI polishing, and PDF generation.
"""

from apps.accounts.models import UserProfile
from apps.ai_services.client import GeminiService
from .models import Resume, ResumeEducation, ResumeExperience, ResumeProject
from .pdf_generator import ResumePDFGenerator


class ResumeService:
    """Orchestrates CV initialization, AI-assisted content improvement, and PDF compilation."""

    @staticmethod
    def create_from_profile(profile: UserProfile, title: str = "My Professional CV") -> Resume:
        """Initializes a new resume pre-populated with user's verified profile data."""
        user = profile.user
        location = f"{profile.city}, {profile.country}".strip(", ") or "Dhaka, Bangladesh"

        skills_joined = ", ".join([s.skill_name for s in profile.skills.all()])

        resume = Resume.objects.create(
            profile=profile,
            title=title,
            target_role=profile.target_career or "",
            full_name=user.full_name,
            email=user.email,
            phone=profile.phone or "",
            location=location,
            linkedin_url=profile.linkedin_url or "",
            github_url=profile.github_url or "",
            portfolio_url=profile.portfolio_url or "",
            professional_summary=profile.summary or "",
            skills_raw=skills_joined,
            template_style='modern_clean',
        )

        # Clone education records
        for idx, edu in enumerate(profile.educations.all()):
            start = edu.start_date.strftime('%Y') if edu.start_date else ''
            end = 'Present' if edu.is_current else (edu.end_date.strftime('%Y') if edu.end_date else '')
            ResumeEducation.objects.create(
                resume=resume,
                institution=edu.institution,
                degree=edu.degree,
                field_of_study=edu.field_of_study,
                start_date=start,
                end_date=end,
                grade=edu.grade or '',
                order=idx,
            )

        # Clone experience records
        for idx, exp in enumerate(profile.experiences.all()):
            start = exp.start_date.strftime('%b %Y') if exp.start_date else ''
            end = 'Present' if exp.is_current else (exp.end_date.strftime('%b %Y') if exp.end_date else '')
            ResumeExperience.objects.create(
                resume=resume,
                company=exp.company,
                position=exp.position,
                location=exp.location or '',
                start_date=start,
                end_date=end,
                description=exp.description or '',
                order=idx,
            )

        return resume

    @staticmethod
    def generate_ai_summary(resume: Resume, target_role: str = None, ai_service: GeminiService = None) -> str:
        """Invokes Gemini to generate an impactful summary based strictly on user's real background."""
        service = ai_service or GeminiService()
        profile_data = {
            'headline': resume.target_role or resume.full_name,
            'summary': resume.professional_summary,
            'skills': [{'skill_name': s} for s in resume.skills_list],
            'educations': [
                {'institution': e.institution, 'degree': e.degree, 'field_of_study': e.field_of_study}
                for e in resume.educations.all()
            ],
            'experiences': [
                {'position': x.position, 'company': x.company, 'description': x.description}
                for x in resume.experiences.all()
            ],
        }
        res = service.generate_professional_summary(profile_data, target_role=target_role or resume.target_role)
        return res.professional_summary

    @staticmethod
    def enhance_bullet_point(draft_text: str, context: str = None, ai_service: GeminiService = None) -> dict:
        """Invokes Gemini to improve grammar and action verbs while keeping factual meaning intact."""
        service = ai_service or GeminiService()
        res = service.enhance_bullet_point(draft_text, context=context)
        return {
            'enhanced_text': res.enhanced_text,
            'improvements_made': res.improvements_made,
        }

    @staticmethod
    def generate_pdf(resume: Resume) -> bytes:
        """Returns ReportLab PDF byte buffer for the resume."""
        generator = ResumePDFGenerator(resume)
        return generator.generate()
