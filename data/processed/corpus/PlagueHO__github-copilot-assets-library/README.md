
# 🤖 GitHub Copilot Assets Library

Enhance your GitHub Copilot experience with comprehensive instructions, prompts, chat modes, and configurations. Get consistent AI assistance that follows your team's coding standards and project requirements for development, architecture, planning, and documentation tasks.

There are many ways GitHub Copilot can be used to help you with not just your coding tasks, but also with ideation, problem solving, understanding, planning, research and so much more.

The biggest challenge is either creating or finding the right prompts and tools to get the most out of GitHub Copilot - and when to use them.

I've spent many hours building my own tools and prompts and chat modes to help me with my work, and I want to share them with you.

> [!NOTE]
> I created this repository without knowing the GitHub team had plans to release a similar library [https://github.com/github/awesome-copilot](https://github.com/github/awesome-copilot). However, I am planning to migrate all the resource from this repository over to the Github Awesome Copilot repository in the future. So, you will start seeing duplicated content in both repositories.

## 🎯 GitHub Copilot Customization Features

GitHub Copilot provides multiple ways to customize AI responses and tailor assistance to your specific workflows, team guidelines, and project requirements:

| **🔧 Custom Instructions** | **📝 Prompt Files (Reusable Prompts)** | **🧩 Custom Chat Modes** | **🔌 MCP Servers** |
| --- | --- | --- | --- |
| Define common guidelines for tasks like code generation, reviews, and commit messages. Describe *how* tasks should be performed<br><br>**Benefits:**<br>• Automatic inclusion in every chat request<br>• Repository-wide consistency<br>• Multiple implementation options | Create reusable, standalone prompts for specific tasks. Describe *what* should be done with optional task-specific guidelines<br><br>**Benefits:**<br>• Eliminate repetitive prompt writing<br>• Shareable across teams<br>• Support for variables and dependencies | Define chat behavior, available tools, and codebase interaction patterns within specific boundaries for each request<br><br>**Benefits:**<br>• Context-aware assistance<br>• Tool configuration<br>• Role-specific workflows | Extend GitHub Copilot agents with standardized tools, resources, and prompts via Model Context Protocol for specialized tasks and external integrations<br><br>**Benefits:**<br>• Invoke tools for databases, APIs, and file operations<br>• Access external resources as chat context<br>• Pre-configured prompts for complex workflows<br>• Tool confirmation and parameter editing<br>• Automatic discovery and workspace sharing |

> **💡 Pro Tip:** Custom instructions only affect Copilot Chat (not inline code completions). You can combine all three customization types - use custom instructions for general guidelines, prompt files for specific tasks, and chat modes to control the interaction context.

## Table of Contents

- [Asset Types Overview](#asset-types-overview)
- [Feature Comparison](#copilot-features-comparison-table)
- [Available Assets](#copilot-feature-library)
  - [Copilot Instructions](#copilot-instructions)
  - [📋 Custom Instructions Files](#-custom-instructions-files)
  - [📝 Prompt Files (Reusable Prompts)](#-prompt-files-reusable-prompts)
  - [🧩 Custom Chat Modes](#-custom-chat-modes)
  - [🔌 MCP Servers](#-mcp-servers)

## Asset Types Overview

| Asset Type | Description | Availability | Configuration |
|------------|-------------|--------------|---------------|
| **Copilot Instructions** | Repository-wide instructions to set tone, style, and context for Copilot responses | VS Code & VS | User & Workspace |
| **Custom Instructions** | Language-specific guidelines that apply to file types (e.g., C# files) | VS Code & VS | User & Workspace |
| **Prompt Files** | Reusable, standalone prompts for specific tasks with optional variables | VS Code only | User & Workspace |
| **Custom Chat Modes** | Predefined instructions and tools for specialized workflows and contexts | VS Code only | User & Workspace |
| **MCP Servers** | External service integrations via Model Context Protocol for enhanced functionality | VS Code & VS | User & Workspace |

## Copilot Features Comparison Table

| Feature Name | Description | VS Code/VS Support | Configuration Level |
|--------------|-------------|--------------------|---------------------|
| Copilot Instructions | [Custom instructions](https://code.visualstudio.com/docs/copilot/copilot-customization#_custom-instructions) to set tone, style, and context for Copilot responses. | VS Code & VS | User & Workspace |
| Custom Code Generation Instructions | [Code generation instructions](https://code.visualstudio.com/docs/copilot/copilot-customization#_custom-instructions-examples) for code generation tasks. | VS Code only | User & Workspace |
| Prompt Files | [Prompt files](https://code.visualstudio.com/docs/copilot/copilot-customization#_prompt-files-experimental) are reusable prompts for common tasks. | VS Code only | User & Workspace |
| Custom Chat Modes | [Custom chat modes](https://code.visualstudio.com/docs/copilot/chat/chat-modes#_custom-chat-modes) combine instructions and tools for specific workflows. | VS Code only | User & Workspace |
| MCP Servers | [MCP Servers](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) enable Copilot to call external services via Model Context Protocol. | VS Code & VS | User & Workspace |

## Copilot Feature Library

### Copilot Instructions

Examples for Copilot Instructions can be found in subfolders in the [`copilot-instructions/`](copilot-instructions/) folder.

| Name | Example File | Usage |
|------|--------------|-------|
| Azure Developer Solution Accelerator | [copilot-instructions/azure_developer_solution_accelerator/copilot-instructions.md](copilot-instructions/azure_developer_solution_accelerator/copilot-instructions.md) | Azure Developer CLI (AZD) solution accelerator for deploying Azure resources using modern Infrastructure as Code practices. |

> [!IMPORTANT]
> Copilot Instructions only apply to Chat modes (Ask, Edit, Agent or custom modes), they do not apply to Copilot auto-completion in the editor.

#### Copilot Instructions in workspace usage

To set a custom instruction file in your repository:

1. Copy it from the subfolder in the `copilot-instructions` folder in this repository to the `.github/copilot-instructions/` folder of your repository.
1. (Optional) In Visual Studio Code, use the `Auto-update instructions` command to update the instructions in your repository based on the content of the repository and other AI tools that may have stored instructions in your repository.

    ![Auto-update instructions command in Visual Studio Code](images/auto-update-copilot-instructions.png)

This file will automatically apply to all contributors when they use GitHub Copilot for all file types.

### 📋 Custom Instructions Files

Custom instruction files with specific language and framework guidance can be found in the [`instructions/`](instructions/) folder.

> [!IMPORTANT]
> Custom Instructions only apply to Chat modes (Ask, Edit, Agent or custom modes), they do not apply to Copilot auto-completion in the editor.

| Title | Description | Install |
| ----- | ----------- | ------- |
| [Azure Developer Solution Accelerator](instructions/azure-developer-solution-accelerator.md) | Apply Azure Developer CLI best practices and guidelines for creating Azure solution accelerators | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-instructions%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Finstructions%2Fazure-developer-solution-accelerator.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Achat-instructions%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Finstructions%2Fazure-developer-solution-accelerator.md) |
| [Copilot Thought Logging](instructions/copilot-thought-logging.instructions.md) | See process Copilot is following where you can edit this to reshape the interaction or save when follow up may be needed | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-instructions%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Finstructions%2Fcopilot-thought-logging.instructions.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Achat-instructions%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Finstructions%2Fcopilot-thought-logging.instructions.md) |
| [C# 14 Best Practices](instructions/csharp-14-best-practices.instructions.md) | C# 14 best practices and formatting guidelines for AI code generation | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-instructions%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Finstructions%2Fcsharp-14-best-practices.instructions.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Achat-instructions%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Finstructions%2Fcsharp-14-best-practices.instructions.md) |
| [C# Best Practices (All Versions)](instructions/csharp-best-practices.instructions.md) | C# best practices and formatting guidelines for AI code generation (all versions) | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-instructions%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Finstructions%2Fcsharp-best-practices.instructions.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Achat-instructions%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Finstructions%2Fcsharp-best-practices.instructions.md) |
| [Markdown](instructions/markdown.instructions.md) | Documentation and content creation standards | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-instructions%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Finstructions%2Fmarkdown.instructions.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Achat-instructions%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Finstructions%2Fmarkdown.instructions.md) |

#### Custom Instruction Files in workspace usage

To set a custom instruction file in your repository:

1. Copy it from the `instructions` folder in this repository to the `.github/instructions/` folder of your repository.

This file will automatically apply to all contributors when they use GitHub Copilot in the specified file types (e.g., C# files).

### 📝 Prompt Files (Reusable Prompts)

Prompt file examples are found in the [`prompts/`](prompts/) folder.

| Title | Description | Install |
| ----- | ----------- | ------- |
| [Create Architectural Decision Record (ADR)](prompts/create_architectural_decision_record.prompt.md) | Create an Architectural Decision Record (ADR) document for AI-optimized decision documentation | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_architectural_decision_record.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_architectural_decision_record.prompt.md) |
| [Create GitHub Issue from Specification](prompts/create_github_issue_feature_from_specification.prompt.md) | Create GitHub Issue for feature request from specification file using feature_request.yml template | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_github_issue_feature_from_specification.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_github_issue_feature_from_specification.prompt.md) |
| [Create GitHub Issues for Implementation Plan](prompts/create_github_issues_feature_from_implementation_plan.prompt.md) | Create GitHub Issues from implementation plan phases using feature_request.yml or chore_request.yml templates | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_github_issues_feature_from_implementation_plan.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_github_issues_feature_from_implementation_plan.prompt.md) |
| [Create GitHub Issues for Unmet Requirements](prompts/create_github_issues_for_unmet_specification_requirements.prompt.md) | Create GitHub Issues for unimplemented requirements from specification files using feature_request.yml template | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_github_issues_for_unmet_specification_requirements.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_github_issues_for_unmet_specification_requirements.prompt.md) |
| [Create Implementation Plan](prompts/create_implementation_plan.prompt.md) | Create a new implementation plan file for new features, refactoring existing code or upgrading packages, design, architecture or infrastructure | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_implementation_plan.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_implementation_plan.prompt.md) |
| [Create OO Component Documentation](prompts/create_oo_component_documentation.prompt.md) | Create comprehensive, standardized documentation for object-oriented components following industry best practices and architectural documentation standards | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_oo_component_documentation.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_oo_component_documentation.prompt.md) |
| [Create Specification](prompts/create_specification.prompt.md) | Create a new specification file for the solution, optimized for Generative AI consumption | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_specification.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fcreate_specification.prompt.md) |
| [.NET Best Practices Review](prompts/dotnet_best_practices.prompt.md) | Ensure .NET/C# code meets the best practices specific to the solution/project including documentation, structure, and design patterns | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fdotnet_best_practices.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fdotnet_best_practices.prompt.md) |
| [.NET Design Pattern Review](prompts/dotnet_design_pattern_review.prompt.md) | Review the C#/.NET code for design pattern implementation and suggest improvements for the solution/project | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fdotnet_design_pattern_review.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fdotnet_design_pattern_review.prompt.md) |
| [Update AVM Modules in Bicep](prompts/update_avm_modules_in_bicep.prompt.md) | Update Azure Verified Modules to latest versions in Bicep files | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_avm_modules_in_bicep.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_avm_modules_in_bicep.prompt.md) |
| [Update Implementation Plan](prompts/update_implementation_plan.prompt.md) | Update an existing implementation plan file with new or update requirements to provide new features, refactoring existing code or upgrading packages | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_implementation_plan.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_implementation_plan.prompt.md) |
| [Update LLMs](prompts/update_llms.prompt.md) | Update the llms.txt file in the root folder to reflect changes in documentation or specifications | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_llms.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_llms.prompt.md) |
| [Update Markdown File Index](prompts/update_markdown_file_index.prompt.md) | Update a markdown file section with an index/table of files from a specified folder | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_markdown_file_index.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_markdown_file_index.prompt.md) |
| [Update OO Component Documentation](prompts/update_oo_component_documentation.prompt.md) | Update existing object-oriented component documentation following industry best practices and architectural documentation standards | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_oo_component_documentation.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_oo_component_documentation.prompt.md) |
| [Update Specification](prompts/update_specification.prompt.md) | Update an existing specification file for the solution, optimized for Generative AI consumption based on new requirements or updates to any existing code | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_specification.prompt.md) [![Install in VS Code](https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Aprompt-files%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fprompts%2Fupdate_specification.prompt.md) |

#### Prompt Files in workspace usage

To add a prompt file in your repository:

1. Copy it from the `prompts` folder in this repository to the `.github/prompts/` folder of your repository.
1. In Visual Studio Code, you can execute the prompt file by pressing `/` and selecting the prompt file and adding any required input variables.

    ![Prompt file execution in Visual Studio Code](images/run-custom-prompt-file.png)

This will run the prompt file in the chat and generate the output based on the instructions in the file.

### 🧩 Custom Chat Modes

Chat mode examples are found in the [`chatmodes/`](chatmodes/) folder:

| Title | Description | Install |
| ----- | ----------- | ------- |
| [Azure Principal Architect](chatmodes/azure_principal_architect.chatmode.md) | Provide expert Azure Principal Architect guidance using Azure Well-Architected Framework principles and Microsoft best practices | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fazure_principal_architect.chatmode.md) |
| [Azure SaaS Architect](chatmodes/azure_saas_architect.chatmode.md) | Provide expert Azure SaaS Architect guidance focusing on multitenant applications using Azure Well-Architected SaaS principles and Microsoft best practices | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fazure_saas_architect.chatmode.md) |
| [Azure Verified Modules (Bicep)](chatmodes/azure_verified_modules_bicep.chatmode.md) | Create, update, or review Azure IaC in Bicep using Azure Verified Modules (AVM) | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fazure_verified_modules_bicep.chatmode.md) |
| [Azure Verified Modules (Terraform)](chatmodes/azure_verified_modules_terraform.chatmode.md) | Create, update, or review Azure IaC in Terraform using Azure Verified Modules (AVM) | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fazure_verified_modules_terraform.chatmode.md) |
| [Critical Thinking](chatmodes/critical_thinking.chatmode.md) | Challenge assumptions and encourage critical thinking to ensure the best possible solution and outcomes | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fcritical_thinking.chatmode.md) |
| [C#/.NET Janitor](chatmodes/csharp_dotnet_janitor.chatmode.md) | Perform janitorial tasks on C#/.NET code including cleanup, modernization, and tech debt remediation | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fcsharp_dotnet_janitor.chatmode.md) |
| [Demonstrate Understanding](chatmodes/demonstrate_understanding.chatmode.md) | Validate user understanding of code, design patterns, and implementation details through guided questioning | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fdemonstrate_understanding.chatmode.md) |
| [Expert .NET Software Engineer](chatmodes/expert_dotnet_software_engineer.chatmode.md) | Provide expert .NET software engineering guidance using modern software design patterns | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fexpert_dotnet_software_engineer.chatmode.md) |
| [Expert React Frontend Engineer](chatmodes/expert_react_frontend_engineer.chatmode.md) | Provide expert React frontend engineering guidance using modern TypeScript and design patterns | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fexpert_react_frontend_engineer.chatmode.md) |
| [Implementation Plan](chatmodes/implementation_plan.chatmode.md) | Generate an implementation plan for new features or refactoring existing code | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fimplementation_plan.chatmode.md) |
| [Janitor](chatmodes/janitor.chatmode.md) | Perform janitorial tasks on any codebase including cleanup, simplification, and tech debt remediation | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fjanitor.chatmode.md) |
| [Mentor](chatmodes/mentor.chatmode.md) | Help mentor the engineer by providing guidance and support | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fmentor.chatmode.md) |
| [Principal Software Engineer](chatmodes/principal_software_engineer.chatmode.md) | Provide principal-level software engineering guidance with focus on engineering excellence, technical leadership, and pragmatic implementation | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fprincipal_software_engineer.chatmode.md) |
| [Semantic Kernel (.NET)](chatmodes/semantic_kernel_dotnet.chatmode.md) | Create, update, refactor, explain or work with code using the .NET version of Semantic Kernel | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fsemantic_kernel_dotnet.chatmode.md) |
| [Semantic Kernel (Python)](chatmodes/semantic_kernel_python.chatmode.md) | Create, update, refactor, explain or work with code using the Python version of Semantic Kernel | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fsemantic_kernel_python.chatmode.md) |
| [Simple App Idea Generator](chatmodes/simple_app_idea_generator.chatmode.md) | Brainstorm and develop new application ideas through fun, interactive questioning until ready for specification creation | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fsimple_app_idea_generator.chatmode.md) |
| [Specification](chatmodes/specification.chatmode.md) | Generate or update specification documents for new or existing functionality | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Fspecification.chatmode.md) |
| [Tech Debt Remediation Plan](chatmodes/tech_debt_remediation_plan.chatmode.md) | Generate technical debt remediation plans for code, tests, and documentation | [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect?url=vscode%3Achat-modes%2Finstall%3Furl%3Dhttps%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fgithub-copilot-assets-library%2Fmain%2Fchatmodes%2Ftech_debt_remediation_plan.chatmode.md) |

#### Custom Chat Modes in workspace usage

To add a custom chat mode in your repository:

1. Copy the chat mode file from the `chatmodes` folder in this repository to the `.github/chatmodes/` folder of your repository.
1. In Visual Studio Code, you can select the chat mode from the chat mode selector in the chat view.

    ![Chat mode selector in Visual Studio Code](images/select-custom-chat-mode.png)

> [!NOTE]
> You may need to restart Visual Studio Code to see the new chat mode in the chat mode selector. (Newer versions of Visual Studio Code will automatically detect new chat modes in the `.github/chatmodes/` folder).

### 🔌 MCP Servers

MCP Server configurations are found in the [`mcp/mcp.json`](mcp/mcp.json) file.

| Server Name | Description | Status |
| ----------- | ----------- | ------ |
| **microsoft.docs.mcp** | Provides access to Microsoft Docs via Model Context Protocol for documentation and examples | ✅ Available |
| **filesystem** | Provides file system access capabilities to Copilot for reading and writing files | ✅ Available |
| **playwright** | Enables web automation and testing capabilities through Playwright | ✅ Available |
| **github** | Integrates GitHub API functionality for repository operations and management | ✅ Available |
| **giphy** | Adds GIF search and integration capabilities through the Giphy API | ✅ Available |
| **ado** | Integrates Azure DevOps API for project management and CI/CD operations | ✅ Available |

#### MCP Servers in workspace usage

To add an MCP server in your repository:

1. Copy the server configuration from the `mcp.json` file in the `mcp` folder of this repository to the `.vscode/mcp.json` file in your repository.

> [!NOTE]
> You can also add MCP servers to your GitHub Repository for use by Coding Agents. See the [Extending Copilot coding agent with the Model Context Protocol (MCP)](https://docs.github.com/en/copilot/how-tos/agents/copilot-coding-agent/extending-copilot-coding-agent-with-mcp) documentation for more information.

For Visual Studio Code Insiders edition there is also a public website that lists MCP Servers that you can use in your workspace. You can find it at [https://code.visualstudio.com/insider/mcp](https://code.visualstudio.com/insider/mcp)
