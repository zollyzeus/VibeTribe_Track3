#!/usr/bin/env python3
"""
Team-Hiring One-Shot Solution - Prototype Implementation
Demonstrates the end-to-end team composition optimization using the India Runs dataset
"""

import json
import jsonlines
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import sys
from datetime import datetime

# Import team hiring components
from team_hiring import (
    SkillMatrixManager,
    CandidateFeatureExtractor,
    RoleBasedRanker,
    TeamCompositionOptimizer,
    TeamHiringReportGenerator
)


class TeamHiringPrototype:
    """End-to-end prototype for team hiring solution."""
    
    def __init__(self, candidates_file: str, team_requirements_file: str):
        """Initialize the prototype."""
        self.candidates_file = candidates_file
        self.team_requirements_file = team_requirements_file
        
        # Initialize components
        self.skill_manager = SkillMatrixManager()
        self.feature_extractor = CandidateFeatureExtractor(use_embeddings=False)
        self.ranker = RoleBasedRanker(self.skill_manager, self.feature_extractor)
        self.optimizer = TeamCompositionOptimizer(self.skill_manager)
        self.report_generator = TeamHiringReportGenerator()
        
        # Data storage
        self.candidates = []
        self.candidate_features = {}
        self.team_requirements = {}
        self.role_rankings = {}
        self.team_compositions = []
        
        print("✅ Team Hiring Prototype Initialized")
    
    def load_team_requirements(self) -> None:
        """Load team requirements from configuration file."""
        print(f"\n📂 Loading team requirements from {self.team_requirements_file}...")
        
        with open(self.team_requirements_file, 'r') as f:
            self.team_requirements = json.load(f)
        
        # Set up skill matrices for each role
        for role in self.team_requirements.get('roles', []):
            role_id = role['role_id']
            self.skill_manager.add_skill_matrix(role_id, {
                'mandatory_skills': role.get('mandatory_skills', []),
                'important_skills': role.get('important_skills', []),
                'flexible_skills': role.get('flexible_skills', []),
                'mandatory_combinations': role.get('mandatory_combinations', []),
                'constraints': role.get('constraints', {})
            })
            print(f"  ✓ Loaded {role_id}: {role['role_name']}")
        
        print(f"✅ Team Requirements Loaded: {len(self.team_requirements['roles'])} roles")
    
    def load_candidates(self, max_candidates: Optional[int] = None) -> None:
        """Load and sample candidate profiles."""
        print(f"\n📂 Loading candidates from {self.candidates_file}...")
        
        with jsonlines.open(self.candidates_file) as reader:
            for i, line in enumerate(reader):
                if max_candidates and i >= max_candidates:
                    break
                self.candidates.append(line)
                
                if (i + 1) % 10000 == 0:
                    print(f"  ✓ Loaded {i + 1:,} candidates...")
        
        print(f"✅ Candidates Loaded: {len(self.candidates):,} total")
    
    def extract_candidate_features(self) -> None:
        """Extract features from all candidates."""
        print(f"\n🔍 Extracting features from {len(self.candidates):,} candidates...")
        
        for i, candidate in enumerate(self.candidates):
            features = self.feature_extractor.extract_all_features(candidate)
            self.candidate_features[candidate['candidate_id']] = features
            
            if (i + 1) % 10000 == 0:
                print(f"  ✓ Processed {i + 1:,} candidates...")
        
        print(f"✅ Features Extracted: {len(self.candidate_features):,} candidates")
    
    def rank_candidates_per_role(self) -> None:
        """Rank candidates for each role."""
        print(f"\n🏆 Ranking candidates for {len(self.team_requirements['roles'])} roles...")
        
        candidates_list = list(self.candidate_features.values())
        
        for role in self.team_requirements.get('roles', []):
            role_id = role['role_id']
            print(f"\n  Processing {role_id}: {role['role_name']}")
            
            try:
                rankings = self.ranker.rank_candidates_for_role(
                    candidates_list,
                    role_id,
                    top_k=50
                )
                self.role_rankings[role_id] = rankings
                
                # Print top 3 for this role
                for rank, candidate in enumerate(rankings[:3], 1):
                    print(f"    {rank}. {candidate['candidate_id']} "
                          f"(Score: {candidate['total_score']:.3f})")
                print(f"    ... ({len(rankings)} total shortlisted candidates)")
                
            except Exception as e:
                print(f"    ⚠️  Error ranking role {role_id}: {e}")
        
        print(f"\n✅ Ranking Complete: {len(self.role_rankings)} roles ranked (50 candidates per role)")
    
    def optimize_team_compositions(self, num_teams: int = 10) -> None:
        """Optimize team compositions."""
        print(f"\n🤝 Optimizing team compositions (target: {num_teams} teams)...")
        
        self.team_compositions = self.optimizer.optimize_team_composition(
            self.role_rankings,
            self.candidate_features,
            num_teams=num_teams
        )
        
        for rank, composition in enumerate(self.team_compositions, 1):
            print(f"\n  Team #{rank} - Score: {composition['total_score']:.3f}")
            for role_id, candidate_id in composition['team']:
                try:
                    candidate = self.candidate_features[candidate_id]['raw_candidate']
                    name = candidate['profile']['anonymized_name']
                    print(f"    • {role_id}: {name}")
                except:
                    print(f"    • {role_id}: {candidate_id}")
        
        print(f"\n✅ Team Optimization Complete: {len(self.team_compositions)} teams")
    
    def generate_final_report(self) -> Dict:
        """Generate comprehensive final report."""
        print(f"\n📊 Generating comprehensive report...")
        
        report = self.report_generator.generate_report(
            self.team_compositions,
            self.role_rankings,
            self.skill_manager.skill_matrices,
            self.candidate_features
        )
        
        # Add additional metadata
        report['team_requirements'] = self.team_requirements
        report['total_candidates_evaluated'] = len(self.candidates)
        report['generation_timestamp'] = datetime.now().isoformat()
        
        return report
    
    def save_report(self, report: Dict, output_dir: str = "outputs") -> None:
        """Save report to files."""
        print(f"\n💾 Saving reports to {output_dir}...")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save JSON report
        json_file = output_path / f"team_hiring_report_{report['timestamp']}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"  ✓ JSON report: {json_file}")
        
        # Save CSV with top team composition
        csv_file = output_path / f"top_team_{report['timestamp']}.csv"
        top_team_data = []
        
        if report['top_team']:
            for member in report['top_team']['team']:
                top_team_data.append({
                    'rank': len(top_team_data) + 1,
                    'role': member['role'],
                    'candidate_id': member['candidate_id'],
                    'name': member['name'],
                    'headline': member['headline'],
                    'years_experience': member['years_experience'],
                    'role_score': member['role_score']
                })
        
        if top_team_data:
            df = pd.DataFrame(top_team_data)
            df.to_csv(csv_file, index=False)
            print(f"  ✓ CSV report: {csv_file}")
        
        # Save markdown summary
        md_file = output_path / f"team_hiring_summary_{report['timestamp']}.md"
        with open(md_file, 'w') as f:
            self._write_markdown_report(f, report)
        print(f"  ✓ Markdown summary: {md_file}")
    
    def _write_markdown_report(self, f, report: Dict) -> None:
        """Write markdown format report."""
        f.write(f"# Team Hiring Report\n\n")
        f.write(f"**Generated**: {report['timestamp']}\n\n")
        
        f.write(f"## Summary\n\n")
        f.write(f"- **Total Roles**: {report['summary']['total_roles']}\n")
        f.write(f"- **Top Team Score**: {report['summary']['top_team_score']:.3f}\n")
        f.write(f"- **Alternative Teams**: {report['summary']['alternative_teams_available']}\n")
        f.write(f"- **Candidates Evaluated**: {report['total_candidates_evaluated']:,}\n\n")
        
        f.write(f"## Recommended Team (Primary)\n\n")
        if report['top_team']:
            f.write(f"**Team Score**: {report['top_team']['total_score']:.3f}\n\n")
            for member in report['top_team']['team']:
                f.write(f"### {member['role']}\n\n")
                f.write(f"- **Candidate**: {member['name']}\n")
                f.write(f"- **ID**: {member['candidate_id']}\n")
                f.write(f"- **Headline**: {member['headline']}\n")
                f.write(f"- **Experience**: {member['years_experience']} years\n")
                f.write(f"- **Role Score**: {member['role_score']:.3f}\n")
                f.write(f"- **Top Skills**: {', '.join(member['top_skills'][:5])}\n\n")
        
        f.write(f"## Alternative Team Compositions\n\n")
        for i, team in enumerate(report['alternative_teams'][:3], 1):
            f.write(f"### Option {i} - Score: {team['total_score']:.3f}\n\n")
            for member in team['team']:
                f.write(f"- {member['role']}: {member['name']}\n")
            f.write("\n")
        
        f.write(f"## Skill Gap Analysis\n\n")
        for role_id, gap in report['skill_gap_analysis'].items():
            f.write(f"### {role_id}\n\n")
            f.write(f"- **Coverage**: {gap['coverage_percent']:.1f}%\n")
            if gap['missing_mandatory_skills']:
                f.write(f"- **Missing Skills**: {', '.join(gap['missing_mandatory_skills'])}\n")
            f.write("\n")
    
    def run_full_pipeline(self, max_candidates: Optional[int] = 50000,
                         num_teams: int = 10) -> Dict:
        """Run the complete pipeline."""
        print("\n" + "="*80)
        print("🚀 TEAM HIRING ONE-SHOT SOLUTION - FULL PIPELINE")
        print("="*80)
        
        # Step 1: Load requirements
        self.load_team_requirements()
        
        # Step 2: Load candidates
        self.load_candidates(max_candidates=max_candidates)
        
        # Step 3: Extract features
        self.extract_candidate_features()
        
        # Step 4: Rank per role
        self.rank_candidates_per_role()
        
        # Step 5: Optimize team
        self.optimize_team_compositions(num_teams=num_teams)
        
        # Step 6: Generate report
        report = self.generate_final_report()
        
        # Step 7: Save reports
        self.save_report(report)
        
        print("\n" + "="*80)
        print("✅ PIPELINE COMPLETE")
        print("="*80 + "\n")
        
        return report


def main():
    """Main execution."""
    # Configuration
    CANDIDATES_FILE = "/home/anand/projects/candidate_ranking/data/datasets/India_runs_data_and_ai_challenge/candidates.jsonl"
    TEAM_REQUIREMENTS_FILE = "/home/anand/projects/candidate_ranking/Ideathon/team_hiring_solution/config/team_requirements_sample.json"
    OUTPUT_DIR = "/home/anand/projects/candidate_ranking/Ideathon/team_hiring_solution/results"
    
    # Verify files exist
    if not Path(CANDIDATES_FILE).exists():
        print(f"❌ Candidates file not found: {CANDIDATES_FILE}")
        return
    
    if not Path(TEAM_REQUIREMENTS_FILE).exists():
        print(f"❌ Team requirements file not found: {TEAM_REQUIREMENTS_FILE}")
        return
    
    # Run prototype
    prototype = TeamHiringPrototype(CANDIDATES_FILE, TEAM_REQUIREMENTS_FILE)
    
    # Execute with sample size (50K candidates for demonstration)
    # In production, use all 100K candidates
    report = prototype.run_full_pipeline(
        max_candidates=50000,
        num_teams=10
    )
    
    # Print key findings
    print("\n🎯 KEY FINDINGS")
    print("-" * 80)
    if report['top_team']:
        print(f"\n✅ TOP RECOMMENDED TEAM")
        print(f"   Team Score: {report['top_team']['total_score']:.3f}")
        print(f"   Team Members:")
        for member in report['top_team']['team']:
            print(f"     • {member['role']}: {member['name']} ({member['years_experience']} yrs)")
        
        print(f"\n📊 SKILL COVERAGE")
        for role_id, gap in report['skill_gap_analysis'].items():
            print(f"   {role_id}: {gap['coverage_percent']:.1f}% coverage")
    
    return report


if __name__ == "__main__":
    main()

