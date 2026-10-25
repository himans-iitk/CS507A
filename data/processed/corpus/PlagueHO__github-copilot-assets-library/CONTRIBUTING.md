# Contributing to GitHub Copilot Assets Library

Thank you for your interest in contributing to the GitHub Copilot Assets Library! This repository serves as a community resource for sharing GitHub Copilot customization assets including Custom Chat Modes, Prompt Files, and other Copilot enhancement tools.

## What We Accept

We welcome contributions of the following asset types:

### Custom Chat Modes

- **Location**: [`.github/chatmodes/`](.github/chatmodes/)
- **File naming**: `[descriptive-name].chatmode.md` (lowercase with hyphens)
- **Purpose**: Specialized modes that combine instructions and tools for specific workflows

### Prompt Files

- **Location**: [`.github/prompts/`](.github/prompts/)
- **File naming**: `[descriptive-name].prompt.md` (lowercase with hyphens)
- **Purpose**: Reusable prompts for common development tasks

### MCP Server Configurations

- **Location**: [`.vscode/mcp.json`](.vscode/mcp.json)
- **Purpose**: External service integrations for enhanced Copilot functionality

## Contribution Guidelines

### Quality Standards

All contributions must meet these requirements:

1. **Self-Contained**: Each asset should be complete and context-independent
2. **Precise Language**: Use explicit, unambiguous instructions
3. **Structured Format**: Use proper headings, bullets, and tables for clarity
4. **No Boilerplate**: Avoid generic advice, focus on specific guidance
5. **Practical Value**: Provide clear benefits for common development scenarios

### File Standards

#### Chat Mode Format

Chat mode files must follow this structure:

```markdown
---
description: Brief description of the chat mode purpose
tools: [list, of, applicable, tools]
---

# Chat Mode Title

## Instructions

Clear, specific instructions for the chat mode behavior.

## Context

Additional context or background information.

## Examples

Usage examples or scenarios where this mode is beneficial.
```

**Requirements:**

- Include comprehensive tool arrays based on functionality needs
- Structure instructions in clear sections with specific guidance
- Reference industry experts or thought leaders for authority when applicable
- Specify target frameworks and versions explicitly when relevant

#### Prompt File Format

Prompt files must follow this structure:

```markdown
---
mode: [chat|inline|agent]
description: Brief description of the prompt purpose
---

# Prompt Title

## Task Description

Clear description of what the prompt accomplishes.

## Instructions

Detailed instructions for executing the task.

## Variables

Use `${input:VariableName}` syntax for user inputs.

## Expected Outcomes

Description of expected results and deliverables.
```

**Requirements:**

- Include variable substitution using `${input:VariableName}` syntax where applicable
- Provide clear task descriptions and expected outcomes
- Follow specification template structure for consistency
- Include examples and edge cases where applicable

### Content Guidelines

#### Language and Tone

- Use professional, technical language appropriate for developers
- Be specific rather than general
- Provide actionable guidance
- Include relevant technical details

#### Technical Requirements

- Follow Markdown syntax standards
- Ensure valid YAML front matter
- Use appropriate heading hierarchy (# ## ###)
- Include proper code formatting when showing examples

#### Scope and Focus

- Focus on widely applicable scenarios
- Avoid organization-specific or proprietary information
- Ensure cross-platform compatibility where possible
- Consider diverse development environments

## Submission Process

### Before You Submit

1. **Check Existing Assets**: Review existing chat modes and prompts to avoid duplication
2. **Test Your Asset**: Verify your contribution works as intended in VS Code
3. **Follow Naming Conventions**: Use lowercase with hyphens for file names
4. **Validate Markdown**: Ensure proper syntax and front matter structure

### Pull Request Process

1. **Fork the Repository**: Create your own fork of the repository
2. **Create a Feature Branch**: Use a descriptive branch name (e.g., `add-testing-chatmode`)
3. **Add Your Asset**: Place files in the appropriate directory structure
4. **Update README**: Add your contribution to the relevant table in README.md
5. **Write Clear Commit Messages**: Follow the format specified in the repository

#### Commit Message Format

Follow this pattern:

```text
[TYPE]: [50 char summary]

Detailed summary with `-` bullets:
- Brief description of changes
- Any important considerations
- Breaking changes or security notes
```

Where TYPE is one of: CHORE|FIX|CHANGE|BREAKING CHANGE|TESTS|SECURITY|COMPLEX

### Pull Request Requirements

Your PR should include:

1. **New Asset File(s)**: Properly formatted and located
2. **README Update**: Add entry to the appropriate table
3. **Clear Description**: Explain the purpose and benefits of your contribution
4. **Testing Notes**: How you verified the asset works correctly

### Review Process

1. **Automated Checks**: Ensure Markdown syntax validation passes
2. **Community Review**: Other contributors may provide feedback
3. **Maintainer Review**: Final review by repository maintainers
4. **Merge**: Approved contributions will be merged into the main branch

## Examples and Templates

### Chat Mode Template

```markdown
---
description: Expert guidance for [specific domain/technology]
tools: [workspace, read_file, list_dir, semantic_search, grep_search]
---

# [Technology/Domain] Expert

You are an expert [technology/domain] engineer with deep knowledge of [specific areas].

## Instructions

### Core Expertise
- [Specific capability 1]
- [Specific capability 2]
- [Specific capability 3]

### Response Guidelines
- Provide detailed technical explanations
- Reference best practices and industry standards
- Suggest specific tools, libraries, or patterns
- Include code examples when relevant

### Quality Standards
- Follow [specific framework/technology] conventions
- Prioritize [relevant principles like performance, security, etc.]
- Consider [specific considerations for the domain]

## Context

This mode is designed for developers working with [technology/domain] who need expert-level guidance on [specific scenarios].
```

### Prompt File Template

```markdown
---
mode: chat
description: [Brief description of what this prompt accomplishes]
---

# [Prompt Name]

## Task

[Clear description of the task this prompt performs]

## Instructions

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Input Variables

- `${input:Variable1}`: Description of variable 1
- `${input:Variable2}`: Description of variable 2

## Expected Output

[Description of expected results and format]

## Examples

[Usage examples or scenarios where this prompt is beneficial]
```

## Questions or Issues?

If you have questions about contributing or need clarification on requirements:

1. **Check Existing Issues**: Look for similar questions in the repository issues
2. **Create a Discussion**: Use GitHub Discussions for general questions
3. **Open an Issue**: For specific problems or suggestions

## License

By contributing to this repository, you agree that your contributions will be licensed under the same license as the project.

Thank you for helping make GitHub Copilot more useful for the developer community!
