# Strands Agents: Loan Application Evaluator

A multi-agent evaluation system for loan applications using AWS Strands agents and Bedrock models. Leverages multiple specialized AI agents (Credit Analyst, Compliance Officer, Fraud Detector, Loan Officer) to provide comprehensive loan assessments.

## Overview

This project demonstrates how to use Strands agents with AWS Bedrock to build a sophisticated loan evaluation system. Each agent specializes in a specific aspect of loan evaluation:

- **Credit Risk Analyst**: Assesses creditworthiness, debt-to-income ratios, credit history
- **Compliance Officer**: Ensures regulatory compliance, KYC requirements, documentation quality
- **Fraud Detection Specialist**: Identifies potential fraud patterns, document inconsistencies
- **Loan Officer**: Provides holistic assessment and final recommendation

### Key Features

- Multi-agent orchestration using Strands
- AWS Bedrock integration for LLM inference
- Structured evaluation with Pydantic models
- LangSmith logging for agent tracing and monitoring
- Configurable evaluation criteria and scoring
- Sample data and realistic test cases
- Jupyter notebook for interactive evaluation
- Comprehensive test suite

## Prerequisites

- Python 3.10+
- AWS Account with Bedrock access
- AWS credentials configured locally
- pip or conda

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/isadays/strands-agents-loan-evaluator.git
cd strands-agents-loan-evaluator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure AWS

```bash
aws configure
```

### 3. Run the Evaluator

Open and run the Jupyter notebook:
```bash
cd testing_langfuse/loan-evaluator
jupyter notebook evaluator_v1.ipynb
```

Or use Python directly:
```bash
python loan_evaluator.py
```

## Project Structure

```
strands-agents-loan-evaluator/
├── testing_langfuse/
│   └── loan-evaluator/
│       ├── evaluator_v1.ipynb
│       ├── loan_evaluator.py
│       ├── models.py
│       ├── prompts/
│       │   ├── credit_analyst_prompt.txt
│       │   ├── compliance_prompt.txt
│       │   ├── fraud_detection_prompt.txt
│       │   └── loan_officer_prompt.txt
│       └── sample_data/
│           ├── loan_application_1.json
│           ├── loan_application_2.json
│           └── loan_application_3.json
├── tests/
│   ├── test_project.py
│   ├── demo.py
│   └── README.md
├── requirements.txt
├── TESTING.md
├── README.md
└── LICENSE
```

## Example Usage

```python
from testing_langfuse.loan_evaluator import LoanEvaluator

evaluator = LoanEvaluator()

loan_app = LoanApplication(
    applicant_name="John Doe",
    requested_amount=250000,
    loan_purpose="Home Purchase",
    employment_status="Employed",
    annual_income=85000,
    credit_score=720,
    employment_years=5,
    documents_provided=["pay_stubs", "tax_returns", "bank_statements"]
)

result = evaluator.evaluate(loan_app)

for review in result.reviews:
    print(f"{review.reviewer_name}: {review.score}/100")
    print(f"Recommendation: {review.recommended_action}")
```

## Configuration

Edit the `LoanEvaluator` class initialization to customize:
- LLM model (default: Claude 3.5 Sonnet via Bedrock)
- AWS region
- LangSmith logging preferences

## Evaluation Output

Each loan application receives:
- **Score** (0-100): Overall assessment
- **Strengths**: Key positive factors
- **Risks**: Potential concerns
- **Recommended Action**: Approve/Deny/Request More Info
- **Confidence**: Model's confidence in the assessment
- **Detailed Analysis**: Each agent's specialized feedback

## Agents Overview

### Credit Risk Analyst
Evaluates:
- Credit score and history
- Debt-to-income ratio
- Income stability and growth
- Payment history
- Loan-to-value ratio

### Compliance Officer
Checks:
- Document completeness and authenticity
- KYC requirements
- Regulatory compliance
- Risk category classification
- Documentation quality

### Fraud Detection Specialist
Investigates:
- Income documentation inconsistencies
- Employment verification gaps
- Address history anomalies
- Document authenticity signals
- Application pattern anomalies

### Loan Officer
Provides:
- Holistic assessment combining all perspectives
- Final recommendation
- Suggested loan terms if approved
- Recommended next steps

## LangSmith Integration

When `use_langsmith=True`, agent interactions are logged to LangSmith for:
- Agent trace visualization
- Performance monitoring
- Token usage tracking
- Cost analysis
- Debugging and optimization

Set the standard LangSmith environment variables before running:

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_ENDPOINT=https://api.smith.langchain.com
export LANGSMITH_API_KEY=<your-langsmith-api-key>
export LANGSMITH_PROJECT="strands-agents-loan"
```

## Testing

Run the test suite to verify all components:

```bash
python3 tests/test_project.py
```

Run the demonstration to see the full workflow:

```bash
python3 tests/demo.py
```

See [tests/README.md](tests/README.md) for detailed information.

## Learning Resources

- [Strands Documentation](https://github.com/strands-ai/strands)
- [AWS Bedrock Quickstart](https://docs.aws.amazon.com/bedrock/)
- [LangSmith Documentation](https://docs.langchain.com/langsmith)
- [Agent Design Patterns](./docs/agent-patterns.md)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit changes (`git commit -am 'Add YourFeature'`)
4. Push to branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Support

For issues, questions, or feedback:
- Open an issue on GitHub
- Check existing documentation in TESTING.md
- Review the notebook examples

---

Built with Strands agents and AWS Bedrock
