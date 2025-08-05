# Build Bootcamp Agenda Prompt

## Task Overview
Create a comprehensive 3-day bootcamp agenda for building the Wealth Management Advisor Assistant Agent based on the research findings in `.claude/research/exploration-result.md`.

## Team Composition
- **1 Data Scientist**: Expertise in data analysis, model evaluation, statistical insights, API integration patterns
- **2 Research Engineers**: Expertise in system architecture, advanced AI patterns, technical implementation, framework evaluation  
- **1 Software Engineer**: Expertise in production systems, API development, testing, deployment, infrastructure

## Target System Goals (from exploration.md)
Build 2 core agent capabilities:
1. **Meeting Intelligence Agent**: transcript/summary → relevant URLs/references/explanations
2. **Strategic Advisory Agent**: transcript + summary + client profile → tailored investment strategy

## Available Resources
- **Data Sources**: `data/transcript/`, `data/summary/`, `data/client-profile/`
- **Integrated Tools**: 
  - CRA publications (Weaviate RAG system)
  - Statistics Canada API
  - Bank of Canada API  
  - Twelve Data API
- **Context**: 3-day bootcamp for developers learning agent systems

## Key Constraints & Requirements

### Technical Constraints
- **3 days maximum** for bootcamp duration
- **4 team members** with complementary skill sets
- **Learning-focused environment** - developers new to agent systems
- **Feasible scope** - working prototype demonstration rather than production system

### Deliverable Requirements
- **Working Meeting Intelligence Agent** that processes transcripts and returns relevant financial references
- **Working Strategic Advisory Agent** that combines client data to generate investment recommendations
- **API integration examples** using all 4 available tools (CRA/StatCan/BoC/Twelve Data)
- **Evaluation framework** for measuring agent accuracy and relevance
- **Clear learning documentation** for agent system concepts and implementation

## Research Context Integration
Base the agenda on key findings from exploration research:

### Priority Implementation Areas
1. **Meeting Intelligence Architecture**: Transcript processing → entity extraction → knowledge base search → relevant document retrieval
2. **Strategic Advisory Logic**: Client profile analysis + market data → risk assessment → portfolio recommendations
3. **Canadian Financial Integration**: Production patterns for BoC/StatCan/CRA data integration
4. **Multi-agent Coordination**: How the two agents can share context and cross-validate outputs
5. **Framework Selection**: Best approach for the specific use case based on research findings

### Critical Success Patterns from Research
- **Domain-specific tooling** over generic solutions for financial context
- **Knowledge graph enhancement** for relationship-aware document retrieval  
- **Cross-verification** between agents to reduce hallucinations in financial advice
- **Progressive disclosure** from summary insights to detailed analysis
- **Graceful degradation** when external APIs are unavailable

## Agenda Structure Requirements

Create a day-by-day schedule that balances learning with implementation. Include morning kickoffs, focused work sessions, integration checkpoints, and end-of-day demos. Assign specific roles and deliverables to each team member based on their expertise.

Structure progression from foundational concepts (Day 1) through multi-agent architecture (Day 2) to production considerations (Day 3). Ensure sufficient time for both concept learning and hands-on implementation.

## Instructions for Agenda Creation

### Content Requirements
- Executive summary of bootcamp goals and outcomes
- Detailed hourly breakdown for each day
- Clear role assignments for each activity
- Specific deliverable specifications with acceptance criteria
- Learning objectives integrated with implementation tasks

### Success Validation
Ensure the agenda addresses:
- Both Meeting Intelligence and Strategic Advisory agent objectives
- All available tools (CRA/StatCan/BoC/Twelve Data) integration
- Team learning needs for agent system concepts
- Realistic time allocation for implementation and debugging
- Cross-team collaboration and integration checkpoints

### Risk Mitigation
Account for common bootcamp challenges:
- Learning curve for new technologies and concepts  
- API integration complexity and debugging time
- Component integration between team members
- Scope management to maintain achievable deliverables

Use exploration research findings to inform technical approach recommendations while maintaining appropriate scope for a 3-day learning-focused bootcamp.