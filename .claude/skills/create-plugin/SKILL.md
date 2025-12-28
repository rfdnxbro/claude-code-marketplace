---
name: creating-plugins
description: Creates Claude Code marketplace plugins with proper structure. Use when creating new plugins, adding commands, agents, hooks, or MCP servers to the marketplace.
---

# Creating Plugins

## Directory structure

```
plugins/[plugin-name]/
├── .claude-plugin/
│   └── plugin.json       # Required
├── commands/
│   └── [command-name].md
├── agents/
│   └── [agent-name].md
├── hooks/
│   └── hooks.json
├── .mcp.json
└── README.md
```

## Naming conventions

| Item | Rule | Example |
|------|------|---------|
| Plugin name | kebab-case | `my-awesome-plugin` |
| Command file | kebab-case.md | `review-code.md` |
| Agent file | kebab-case.md | `code-reviewer.md` |

## Workflow

Copy this checklist:

```
Plugin Creation:
- [ ] Step 1: Create plugin directory
- [ ] Step 2: Create plugin.json
- [ ] Step 3: Add components
- [ ] Step 4: Write README.md
- [ ] Step 5: Validate
```

**Step 1**: Create `plugins/[plugin-name]/` directory

**Step 2**: Create `.claude-plugin/plugin.json` with required `name` field

**Step 3**: Add needed components:
- `commands/` for slash commands
- `agents/` for sub-agents
- `hooks/hooks.json` for hooks
- `.mcp.json` for MCP servers

**Step 4**: Write `README.md` explaining the plugin

**Step 5**: Validate with `claude plugin validate ./plugins/[plugin-name]`

## Required fields

- `plugin.json`: `name` (kebab-case)
- Commands: `description` in frontmatter
- Agents: `name` and `description` in frontmatter
