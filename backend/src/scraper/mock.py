"""
Synthetic job data generator for offline demos and CI.
Produces realistic-looking job postings without needing API keys.
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from src.logger import get_logger

logger = get_logger(__name__)

try:
    from faker import Faker
    _faker = Faker()
except ImportError:
    _faker = None

# Correlated salary bands: (min, max) pairs — prevents min > max
_SALARY_BANDS = [
    (80000, 130000),
    (100000, 160000),
    (120000, 200000),
    (140000, 250000),
]

ROLE_FAMILIES = {
    "Data Scientist": {
        "skills": ["Python", "machine learning", "pandas", "scikit-learn", "TensorFlow",
                   "PyTorch", "SQL", "statistics", "R", "Jupyter", "MLflow", "feature engineering",
                   "deep learning", "NLP", "computer vision", "A/B testing", "data visualization"],
        "companies": ["Netflix", "Airbnb", "Stripe", "Databricks", "Palantir", "Two Sigma"],
    },
    "Software Engineer": {
        "skills": ["Python", "Java", "Go", "Kubernetes", "Docker", "REST APIs", "microservices",
                   "PostgreSQL", "Redis", "AWS", "CI/CD", "Git", "TypeScript", "React", "gRPC",
                   "system design", "distributed systems", "unit testing"],
        "companies": ["Google", "Meta", "Amazon", "Apple", "Microsoft", "Shopify", "Notion"],
    },
    "Data Engineer": {
        "skills": ["Apache Spark", "Airflow", "dbt", "Snowflake", "BigQuery", "Python", "SQL",
                   "Kafka", "ETL", "data modeling", "Redshift", "Delta Lake", "Databricks",
                   "Terraform", "AWS Glue", "data warehouse"],
        "companies": ["Uber", "Lyft", "DoorDash", "Coinbase", "Robinhood", "Plaid"],
    },
    "ML Engineer": {
        "skills": ["Python", "TensorFlow", "PyTorch", "MLflow", "Kubernetes", "Docker",
                   "model serving", "feature stores", "ONNX", "CUDA", "distributed training",
                   "CI/CD for ML", "Ray", "Triton", "model monitoring"],
        "companies": ["OpenAI", "Anthropic", "DeepMind", "Hugging Face", "Scale AI", "Cohere"],
    },
    "Frontend Engineer": {
        "skills": ["React", "TypeScript", "CSS", "Next.js", "GraphQL", "Webpack", "Jest",
                   "accessibility", "performance optimization", "Figma", "Storybook", "Redux",
                   "web components", "PWA", "Vite"],
        "companies": ["Vercel", "Figma", "Linear", "Notion", "Loom", "Canva"],
    },
    "DevOps Engineer": {
        "skills": ["Kubernetes", "Terraform", "AWS", "GCP", "Azure", "Docker", "Helm",
                   "Prometheus", "Grafana", "CI/CD", "Ansible", "Linux", "bash scripting",
                   "security hardening", "GitOps", "Datadog"],
        "companies": ["HashiCorp", "Cloudflare", "Fastly", "Datadog", "PagerDuty"],
    },
    "Product Manager": {
        "skills": ["roadmap planning", "stakeholder management", "SQL", "A/B testing",
                   "user research", "Jira", "Confluence", "OKRs", "PRD writing",
                   "data analysis", "go-to-market strategy", "agile"],
        "companies": ["Spotify", "Slack", "Atlassian", "HubSpot", "Salesforce"],
    },
}

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
    "Boston, MA", "Chicago, IL", "Los Angeles, CA", "Remote",
    "Denver, CO", "Atlanta, GA",
]

DESCRIPTION_TEMPLATES = [
    "We are looking for a talented {title} to join our team. "
    "You will work with {skill1}, {skill2}, and {skill3}. "
    "Responsibilities include building scalable systems, collaborating with cross-functional teams, "
    "and delivering high-quality solutions. "
    "Required: 3+ years experience with {skill4} and {skill5}. "
    "Nice to have: {skill6}, {skill7}. "
    "We offer competitive compensation, equity, and great benefits.",

    "Join {company} as a {title}. "
    "Our team uses {skill1} and {skill2} to solve challenging problems at scale. "
    "You'll be responsible for {skill3}-based solutions and mentoring junior engineers. "
    "Must have: {skill4}, {skill5}, {skill6}. "
    "Experience with {skill7} is a plus. "
    "We are an equal opportunity employer.",

    "Exciting opportunity for a {title} at a fast-growing startup. "
    "Day-to-day: designing {skill1} pipelines, optimizing {skill2} workflows, "
    "and building {skill3} tooling. "
    "Stack: {skill4}, {skill5}, {skill6}. "
    "Bonus: {skill7} experience. "
    "Flexible remote policy.",
]


def generate_mock_jobs(n: int = 500, output_dir: str = "data/raw") -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "mock_jobs.jsonl"

    base_date = datetime.now() - timedelta(days=180)
    jobs = []

    for i in range(n):
        role = random.choice(list(ROLE_FAMILIES.keys()))
        family = ROLE_FAMILIES[role]
        skills = random.sample(family["skills"], min(7, len(family["skills"])))
        company = random.choice(family["companies"])
        location = random.choice(LOCATIONS)
        template = random.choice(DESCRIPTION_TEMPLATES)
        description = template.format(
            title=role, company=company,
            skill1=skills[0], skill2=skills[1], skill3=skills[2],
            skill4=skills[3], skill5=skills[4],
            skill6=skills[5] if len(skills) > 5 else skills[0],
            skill7=skills[6] if len(skills) > 6 else skills[1],
        )

        days_ago = random.randint(0, 180)
        created = (base_date + timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Use correlated salary bands to ensure min <= max
        band = random.choice(_SALARY_BANDS + [(None, None)])
        job = {
            "id": f"mock_{i:05d}",
            "title": role,
            "company": {"display_name": company},
            "location": {"display_name": location},
            "description": description,
            "created": created,
            "salary_min": band[0],
            "salary_max": band[1],
            "_query": role,
            "_source": "mock",
            "_scraped_at": datetime.utcnow().isoformat(),
        }
        jobs.append(job)

    with open(out_path, "w") as f:
        for job in jobs:
            f.write(json.dumps(job) + "\n")

    logger.info("Generated %d mock jobs -> %s", n, out_path)
    return out_path
