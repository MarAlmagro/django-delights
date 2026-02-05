Create a structured development roadmap for Django Delights using Cursor's Task format. Follow the KISS principle (Keep It Simple, Stupid) to ensure clarity and focus.

## Task Details
- **Task description**: Build a complete Django web application for restaurant inventory, menus, menu items, purchases, user roles, and cost-based availability management, exactly as defined in the “Project_Decisions.md” document.
- **Technologies**: Django 5, Python 3.12+, Bootstrap, SQLite (dev), HTML templates, Django CBVs, Django Auth.
- **Main goals**: 
* Implement all models, views, URLs and templates defined in the "Project_Decisions.md" document
* Build functional staff/admin workflows (inventory, menu items, menus, purchases, users).
* Deliver a stable, test-covered Django application.

## Structure
Divide the development into 6 sequential phases. For Phase 1, focus on Project Setup & Core Models.
The 6 sequential phases are described in the "Roadmap.md" document

For each phase, include:
1. A brief introduction explaining the phase's purpose and goals (2-3 sentences)
2. 3-5 main tasks with clearly defined goals
3. Relevant subtasks under each main task

## Task Format Requirements
- Use Cursor's checkbox format:
  - Main tasks: `1. [ ] **Task Name**`
  - Subtasks: `   - [ ] Subtask description`
- For each main task:
  - Add priority tag: `[CRITICAL]`, `[HIGH]`, `[MEDIUM]`, or `[LOW]`
  - Include "Done when:" success criteria at the end of each main task
- Include any critical dependencies between tasks
- Avoid code snippets; focus on clear action items
- Keep task descriptions concise (max 1-2 lines per item)

## Example Format
```markdown
# Phase 1: [Phase Name]

Brief introduction explaining this phase's purpose and what we're trying to accomplish.

## Tasks

1. [ ] **[CRITICAL] Set up project repository and basic structure**
   - [ ] Initialize Git repository
   - [ ] Create README with project overview
   - [ ] Set up basic directory structure
   - [ ] Configure essential dotfiles
   - Done when: Repository is created with initial commit and proper documentation

2. [ ] **[HIGH] Configure development environment**
   - [ ] Install dependencies
   - [ ] Set up linting and formatting
   - Done when: Developers can run the project locally with proper tooling
```