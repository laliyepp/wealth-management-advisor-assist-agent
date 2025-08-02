# CLAUDE.md

**If you have your own role, ignore this file.**

**If you do not have your own role, read MASTER.md to act as the project lead.**

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
**Wealth Management Advisor Assistant Agent** - A ReAct-powered AI agent for financial advisory and wealth management guidance using knowledge base search and structured reasoning.

## Agent Architecture

### Master Agent
- Complete project knowledge and coordination authority
- **MUST read .claude/prompts/MASTER.md before all tasks**
- Decides when to invoke specialized sub-agents based on task requirements
- Handles complex cross-domain tasks requiring integration

### Sub-Agents (Role-Specific)
- **NEVER read .claude/prompts/MASTER.md under any circumstance**
- Operate strictly within defined scope and expertise
- Follow Master Agent instructions precisely
- Cannot invoke other sub-agents

#### Available Sub-Agents:
- **data-scientist**: Data analysis, evaluation metrics, statistical insights  
- **code-reviewer**: Code quality assessment, best practices enforcement
- **debugger**: Issue diagnosis, troubleshooting, error resolution
- **test-engineer**: Test creation, validation, quality assurance
- **prompt-engineer**: Evaluation prompt optimization and refinement

## Project Context
For project-specific technical details, architecture, and domain knowledge:
@.claude/prompts/project.md