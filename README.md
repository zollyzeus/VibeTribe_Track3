# AI-Powered Candidate Ranking & Team Composition System

**Version**: 1.0.0 | **Status**: Production Ready ✅

An intelligent system for ranking 50,000+ candidate profiles and automatically composing high-performing teams based on skill requirements and synergy optimization.

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Run the System
```bash
python3 examples/quick_start.py
```

### View Results
- **JSON**: `outputs/team_hiring_report_20260701_113828.json`
- **CSV**: `outputs/*_ranked_profiles.csv` (per-role rankings)
- **XLSX**: `outputs/ranked_profiles_consolidated.xlsx` (all roles)

## ✨ Features

- ✅ **Semantic Skill Matching**: NLP-based intelligent skill evaluation
- ✅ **50 Profiles Per Role**: Comprehensive ranked candidate lists
- ✅ **Team Optimization**: Generates 10 team compositions with synergy scoring
- ✅ **Multiple Formats**: JSON, CSV, XLSX outputs
- ✅ **50K+ Candidates**: Processes large-scale datasets efficiently (~16 minutes)
- ✅ **Customizable**: Easy JSON configuration for any roles
- ✅ **Production Ready**: Tested and validated

## 📊 System Architecture

Six-layer component system:

```
1. SkillMatrixManager       → Skill requirements management
2. CandidateFeatureExtractor → Feature extraction from profiles
3. RoleBasedRanker          → Semantic ranking per role
4. TeamCompositionOptimizer → Generates team options
5. TeamSynergyScorer        → Evaluates team compatibility
6. ReportGenerator          → Creates outputs (JSON/CSV/XLSX)
```

## 🎯 Scoring Formula

```
Total_Score = (0.40 × SkillMatch) + (0.25 × Experience) + 
              (0.15 × Education) + (0.20 × EngagementSignals)
```

## 📁 Project Structure

```
team-hiring-ai/
├── src/                           # Core source code
│   ├── team_hiring.py            # Main system (6 classes)
│   ├── team_hiring_prototype.py   # Pipeline orchestrator
│   └── export_rankings.py         # Output generation
├── config/
│   └── team_requirements_sample.json   # Role configuration
├── docs/
│   ├── README.md                 # This file
│   ├── ARCHITECTURE.md           # Detailed design
│   └── GETTING_STARTED.md        # Setup guide
├── examples/
│   └── quick_start.py            # 6 example functions
├── outputs/                       # Sample results
│   ├── team_hiring_report_*.json  # Complete results
│   ├── *_ranked_profiles.csv      # Per-role rankings
│   └── ranked_profiles_consolidated.xlsx
├── requirements.txt              # Dependencies
└── LICENSE                       # MIT License
```

## 📈 Performance

Processing 50,000 candidate profiles:

| Stage | Time | Details |
|-------|------|---------|
| Setup | 2 min | Config loading, model initialization |
| Ranking | 11 min | Semantic matching for 5 roles |
| Optimization | 30 sec | Generate 10 team compositions |
| Export | 2 min | Create JSON, CSV, XLSX |
| **Total** | **~16 min** | Complete pipeline |

## 🔧 Dependencies

- pandas ≥ 2.0.0
- numpy ≥ 1.24.0
- sentence-transformers ≥ 2.2.0
- jsonlines ≥ 4.0.0
- openpyxl ≥ 3.10.0

## 📖 Documentation

- **[GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Installation & usage guide
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical details
- **[quick_start.py](examples/quick_start.py)** - Code examples

## 💡 Use Cases

1. **Talent Acquisition**: Rank candidates for hiring
2. **Team Building**: Compose high-performing teams
3. **HR Analytics**: Analyze candidate pools
4. **Succession Planning**: Identify team replacements
5. **Skill Matching**: Match candidates to open roles

## 🎓 API Reference

### Basic Usage

```python
from src.team_hiring_prototype import TeamHiringPrototype

system = TeamHiringPrototype()
system.load_team_requirements('config/team_requirements_sample.json')
results = system.run_full_pipeline(num_teams=10)
```

### Output Structure

```json
{
  "per_role_analysis": {
    "DATA_ENGINEER_LEAD": {
      "all_ranked_candidates": [
        {
          "rank": 1,
          "candidate_id": "CAND_0001",
          "score": 0.85,
          "skill_coverage": 4
        }
      ]
    }
  },
  "team_compositions": [
    {
      "synergy_score": 1.45,
      "members": [...]
    }
  ]
}
```

## 🛠️ Customization

Edit `config/team_requirements_sample.json`:

```json
{
  "YOUR_ROLE": {
    "mandatory_skills": ["Skill1", "Skill2"],
    "important_skills": ["Skill3", "Skill4"],
    "flexible_skills": ["Skill5"],
    "experience_range": [3, 7],
    "education_required": "Bachelor's",
    "max_candidates": 50
  }
}
```

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Additional scoring algorithms
- Real-time processing
- Database integration
- REST API endpoint
- Advanced analytics

## 📄 License

MIT License - See [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- Developed for VibeTribe Ideathon Track 3
- Uses sentence-transformers for semantic analysis
- Tested on India Runs Challenge dataset

---

**Status**: ✅ Production Ready | **Version**: 1.0.0 | **Last Updated**: 2026-07-01
