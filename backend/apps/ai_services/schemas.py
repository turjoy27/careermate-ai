"""
Pydantic schemas for structured Gemini AI responses.
"""

from typing import List
from pydantic import BaseModel, Field


class CareerRecommendationItem(BaseModel):
    """Structured representation of a single recommended career path."""
    title: str = Field(description="Title of the career role (e.g. Django Backend Engineer, Data Analyst)")
    match_score: int = Field(description="Calculated suitability percentage from 0 to 100 based on user skills & background", ge=0, le=100)
    suitability_reason: str = Field(description="Detailed rationale explaining why this role fits the candidate's academic coursework and skills")
    market_outlook_bd: str = Field(description="Realistic industry demand and outlook for this role in Bangladesh")
    required_skills: List[str] = Field(description="Key competencies and technologies required by the market for this role")
    matched_skills: List[str] = Field(description="Skills the user currently has that match this role")
    missing_skills: List[str] = Field(description="Crucial skills the user lacks and needs to acquire")
    growth_potential: str = Field(description="Career progression outlook (e.g. High, Moderate, Emerging)")
    recommended_next_steps: List[str] = Field(description="Actionable 2-4 immediate steps to improve readiness for this role")


class CareerRecommendationResponse(BaseModel):
    """Envelope containing multiple career suggestions and overall assessment."""
    target_analysis: str = Field(description="Executive analysis of the candidate's background and alignment with current job market")
    readiness_level: str = Field(description="Assessment of current readiness (e.g. Entry-Ready, Needs Foundational Upskilling, Specialized Transition)")
    recommendations: List[CareerRecommendationItem] = Field(description="Top 3 to 5 recommended career paths", min_length=1)


class SummaryEnhanceResponse(BaseModel):
    """Structured response for AI-generated professional summary."""
    professional_summary: str = Field(
        description="A concise 3-4 sentence professional summary highlighting real background, core skills, and aspirations without fabricating experience."
    )
    suggested_highlights: List[str] = Field(
        default_factory=list,
        description="2-3 key strengths or themes emphasized in the summary."
    )


class BulletPointEnhanceResponse(BaseModel):
    """Structured response for polished project or work experience bullet points."""
    enhanced_text: str = Field(
        description="Grammatically polished and action-driven version of the user's draft, preserving factual truth without inventing claims."
    )
    improvements_made: List[str] = Field(
        default_factory=list,
        description="Brief explanations of edits (e.g., stronger action verb, improved conciseness, grammar correction)."
    )


class GeneratedInterviewQuestion(BaseModel):
    """Single interview question generated for a mock session."""
    question_text: str = Field(description="The interview question posed to the candidate.")
    category: str = Field(description="Question type: e.g. Technical, Behavioral, Problem Solving, System Architecture")
    intent_explanation: str = Field(description="What the hiring manager or tech lead is assessing with this question.")
    sample_approach: str = Field(description="Tips on structure (e.g. STAR method for HR, trade-off explanation for technical).")


class InterviewQuestionsResponse(BaseModel):
    """Response containing a set of interview questions for a mock session."""
    role_title: str = Field(description="Target job title the questions are calibrated for.")
    difficulty_level: str = Field(description="Target difficulty level (Junior, Mid, Senior).")
    questions: List[GeneratedInterviewQuestion] = Field(description="List of questions.", min_length=1)


class AnswerEvaluationResponse(BaseModel):
    """Structured evaluation of a candidate's interview response."""
    score: int = Field(description="Score out of 10 for the response (1-10).", ge=1, le=10)
    strengths: List[str] = Field(description="2-3 specific elements the candidate communicated well.")
    areas_for_improvement: List[str] = Field(description="Concrete suggestions to improve clarity, depth, or structure.")
    feedback_summary: str = Field(description="Constructive overall feedback summary.")
    ideal_answer_points: List[str] = Field(description="Key concepts or points that a top-tier candidate would mention.")


# ==============================================================================
# Learning Roadmap Schemas
# ==============================================================================

class RoadmapResourceItem(BaseModel):
    """Learning resource recommendation for a stage."""
    title: str = Field(description="Resource name, documentation guide, or course title.")
    resource_type: str = Field(description="documentation, course, video, project, or article.")
    url: str = Field(default="", description="URL if known or search keyword link.")
    is_free: bool = Field(default=True, description="Whether this resource is free.")


class RoadmapMilestoneItem(BaseModel):
    """Specific measurable achievement milestone in a learning stage."""
    title: str = Field(description="Milestone or topic to master.")
    skills_covered: List[str] = Field(description="Specific concepts or tools learned.")
    practical_task: str = Field(description="Hands-on mini-project or exercise to build.")


class RoadmapStageItem(BaseModel):
    """A progressive stage in the learning curriculum (Beginner, Intermediate, Advanced)."""
    stage_level: str = Field(description="beginner, intermediate, or advanced.")
    title: str = Field(description="Stage heading, e.g., 'Foundations & Tooling'.")
    duration_weeks: str = Field(description="Estimated duration, e.g., '4 Weeks'.")
    description: str = Field(description="Core objectives and focus areas of this stage.")
    milestones: List[RoadmapMilestoneItem] = Field(description="Actionable milestones to accomplish.", min_length=1)
    recommended_resources: List[RoadmapResourceItem] = Field(default_factory=list, description="Recommended learning resources.")


class LearningRoadmapResponse(BaseModel):
    """Complete personalized learning roadmap from beginner to job-ready advanced."""
    target_role: str = Field(description="Target career role.")
    estimated_total_duration: str = Field(description="Total estimated time, e.g. '16 Weeks (10 hrs/week)'.")
    skill_gap_summary: str = Field(description="Assessment of current skills vs target role requirements.")
    stages: List[RoadmapStageItem] = Field(description="3 progressive stages: Beginner, Intermediate, and Advanced.", min_length=3)



