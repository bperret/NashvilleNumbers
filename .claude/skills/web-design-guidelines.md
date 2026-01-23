# Web Design Guidelines

> source: https://github.com/vercel-labs/agent-skills
> skill: web-design-guidelines
> version: 1.0.0
> author: Vercel

## Description

A tool for reviewing UI code against Web Interface Guidelines. This skill audits files for compliance with web interface best practices by fetching the latest guidelines and comparing provided code against those standards.

## Activation Triggers

Use this skill when the user requests:
- "review my UI"
- "check accessibility"
- "audit design"
- "review UX"
- "check my site against best practices"
- Any request to evaluate UI/frontend code quality

## Workflow

1. **Fetch fresh guidelines** before each review from:
   ```
   https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
   ```

2. **Identify target files**: Use the files or patterns specified by the user. If none provided, prompt the user to specify which files to review.

3. **Read the specified files**: Load the content of all files that need to be audited.

4. **Evaluate against all rules**: Compare the code against every rule in the fetched guidelines.

5. **Report findings**: Output compliance issues tersely in `file:line` format.

## Output Format

Report findings concisely using the format:
```
path/to/file.tsx:42 - Issue description
path/to/file.tsx:58 - Another issue
```

## Guidelines Coverage

The Web Interface Guidelines include 100+ rules covering:
- Accessibility patterns
- Focus states
- Forms
- Animations
- Typography
- Images
- Localization
- Performance
- UX best practices
