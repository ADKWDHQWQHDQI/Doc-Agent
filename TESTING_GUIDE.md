# 🧪 Universal Documentation Agent - Comprehensive Testing Guide

Complete test suite to validate all features of the documentation agent system.

---

## 📋 Test Category 1: Basic Document Generation

### Test 1.1: Simple BRD Generation

```bash
python main.py --request "Create a BRD for an e-commerce platform with shopping cart and payment processing"
```

**Expected**: BRD document in `outputs/` folder

### Test 1.2: FRD Generation

```bash
python main.py --request "Generate FRD for a task management application"
```

**Expected**: FRD document with functional requirements

### Test 1.3: Cloud Document

```bash
python main.py --request "Create Azure deployment guide for a web application"
```

**Expected**: CLOUD document with deployment steps

### Test 1.4: Security Document

```bash
python main.py --request "Generate security documentation for a banking application"
```

**Expected**: SECURITY document with security requirements

---

## 📋 Test Category 2: Multi-Document Generation (Async Parallel)

### Test 2.1: Multiple Docs from Single Request

```bash
python main.py --request "Create BRD, FRD, and Cloud document for a microservices-based inventory system"
```

**Expected**: 3 documents + 1 package summary, parallel execution logs

### Test 2.2: All Document Types

```bash
python main.py --request "Generate complete documentation package (BRD, FRD, NFRD, CLOUD, SECURITY) for healthcare patient management system"
```

**Expected**: 5 documents + package summary

---

## 📋 Test Category 3: Code Analysis (Async Parallel Execution)

### Test 3.1: Analyze Python Code

```bash
python main.py --request "Generate FRD for this multi-agent documentation system" --code-dir ./agents
```

**Expected**: FRD with code analysis, parallel Step 2 & 3 execution  
**Note**: Be specific about document type (FRD) and domain to avoid Dispatcher asking for clarification

### Test 3.2: Specific Files

```bash
python main.py --request "Create technical documentation for the agent architecture" --files agents/base_agent.py agents/specialized_agents.py
```

**Expected**: Documentation based on 2 files, code structure analysis  
**Note**: Provide clear context about what you're documenting

### Test 3.3: Multi-Doc with Code

```bash
python main.py --request "Create BRD and FRD for the file processing tools system" --code-dir ./tools
```

**Expected**: Multiple docs with code insights, async parallel processing  
**Note**: Specify both doc types explicitly and provide system context

---

## 📋 Test Category 4: Interactive Conversation Mode

### Test 4.1: Vague Request (Should Ask Questions)

```bash
python main.py --request "Create documentation" --interactive
```

**Expected**: Agent asks clarifying questions about features, type, etc.
**Action**: Answer the questions iteratively

### Test 4.2: Partial Request

```bash
python main.py --request "Build a mobile app" --interactive
```

**Expected**: Multi-turn conversation gathering requirements
**Action**: Provide details when asked, or type `proceed` to continue

### Test 4.3: Skip Clarification

```bash
python main.py --request "Create trading application" --interactive
```

**Action**: When asked questions, type `proceed` immediately
**Expected**: Agent uses reasonable defaults and generates docs

---

## 📋 Test Category 5: Configuration & Output Options

### Test 5.1: Quiet Mode

```bash
python main.py --request "Create BRD for CRM system" --quiet
```

**Expected**: Minimal output, only final result path

### Test 5.2: Full Preview

```bash
python main.py --request "Generate API documentation" --full-preview
```

**Expected**: Complete document content displayed (not truncated at 500 chars)

### Test 5.3: Custom Output Path

```bash
python main.py --request "Create FRD for inventory system" --output ./custom_docs/inventory_frd.md
```

**Expected**: Document saved to custom path

### Test 5.4: Specific Document Type

```bash
python main.py --request "Document our authentication system" --doc-type SECURITY
```

**Expected**: Forces SECURITY document type

---

## 📋 Test Category 6: Error Handling & Edge Cases

### Test 6.1: Invalid Code Directory

```bash
python main.py --request "Analyze code" --code-dir ./nonexistent
```

**Expected**: Validation error with helpful message

### Test 6.2: Invalid Files

```bash
python main.py --request "Document" --files notfound.py
```

**Expected**: File not found error before execution

### Test 6.3: Empty Files Argument

```bash
python main.py --request "Document" --files
```

**Expected**: Argument validation error

### Test 6.4: Large Code Directory (Test Token Limits)

```bash
python main.py --request "Generate FRD" --code-dir "C:\Windows\System32"
```

**Expected**: Token truncation warnings, still generates document

---

## 📋 Test Category 7: Agent Registry & Foundry Integration

### Test 7.1: Check Azure AI Foundry Agents

**After any test run, check Azure AI Foundry portal:**

1. Go to https://ai.azure.com
2. Navigate to your project
3. Check "Agents" section

**Expected**: See 6 registered agents (Dispatcher, Analyst, Researcher, Writer, Security, Editor)

### Test 7.2: Agent Reuse

```bash
python main.py --request "Create BRD for project A"
python main.py --request "Create BRD for project B"
```

**Expected**: Second run shows "Found existing agent" logs (no recreation)

---

## 📋 Test Category 8: Performance & Async (Time These)

### Test 8.1: Sequential vs Async Comparison

```bash
# Test with code (enables parallel Step 2 & 3)
python main.py --request "Generate FRD" --code-dir ./agents
```

**Watch console output**: Look for "⚡ Steps 2 & 3: Parallel execution" message

**Expected**: ~50% faster than if sequential

### Test 8.2: Multi-Document Performance

```bash
python main.py --request "Create BRD, FRD, CLOUD for real-time chat app"
```

**Expected**: Shared requirements analysis (only runs once), not 3 times

---

## 📋 Test Category 9: Content Quality Validation

### Test 9.1: Business Document Quality

```bash
python main.py --request "Create BRD for enterprise HR management system with employee onboarding, payroll, and performance reviews"
```

**Verify output contains:**

- ✅ Executive Summary
- ✅ Business Objectives
- ✅ Stakeholder Analysis
- ✅ Requirements (functional/non-functional)
- ✅ Professional formatting

### Test 9.2: Technical Document Quality

```bash
python main.py --request "Generate FRD with security review" --code-dir ./agents --doc-type FRD
```

**Verify output contains:**

- ✅ System Architecture
- ✅ API specifications
- ✅ Data models
- ✅ Security sections (added by Security Reviewer agent)

### Test 9.3: Cloud Document Quality

```bash
python main.py --request "Create Azure deployment guide for containerized microservices"
```

**Verify output contains:**

- ✅ Infrastructure requirements
- ✅ Deployment steps
- ✅ Configuration details
- ✅ Monitoring setup

---

## 📋 Test Category 10: Workflow Logging

### Test 10.1: Check Workflow Logs

```bash
python main.py --request "Create BRD for mobile game"
```

**After completion, check:**

- `outputs/workflow_log_YYYYMMDD_HHMMSS.txt`

**Expected**: Detailed step-by-step execution log with timestamps

---

## 📋 Test Category 11: Specialized Agent Behavior

### Test 11.1: Dispatcher Intelligence

```bash
python main.py --request "healthcare HIPAA compliant patient portal"
```

**Expected**: Dispatcher detects "healthcare" → adds SECURITY document automatically

### Test 11.2: Security Review Trigger

```bash
python main.py --request "Create FRD for financial trading platform"
```

**Expected**: Security Reviewer agent automatically reviews FRD (not BRD)

### Test 11.3: Code Researcher with Tools

```bash
python main.py --request "Generate technical docs" --code-dir ./tools
```

**Expected**: Code Researcher uses code_interpreter tool, extracts structure via AST parsing

---

## 📊 Test Results Checklist

After running tests, verify:

- [ ] All 6 agents visible in Azure AI Foundry portal
- [ ] Documents generated in `outputs/` folder
- [ ] Workflow logs created
- [ ] Parallel execution logs show "⚡ Steps 2 & 3: Parallel execution"
- [ ] No "Error retrieving messages" in document content
- [ ] Multi-document packages include summary file
- [ ] Interactive mode asks relevant questions
- [ ] Token truncation warnings appear for large codebases
- [ ] Agent registry prevents duplicate agent creation
- [ ] Documents contain proper formatting (headings, tables, code blocks)

---

## 🎯 Quick Smoke Test (Run This First)

```bash
# Simple end-to-end test
python main.py --request "Create a BRD for a simple calculator app with basic arithmetic operations"
```

**If this works, your system is ready for comprehensive testing!**

---

## 📊 Performance Benchmarks to Track

| Test Type                   | Expected Duration | What to Measure                 |
| --------------------------- | ----------------- | ------------------------------- |
| Simple BRD (no code)        | ~15-20 seconds    | Total execution time            |
| FRD with code analysis      | ~25-35 seconds    | With async parallel Step 2 & 3  |
| 3-document package          | ~45-60 seconds    | Shared context optimization     |
| Interactive mode (3 rounds) | ~30-45 seconds    | Total conversation + generation |

---

## 🔧 Test Execution Tips

### Running All Tests

```bash
# Create a test script to run all tests
# Save commands to test_all.bat (Windows) or test_all.sh (Linux/Mac)
```

### Viewing Real-Time Logs

```bash
# Windows PowerShell
Get-Content outputs\workflow_log_*.txt -Wait -Tail 50

# Linux/Mac
tail -f outputs/workflow_log_*.txt
```

### Checking Output Files

```bash
# List all generated documents
dir outputs\*.md

# Or on Linux/Mac
ls -lh outputs/*.md
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "Microsoft Agent Framework not available"

**Solution**:

```bash
pip install agent-framework-azure-ai --pre
```

_Note: We use the preview version of the Microsoft Agent Framework._

### Issue 2: "WeasyPrint external libraries" warning

**Solution**: This is harmless - PDF export requires additional libraries, but Markdown works fine

### Issue 3: Slow execution

**Solution**:

- Check `USE_ASYNC_ORCHESTRATION=true` in `.env`
- Verify parallel execution logs appear

### Issue 4: Agent not found in portal

**Solution**:

- Check Azure credentials in `.env`
- Verify `AZURE_PROJECT_NAME` and `AZURE_RESOURCE_GROUP` are correct
- Run `python reset_agents.py` to recreate

### Issue 5: "❓ Clarification Needed" - Request too vague

**Problem**: Dispatcher asks for more information even with `--code-dir` or `--files`

**Solution**: Make requests more specific:

- ❌ Bad: `"Generate technical documentation"`
- ✅ Good: `"Generate FRD for this multi-agent documentation system"`
- ❌ Bad: `"Document these agent files"`
- ✅ Good: `"Create technical documentation for the agent architecture"`

**Key tips**:

- Always specify document type (BRD, FRD, NFRD, CLOUD, SECURITY)
- Provide system/domain context (e.g., "e-commerce platform", "agent system", "file tools")
- Describe the purpose or features briefly

---

## 📈 Advanced Testing Scenarios

### Stress Test: Large Codebase

```bash
python main.py --request "Generate comprehensive FRD" --code-dir "C:\Program Files\Python312\Lib"
```

**Expected**: Token truncation, chunking, still completes

### Concurrent Execution Test

```bash
# Run multiple instances simultaneously
start python main.py --request "Create BRD for app A"
start python main.py --request "Create BRD for app B"
start python main.py --request "Create BRD for app C"
```

**Expected**: All complete without conflicts

### Long-Running Interactive Session

```bash
python main.py --request "Build enterprise system" --interactive
```

**Action**: Have 5+ conversation rounds
**Expected**: Context maintained throughout

---

## 📝 Test Report Template

```markdown
## Test Execution Report

**Date**: [Date]
**Tester**: [Name]
**Environment**: Windows/Mac/Linux

### Test Results Summary

- Total Tests Run: \_\_/30
- Passed: \_\_
- Failed: \_\_
- Skipped: \_\_

### Failed Tests Details

1. Test X.Y: [Description]
   - Error: [Error message]
   - Expected: [What should happen]
   - Actual: [What happened]

### Performance Metrics

- Average BRD generation: \_\_ seconds
- Average FRD with code: \_\_ seconds
- Multi-doc package: \_\_ seconds

### Issues Found

1. [Issue description]
2. [Issue description]

### Recommendations

- [Recommendation 1]
- [Recommendation 2]
```

---

## 🚀 Ready to Test?

**Start with the Quick Smoke Test, then proceed through categories 1-11 systematically.**

Good luck! 🎉
