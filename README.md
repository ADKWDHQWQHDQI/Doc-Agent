# Universal Documentation Agent - MVP

![Azure OpenAI](https://img.shields.io/badge/Azure-OpenAI-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

An intelligent multi-agent system that generates professional technical and business documentation from various inputs using **Azure OpenAI** and a **Multi-Agent Architecture**.

## 🌟 Features

### Document Types Supported

- **BRD** (Business Requirements Document)
- **FRD** (Functional Requirements Document)
- **NFRD** (Non-Functional Requirements Document)
- **Cloud Implementation Guide** (Azure-focused)
- **Security & Compliance Documentation**
- **API Documentation**

### Input Sources

- ✍️ Natural language prompts
- 💻 Source code repositories (Python, Java, C#, JavaScript, etc.)
- 📄 Multiple file formats
- 🎯 Specific file analysis

### Multi-Agent Architecture

The system uses **6 specialized AI agents** working together:

1. **Dispatcher Agent** - Routes requests to appropriate workflows
2. **Requirement Analyst Agent** - Extracts and structures requirements
3. **Code Researcher Agent** - Analyzes source code and architecture
4. **Technical Writer Agent** - Drafts documentation
5. **Security Reviewer Agent** - Reviews and enhances security sections
6. **Editor & Formatter Agent** - Polishes final output

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Azure OpenAI Service account with API key
- GPT-4o or GPT-4 deployment

### Installation

1. **Clone or download this project**

   ```bash
   cd universal-doc-agent-mvp
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Azure OpenAI credentials**

   ```bash
   copy .env.example .env
   ```

   Edit `.env` and add your credentials:

   ```env
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_API_VERSION=2024-08-01-preview
   ```

### Usage Examples

#### 1. Generate a BRD from a prompt

```bash
python main.py --request "Create a BRD for an e-commerce platform with payment gateway integration"
```

#### 2. Generate FRD from source code

```bash
python main.py --request "Generate a Functional Requirements Document" --code-dir ./my-project
```

#### 3. Generate Cloud Implementation Guide

```bash
python main.py --request "Create an Azure deployment guide" --code-dir ./app --doc-type CLOUD
```

#### 4. Analyze specific files

```bash
python main.py --request "Document these API endpoints" --files api.py routes.py models.py
```

#### 5. Generate Security Documentation

```bash
python main.py --request "Create security documentation" --code-dir ./secure-app --doc-type SECURITY
```

## 📁 Project Structure

```
universal-doc-agent-mvp/
├── agents/                    # Multi-agent definitions
│   ├── __init__.py
│   ├── base_agent.py         # Base agent class
│   └── specialized_agents.py # 6 specialized agents
├── tools/                     # Utility tools
│   ├── __init__.py
│   ├── file_tools.py         # File operations
│   └── templates.py          # Document templates
├── outputs/                   # Generated documents
├── templates/                 # Template storage
├── config.py                  # Configuration management
├── orchestrator.py            # Multi-agent workflow orchestration
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables

| Variable                       | Required | Description                               |
| ------------------------------ | -------- | ----------------------------------------- |
| `AZURE_OPENAI_ENDPOINT`        | Yes      | Your Azure OpenAI resource endpoint       |
| `AZURE_OPENAI_API_KEY`         | Yes      | Your Azure OpenAI API key                 |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Yes      | Deployment name (e.g., gpt-4o)            |
| `AZURE_OPENAI_API_VERSION`     | No       | API version (default: 2024-08-01-preview) |
| `OUTPUT_DIR`                   | No       | Output directory (default: outputs)       |
| `LOG_LEVEL`                    | No       | Logging level (default: INFO)             |

### Azure OpenAI Setup

1. **Create Azure OpenAI Resource**

   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new "Azure OpenAI" resource
   - Deploy a GPT-4o or GPT-4 model

2. **Get Credentials**

   - Navigate to your Azure OpenAI resource
   - Go to "Keys and Endpoint"
   - Copy the endpoint and one of the keys

3. **Deploy Model**
   - Go to "Model deployments"
   - Deploy `gpt-4o` (recommended) or `gpt-4`
   - Copy the deployment name

## 💰 Cost Considerations

### Single Agent vs Multi-Agent Cost

This system uses a **multi-agent architecture**, which is actually **more cost-effective** than a single agent for complex tasks:

- **Single Agent**: Processes all information at once (expensive, prone to errors)
- **Multi-Agent**: Breaks tasks into specialized steps (cheaper, higher quality)

**Example Cost** (GPT-4o pricing as of Nov 2024):

- Generating a 2000-word FRD from code: **~$0.25 - $0.50**
- Input tokens: $2.50 per 1M tokens
- Output tokens: $10 per 1M tokens

### Cost Optimization Tips

1. Use code summaries instead of full code (done automatically)
2. Start with smaller codebases
3. Use GPT-4o-mini for simpler documents
4. Monitor usage in Azure Portal

## 🎯 Use Cases

### For Software Teams

- Generate technical specs from existing code
- Create API documentation automatically
- Document cloud infrastructure

### For Product Managers

- Create BRDs and FRDs quickly
- Document feature requirements
- Generate user stories

### For Compliance Teams

- Generate security documentation
- Create compliance checklists
- Document data protection measures

## 🔐 Security & Privacy

- All processing uses **Azure OpenAI** (enterprise-grade security)
- Data stays within your Azure subscription
- No data sent to public OpenAI endpoints
- Supports Azure Private Endpoints

## 🚧 Limitations (MVP)

- Output format: Currently Markdown only (DOCX/PDF conversion requires additional setup)
- No RAG integration (can be added with Azure AI Search)
- No PDF input parsing (requires Azure Document Intelligence)
- No web interface (CLI only)

## 🛣️ Roadmap

- [ ] Add DOCX and PDF export
- [ ] Integrate Azure AI Search for RAG
- [ ] Add Azure Document Intelligence for PDF parsing
- [ ] Create web UI (Streamlit/Gradio)
- [ ] Support for diagram analysis (GPT-4o Vision)
- [ ] Multi-language support
- [ ] Template customization

## 📝 Example Output

The agent generates professional Markdown documents with:

- ✅ Proper structure and sections
- ✅ Tables and formatting
- ✅ Code examples (where applicable)
- ✅ Security considerations
- ✅ Compliance notes

All documents are saved in the `outputs/` directory with timestamps.

## 🤝 Contributing

This is an MVP. Contributions welcome for:

- Additional document types
- New agent capabilities
- Integration with other Azure services
- UI improvements

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

### Common Issues

**Error: "Configuration Error"**

- Check your `.env` file
- Verify Azure OpenAI credentials
- Ensure model is deployed

**Error: "Rate Limit"**

- Check your Azure OpenAI quota
- Wait and retry
- Consider using a different deployment

**Error: "Model not found"**

- Verify deployment name in `.env`
- Check if model is deployed in Azure Portal

### Getting Help

- Check Azure OpenAI documentation
- Review Azure Portal for quota/errors
- Check the `outputs/workflow_log_*.txt` for detailed execution logs

## 🎓 Learn More

- [Azure OpenAI Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/)
- [Multi-Agent Systems Best Practices](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/assistant)

---

**Built with ❤️ using Azure OpenAI and Multi-Agent Architecture**

_Note: This is an MVP (Minimum Viable Product). For production use, consider adding error handling, retry logic, monitoring, and additional security measures._
