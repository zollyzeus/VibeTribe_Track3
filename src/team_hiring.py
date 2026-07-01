#!/usr/bin/env python3
"""
Team-Hiring One-Shot Solution
Extends the candidate ranking system for optimal team composition optimization
"""

import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from itertools import combinations, product
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

try:
    from sentence_transformers import SentenceTransformer, util
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

try:
    from difflib import SequenceMatcher
    SIMILARITY_AVAILABLE = True
except ImportError:
    SIMILARITY_AVAILABLE = False


class SkillMatrixManager:
    """Manages skill matrices and requirements for multiple roles."""
    
    def __init__(self):
        self.skill_matrices = {}  # role_id -> skill_matrix
        self.skill_aliases = defaultdict(list)
        self.proficiency_levels = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        }
    
    def add_skill_matrix(self, role_id: str, skill_matrix: Dict) -> None:
        """Add skill matrix for a role."""
        self.skill_matrices[role_id] = self._normalize_skill_matrix(skill_matrix)
    
    def _normalize_skill_matrix(self, skill_matrix: Dict) -> Dict:
        """Normalize skill matrix to standard format."""
        normalized = {
            'mandatory_skills': {},
            'important_skills': {},
            'flexible_skills': [],
            'mandatory_combinations': [],
            'constraints': {}
        }
        
        # Process mandatory skills
        for skill in skill_matrix.get('mandatory_skills', []):
            skill_name = skill.get('name', '').lower()
            min_proficiency = self.proficiency_levels.get(
                skill.get('min_proficiency', 'beginner'), 1
            )
            normalized['mandatory_skills'][skill_name] = {
                'min_proficiency': min_proficiency,
                'weight': skill.get('weight', 1.0),
                'years_experience': skill.get('years_experience', 0)
            }
        
        # Process important skills
        for skill in skill_matrix.get('important_skills', []):
            skill_name = skill.get('name', '').lower()
            min_proficiency = self.proficiency_levels.get(
                skill.get('min_proficiency', 'beginner'), 1
            )
            normalized['important_skills'][skill_name] = {
                'min_proficiency': min_proficiency,
                'weight': skill.get('weight', 0.5)
            }
        
        # Process flexible skills
        for skill in skill_matrix.get('flexible_skills', []):
            normalized['flexible_skills'].append(skill.lower())
        
        # Process mandatory combinations
        normalized['mandatory_combinations'] = [
            [s.lower() for s in combo]
            for combo in skill_matrix.get('mandatory_combinations', [])
        ]
        
        # Store constraints
        normalized['constraints'] = skill_matrix.get('constraints', {})
        
        return normalized
    
    def add_skill_aliases(self, skill_map: Dict[str, List[str]]) -> None:
        """Add skill aliases (e.g., 'ML' -> ['machine learning', 'ml'])."""
        for primary, aliases in skill_map.items():
            self.skill_aliases[primary.lower()] = [a.lower() for a in aliases]


class CandidateFeatureExtractor:
    """Extracts and normalizes candidate features."""
    
    def __init__(self, use_embeddings: bool = True):
        self.use_embeddings = use_embeddings and EMBEDDINGS_AVAILABLE
        self.embedding_model = None
        if self.use_embeddings:
            print("📦 Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def extract_all_skills(self, candidate: Dict) -> Dict[str, float]:
        """Extract skills from candidate profile with proficiency scores."""
        skills = {}
        
        # Direct skills from profile
        for skill in candidate.get('skills', []):
            skill_name = skill.get('name', '').lower()
            proficiency = self._proficiency_to_score(skill.get('proficiency', 'beginner'))
            
            # Consider endorsements and duration as proficiency boosts
            endorsements = skill.get('endorsements', 0)
            duration_months = skill.get('duration_months', 0)
            
            # Adjust proficiency based on signals
            adjusted_proficiency = min(4, proficiency + (endorsements / 50) + (duration_months / 120))
            skills[skill_name] = adjusted_proficiency
        
        return skills
    
    def _proficiency_to_score(self, proficiency: str) -> float:
        """Convert proficiency string to numeric score (0-4)."""
        mapping = {
            'beginner': 1.0,
            'intermediate': 2.0,
            'advanced': 3.0,
            'expert': 4.0
        }
        return mapping.get(proficiency.lower(), 1.0)
    
    def extract_experience_years(self, candidate: Dict) -> float:
        """Extract total years of experience."""
        return candidate.get('profile', {}).get('years_of_experience', 0)
    
    def extract_domain_expertise(self, candidate: Dict) -> Dict[str, int]:
        """Extract domain expertise from career history."""
        domains = defaultdict(int)
        for job in candidate.get('career_history', []):
            industry = job.get('industry', '').lower()
            if industry:
                domains[industry] += job.get('duration_months', 0)
        return dict(domains)
    
    def extract_education_level(self, candidate: Dict) -> str:
        """Extract highest education level."""
        education = candidate.get('education', [])
        if not education:
            return 'unknown'
        
        degree_levels = {
            'phd': 5,
            'masters': 4,
            'mba': 4,
            'bachelor': 3,
            'b.e.': 3,
            'b.tech': 3,
            'diploma': 2,
            'certificate': 1
        }
        
        highest = ('unknown', 0)
        for edu in education:
            degree = edu.get('degree', '').lower()
            level = degree_levels.get(degree, 0)
            if level > highest[1]:
                highest = (degree, level)
        
        return highest[0]
    
    def compute_embedding(self, candidate_text: str) -> Optional[np.ndarray]:
        """Compute embedding for candidate profile."""
        if not self.use_embeddings:
            return None
        
        try:
            embedding = self.embedding_model.encode(candidate_text, convert_to_tensor=False)
            return embedding
        except Exception as e:
            print(f"⚠️  Embedding error: {e}")
            return None
    
    def extract_all_features(self, candidate: Dict) -> Dict[str, Any]:
        """Extract all features for a candidate."""
        profile_text = f"{candidate.get('profile', {}).get('headline', '')} " \
                      f"{candidate.get('profile', {}).get('summary', '')}"
        
        return {
            'candidate_id': candidate.get('candidate_id'),
            'skills': self.extract_all_skills(candidate),
            'experience_years': self.extract_experience_years(candidate),
            'domain_expertise': self.extract_domain_expertise(candidate),
            'education_level': self.extract_education_level(candidate),
            'embedding': self.compute_embedding(profile_text),
            'engagement_score': self._calculate_engagement_score(candidate),
            'raw_candidate': candidate
        }
    
    def _calculate_engagement_score(self, candidate: Dict) -> float:
        """Calculate engagement score from signals."""
        score = 0.0
        signals = candidate.get('redrob_signals', {})
        
        if signals.get('open_to_work_flag'):
            score += 0.15
        
        if signals.get('verified_email') and signals.get('verified_phone'):
            score += 0.10
        
        if signals.get('github_activity_score', 0) > 5:
            score += 0.10
        
        response_rate = signals.get('recruiter_response_rate', 0)
        if response_rate > 0.5:
            score += 0.10
        
        return min(1.0, score)


class RoleBasedRanker:
    """Ranks candidates for individual roles."""
    
    def __init__(self, skill_matrix_manager: SkillMatrixManager,
                 feature_extractor: CandidateFeatureExtractor):
        self.skill_manager = skill_matrix_manager
        self.feature_extractor = feature_extractor
    
    def score_candidate_for_role(self, candidate_features: Dict, role_id: str) -> Dict:
        """Score a single candidate for a role."""
        skill_matrix = self.skill_manager.skill_matrices.get(role_id)
        if not skill_matrix:
            raise ValueError(f"Unknown role: {role_id}")
        
        # Calculate component scores
        skill_score = self._score_skills(
            candidate_features['skills'],
            skill_matrix,
            role_id
        )
        
        experience_score = self._score_experience(
            candidate_features['experience_years'],
            skill_matrix
        )
        
        education_score = self._score_education(
            candidate_features['education_level'],
            skill_matrix
        )
        
        engagement_score = candidate_features.get('engagement_score', 0)
        
        # Weighted aggregation
        total_score = (
            0.40 * skill_score +
            0.25 * experience_score +
            0.15 * education_score +
            0.10 * engagement_score +
            0.10 * 0.5  # placeholder for certifications
        )
        
        return {
            'candidate_id': candidate_features['candidate_id'],
            'total_score': total_score,
            'skill_score': skill_score,
            'experience_score': experience_score,
            'education_score': education_score,
            'engagement_score': engagement_score,
            'skill_match_details': self._get_skill_match_details(
                candidate_features['skills'],
                skill_matrix
            )
        }
    
    def _score_skills(self, candidate_skills: Dict, skill_matrix: Dict, role_id: str) -> float:
        """Score candidate skills against required skills."""
        mandatory = skill_matrix.get('mandatory_skills', {})
        important = skill_matrix.get('important_skills', {})
        
        mandatory_score = 0
        if mandatory:
            matched = 0
            for req_skill, req_info in mandatory.items():
                if self._skill_matches(req_skill, candidate_skills):
                    matched += 1
            mandatory_score = (matched / len(mandatory)) if mandatory else 0
        
        important_score = 0
        if important:
            matched = 0
            for req_skill in important.keys():
                if self._skill_matches(req_skill, candidate_skills):
                    matched += 1
            important_score = (matched / len(important)) if important else 0
        
        return 0.70 * mandatory_score + 0.30 * important_score
    
    def _skill_matches(self, required_skill: str, candidate_skills: Dict) -> bool:
        """Check if candidate has required skill."""
        required_skill_lower = required_skill.lower()
        
        # Direct match
        if required_skill_lower in candidate_skills:
            return candidate_skills[required_skill_lower] >= 1.0
        
        # Fuzzy match
        for candidate_skill in candidate_skills.keys():
            if self._fuzzy_match(required_skill_lower, candidate_skill):
                return candidate_skills[candidate_skill] >= 1.0
        
        return False
    
    def _fuzzy_match(self, skill1: str, skill2: str) -> bool:
        """Fuzzy match two skills."""
        if SIMILARITY_AVAILABLE:
            similarity = SequenceMatcher(None, skill1, skill2).ratio()
            return similarity > 0.7
        return False
    
    def _score_experience(self, years: float, skill_matrix: Dict) -> float:
        """Score based on years of experience."""
        constraints = skill_matrix.get('constraints', {})
        min_years = constraints.get('min_experience_years', 0)
        max_years = constraints.get('max_experience_years', 50)
        
        if min_years <= years <= max_years:
            return 1.0
        elif min_years - 2 <= years <= max_years + 2:
            return 0.8
        else:
            return 0.5
    
    def _score_education(self, education_level: str, skill_matrix: Dict) -> float:
        """Score based on education level."""
        required_edu = skill_matrix.get('constraints', {}).get('required_education', 'any')
        
        edu_hierarchy = {
            'phd': 5,
            'masters': 4,
            'mba': 4,
            'bachelor': 3,
            'b.e.': 3,
            'b.tech': 3,
            'diploma': 2,
            'certificate': 1,
            'unknown': 0
        }
        
        if required_edu.lower() == 'any':
            return 0.8
        
        required_level = edu_hierarchy.get(required_edu.lower(), 3)
        actual_level = edu_hierarchy.get(education_level.lower(), 0)
        
        if actual_level >= required_level:
            return 1.0
        elif actual_level >= required_level - 1:
            return 0.8
        else:
            return 0.5
    
    def _get_skill_match_details(self, candidate_skills: Dict, skill_matrix: Dict) -> Dict:
        """Get detailed skill match information."""
        mandatory = skill_matrix.get('mandatory_skills', {})
        important = skill_matrix.get('important_skills', {})
        
        details = {
            'matched_mandatory': [],
            'missing_mandatory': [],
            'matched_important': [],
            'missing_important': []
        }
        
        for req_skill in mandatory.keys():
            if self._skill_matches(req_skill, candidate_skills):
                details['matched_mandatory'].append(req_skill)
            else:
                details['missing_mandatory'].append(req_skill)
        
        for req_skill in important.keys():
            if self._skill_matches(req_skill, candidate_skills):
                details['matched_important'].append(req_skill)
            else:
                details['missing_important'].append(req_skill)
        
        return details
    
    def rank_candidates_for_role(self, all_candidates: List[Dict], role_id: str,
                                  top_k: int = 20) -> List[Dict]:
        """Rank all candidates for a role."""
        scores = []
        for candidate_features in all_candidates:
            score = self.score_candidate_for_role(candidate_features, role_id)
            scores.append(score)
        
        # Sort by total score
        scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        return scores[:top_k]


class TeamCompositionOptimizer:
    """Optimizes team composition from candidate pools."""
    
    def __init__(self, skill_matrix_manager: SkillMatrixManager):
        self.skill_manager = skill_matrix_manager
    
    def identify_multi_role_candidates(self, role_rankings: Dict[str, List[Dict]],
                                      role_threshold: float = 0.75) -> Dict[str, List[str]]:
        """Identify candidates who can fill multiple roles."""
        candidate_roles = defaultdict(list)
        
        for role_id, rankings in role_rankings.items():
            for ranking in rankings:
                candidate_id = ranking['candidate_id']
                if ranking['total_score'] >= role_threshold:
                    candidate_roles[candidate_id].append(role_id)
        
        return {
            cid: roles for cid, roles in candidate_roles.items()
            if len(roles) > 1
        }
    
    def check_mandatory_constraints(self, team: List[Tuple[str, str]], role_id: str,
                                    features_map: Dict) -> bool:
        """Check if team satisfies mandatory constraints for a role."""
        skill_matrix = self.skill_manager.skill_matrices.get(role_id)
        if not skill_matrix:
            return False
        
        # Check mandatory skills
        mandatory = skill_matrix.get('mandatory_skills', {})
        for role, candidate_id in team:
            if role == role_id:
                features = features_map.get(candidate_id)
                if features:
                    matched = 0
                    for req_skill in mandatory.keys():
                        if req_skill.lower() in features['skills']:
                            matched += 1
                    if matched < len(mandatory):
                        return False
        
        return True
    
    def generate_team_compositions(self, role_rankings: Dict[str, List[Dict]],
                                   num_compositions: int = 10) -> List[List[Tuple[str, str]]]:
        """Generate top team compositions."""
        roles = list(role_rankings.keys())
        
        # Get top candidates per role
        top_candidates = {
            role: [r['candidate_id'] for r in role_rankings[role][:5]]
            for role in roles
        }
        
        # Generate combinations
        compositions = []
        for combo in product(*top_candidates.values()):
            # combo is (candidate_1_role1, candidate_2_role2, ..., candidate_n_rolem)
            team = list(zip(roles, combo))
            compositions.append(team)
        
        return compositions[:num_compositions * 10]  # Return more for filtering
    
    def calculate_team_synergy_score(self, team: List[Tuple[str, str]],
                                     role_rankings: Dict[str, List[Dict]],
                                     features_map: Dict) -> Dict:
        """Calculate synergy score for a team composition."""
        # Build scoring data
        individual_scores = {}
        skill_redundancy = defaultdict(int)
        all_skills = set()
        
        for role_id, candidate_id in team:
            # Find score for this candidate in this role
            rankings = role_rankings.get(role_id, [])
            for ranking in rankings:
                if ranking['candidate_id'] == candidate_id:
                    individual_scores[(role_id, candidate_id)] = ranking['total_score']
                    break
            
            # Collect skills
            features = features_map.get(candidate_id)
            if features:
                all_skills.update(features['skills'].keys())
        
        # Calculate component scores
        avg_individual_score = np.mean(list(individual_scores.values())) if individual_scores else 0
        
        # Skill redundancy (how many people per skill)
        skill_coverage = len(all_skills)
        total_potential_skills = sum(
            len(self.skill_manager.skill_matrices[r].get('mandatory_skills', {}))
            for r, _ in team
        )
        coverage_ratio = skill_coverage / max(total_potential_skills, 1)
        
        # Calculate synergy bonus
        synergy_bonus = 0
        if len(individual_scores) >= 5:  # Full team
            if avg_individual_score > 0.8:
                synergy_bonus = 0.15
            elif avg_individual_score > 0.7:
                synergy_bonus = 0.10
        
        total_score = (
            0.40 * avg_individual_score +
            0.25 * coverage_ratio +
            0.20 * synergy_bonus +
            0.15 * (len([c for r, c in team if c]) / len(team))
        )
        
        return {
            'team': team,
            'total_score': total_score,
            'avg_individual_score': avg_individual_score,
            'skill_coverage_ratio': coverage_ratio,
            'synergy_bonus': synergy_bonus,
            'individual_scores': individual_scores
        }
    
    def optimize_team_composition(self, role_rankings: Dict[str, List[Dict]],
                                 features_map: Dict,
                                 num_teams: int = 5) -> List[Dict]:
        """Optimize and return top team compositions."""
        compositions = self.generate_team_compositions(role_rankings, num_teams)
        
        scored_compositions = []
        for composition in compositions:
            score = self.calculate_team_synergy_score(composition, role_rankings, features_map)
            scored_compositions.append(score)
        
        # Sort by total score
        scored_compositions.sort(key=lambda x: x['total_score'], reverse=True)
        
        return scored_compositions[:num_teams]


class TeamHiringReportGenerator:
    """Generates comprehensive team hiring reports."""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def generate_report(self, team_compositions: List[Dict], role_rankings: Dict[str, List[Dict]],
                       skill_matrices: Dict, features_map: Dict) -> Dict:
        """Generate comprehensive team hiring report."""
        report = {
            'timestamp': self.timestamp,
            'summary': {
                'total_roles': len(role_rankings),
                'top_team_rank': 1,
                'top_team_score': team_compositions[0]['total_score'] if team_compositions else 0,
                'alternative_teams_available': len(team_compositions) - 1
            },
            'top_team': self._format_team_details(team_compositions[0], features_map,
                                                   skill_matrices),
            'alternative_teams': [
                self._format_team_details(comp, features_map, skill_matrices)
                for comp in team_compositions[1:]
            ],
            'per_role_analysis': self._generate_per_role_analysis(role_rankings, features_map),
            'skill_gap_analysis': self._generate_skill_gap_analysis(
                team_compositions[0] if team_compositions else {},
                skill_matrices,
                features_map
            )
        }
        
        return report
    
    def _format_team_details(self, composition: Dict, features_map: Dict,
                            skill_matrices: Dict) -> Dict:
        """Format detailed team composition."""
        team_data = []
        
        for role_id, candidate_id in composition.get('team', []):
            features = features_map.get(candidate_id, {})
            candidate = features.get('raw_candidate', {})
            
            team_data.append({
                'role': role_id,
                'candidate_id': candidate_id,
                'name': candidate.get('profile', {}).get('anonymized_name', 'N/A'),
                'headline': candidate.get('profile', {}).get('headline', 'N/A'),
                'years_experience': candidate.get('profile', {}).get('years_of_experience', 0),
                'top_skills': list(features.get('skills', {}).keys())[:5],
                'role_score': composition.get('individual_scores', {}).get((role_id, candidate_id), 0)
            })
        
        return {
            'team': team_data,
            'total_score': composition.get('total_score', 0),
            'avg_individual_score': composition.get('avg_individual_score', 0),
            'skill_coverage_ratio': composition.get('skill_coverage_ratio', 0),
            'synergy_bonus': composition.get('synergy_bonus', 0)
        }
    
    def _generate_per_role_analysis(self, role_rankings: Dict[str, List[Dict]],
                                    features_map: Dict) -> Dict:
        """Generate per-role analysis."""
        analysis = {}
        
        for role_id, rankings in role_rankings.items():
            # Include ALL ranked candidates (not just top 3)
            analysis[role_id] = {
                'all_ranked_candidates': [
                    {
                        'rank': i + 1,
                        'candidate_id': r['candidate_id'],
                        'score': r['total_score'],
                        'skill_coverage': len(r.get('skill_match_details', {}).get('matched_mandatory', []))
                    }
                    for i, r in enumerate(rankings)
                ],
                'top_candidates': [
                    {
                        'candidate_id': r['candidate_id'],
                        'score': r['total_score'],
                        'skill_coverage': len(r.get('skill_match_details', {}).get('matched_mandatory', []))
                    }
                    for r in rankings[:3]
                ],
                'total_candidates_ranked': len(rankings)
            }
        
        return analysis
    
    def _generate_skill_gap_analysis(self, composition: Dict, skill_matrices: Dict,
                                      features_map: Dict) -> Dict:
        """Generate skill gap analysis."""
        gaps = {}
        
        for role_id, candidate_id in composition.get('team', []):
            skill_matrix = skill_matrices.get(role_id, {})
            mandatory_skills = skill_matrix.get('mandatory_skills', {})
            features = features_map.get(candidate_id, {})
            candidate_skills = set(features.get('skills', {}).keys())
            
            missing = []
            for req_skill in mandatory_skills.keys():
                if req_skill.lower() not in candidate_skills:
                    missing.append(req_skill)
            
            gaps[role_id] = {
                'missing_mandatory_skills': missing,
                'coverage_percent': ((len(mandatory_skills) - len(missing)) / max(len(mandatory_skills), 1)) * 100
            }
        
        return gaps


# Main Execution
def main():
    """Main execution function."""
    print("🚀 Team-Hiring One-Shot Solution Initialized")
    print("Core components ready for integration with candidate ranking system")


if __name__ == "__main__":
    main()

