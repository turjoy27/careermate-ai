"""
Transparent, algorithmic profile-to-job matching engine.
No LLM hallucinations: scores are deterministically computed based on user skills and job requirements.
"""

import re
from apps.accounts.models import UserProfile
from .models import JobListing


def normalize_skill(skill: str) -> str:
    """Normalizes skill text for fuzzy string matching."""
    s = skill.lower().strip()
    s = re.sub(r'[\s\-_]+', ' ', s)
    # Common tech aliases
    aliases = {
        'react.js': 'react',
        'reactjs': 'react',
        'vue.js': 'vue',
        'vuejs': 'vue',
        'node.js': 'node',
        'nodejs': 'node',
        'rest api': 'rest apis',
        'restful api': 'rest apis',
        'restful apis': 'rest apis',
        'postgresql': 'postgres',
        'docker container': 'docker',
        'k8s': 'kubernetes',
    }
    return aliases.get(s, s)


class JobMatchEngine:
    """Calculates deterministic matching metrics between a candidate profile and a job listing."""

    @classmethod
    def evaluate_fit(cls, profile: UserProfile, job: JobListing) -> dict:
        """
        Computes match score and categorical breakdowns:
        - Required skills weight: 80%
        - Preferred skills bonus: 15%
        - Target role alignment: 5%
        """
        # User skills set
        user_skills_raw = [s.skill_name for s in profile.skills.all()]
        user_skills_map = {normalize_skill(s): s for s in user_skills_raw}
        user_norm_set = set(user_skills_map.keys())

        # Job required skills
        req_skills_raw = job.required_skills_list
        req_norm_map = {normalize_skill(s): s for s in req_skills_raw}
        req_norm_set = set(req_norm_map.keys())

        # Job preferred skills
        pref_skills_raw = job.preferred_skills_list
        pref_norm_map = {normalize_skill(s): s for s in pref_skills_raw}
        pref_norm_set = set(pref_norm_map.keys())

        # Compute intersections and differences
        matched_req_norm = user_norm_set.intersection(req_norm_set)
        missing_req_norm = req_norm_set.difference(user_norm_set)

        matched_pref_norm = user_norm_set.intersection(pref_norm_set)
        missing_pref_norm = pref_norm_set.difference(user_norm_set)

        # Convert back to readable display names
        matched_required = [req_norm_map[k] for k in matched_req_norm]
        missing_required = [req_norm_map[k] for k in missing_req_norm]

        matched_preferred = [pref_norm_map[k] for k in matched_pref_norm]
        missing_preferred = [pref_norm_map[k] for k in missing_pref_norm]

        # Calculate mathematical score
        if len(req_norm_set) == 0:
            req_score = 75.0
        else:
            req_score = (len(matched_req_norm) / len(req_norm_set)) * 80.0

        if len(pref_norm_set) > 0:
            pref_score = (len(matched_pref_norm) / len(pref_norm_set)) * 15.0
        else:
            pref_score = 0.0

        # Target role keyword alignment bonus (up to 5%)
        role_bonus = 0.0
        if profile.target_career:
            target_norm = profile.target_career.lower()
            job_title_norm = job.title.lower()
            target_tokens = set(re.findall(r'\w+', target_norm))
            title_tokens = set(re.findall(r'\w+', job_title_norm))
            if target_tokens.intersection(title_tokens):
                role_bonus = 5.0

        raw_total = req_score + pref_score + role_bonus
        final_score = int(round(max(0.0, min(100.0, raw_total))))

        # Human-readable breakdown rationale
        total_req = len(req_norm_set)
        matched_count = len(matched_req_norm)
        reason = (
            f"Matched {matched_count} of {total_req} core required skills ({int(req_score)}/80 pts), "
            f"+{int(pref_score)}/15 pts from preferred tools, and +{int(role_bonus)}/5 pts for target role alignment."
        )

        return {
            'match_score': final_score,
            'matched_required': matched_required,
            'missing_required': missing_required,
            'matched_preferred': matched_preferred,
            'missing_preferred': missing_preferred,
            'breakdown_reason': reason,
        }
