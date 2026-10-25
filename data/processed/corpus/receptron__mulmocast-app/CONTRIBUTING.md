# Contributing to MulmoCast

Thank you for your interest in contributing to MulmoCast App! This guide will help you understand the project structure and development workflow.

## Project Overview

MulmoCast is an Electron application with a React frontend and Express backend. The application provides a modern desktop interface for managing multimedia casting projects.

## Technology Stack

- **Frontend**: Vue 3, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Node.js
- **Desktop**: Electron
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with shadcn/ui components

## Project Structure

```
mulmocast-app/
├── src/
│   ├── main/            # Backend Node.js
│   └── renderer/        # Frontend Vue application
│       ├── pages/       # Vue components
│       │   └── ui/      # shadcn/ui base components
│       ├── lib/         # Utilities and helpers
│       └── styles/      # CSS styles
```

## Development Setup

1. **Install dependencies**:
   ```bash
   yarn install
   ```

2. **Start development server**:
   ```bash
   yarn start
   ```

3. **Run linting**:
   ```bash
   yarn lint
   ```

4. **Format code**:
   ```bash
   yarn format
   ```

## Adding shadcn-vue Components

To add new [shadcn-vue](https://www.shadcn-vue.com/) components to the project:

```bash
npx shadcn-vue@latest add [component-name]
```

For example:
```bash
npx shadcn-vue@latest add button
npx shadcn-vue@latest add card
npx shadcn-vue@latest add dialog
```
