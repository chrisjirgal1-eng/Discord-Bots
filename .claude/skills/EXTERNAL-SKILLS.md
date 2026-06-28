# External skills (installed, not vendored into git)

These third-party skill packs are installed locally under `.claude/skills/` so they are live in this
project, but their content is **gitignored** (it is large third-party material with its own repos and
licenses). This file is the record + reinstall guide. Re-run the clone+copy below on a fresh machine.

| Skill | Source repo | What it gives | License |
|---|---|---|---|
| `three-best-practices` | github.com/emalorenzo/three-agent-skills | 120+ Three.js rules: TSL node shaders, PBR lighting/shadows, post-processing (selective bloom/AO/DoF), instancing, draw-call + memory optimization | MIT |
| `r3f-best-practices` | github.com/emalorenzo/three-agent-skills | React Three Fiber + drei/postprocessing/rapier best practices | MIT |
| `ui-ux-pro-max` | github.com/nextlevelbuilder/ui-ux-pro-max-skill | Design intelligence: 50+ styles, 161 palettes, 57 font pairings, 99 UX rules (self-contained data/ + scripts/) | see repo |
| `design`, `design-system`, `ui-styling` | github.com/nextlevelbuilder/ui-ux-pro-max-skill | Design workflow, design-system + styling (glassmorphism, dark mode, tokens) | see repo |

## Reinstall

```bash
TMP=$(mktemp -d)
git clone --depth 1 https://github.com/emalorenzo/three-agent-skills.git "$TMP/tas"
git clone --depth 1 https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git "$TMP/uux"
cp -r "$TMP/tas/skills/three-best-practices" "$TMP/tas/skills/r3f-best-practices" .claude/skills/
for s in ui-ux-pro-max design design-system ui-styling; do cp -r "$TMP/uux/.claude/skills/$s" .claude/skills/; done
```

## Reviewed but NOT installed as skills
- **github.com/openscad/openscad** - the OpenSCAD *application* (procedural CAD program), not a Claude
  skill. If you want procedural/generative 3D models, install the OpenSCAD app and I can write `.scad`
  scripts; nothing to copy into `.claude/skills/`.
- **github.com/majiayu000/claude-skill-registry** - a registry/catalog of skills (crawler + manifest),
  not runnable skills itself.
- **github.com/Jeffallan/claude-skills** - 66 general skills (game-developer, architecture, etc.);
  not 3D-specific. Say the word and I will install the relevant ones.
- **github.com/MonumentalSystems/Atlas-Agent-Teams** - agent-team definitions (161 md), a different
  mechanism than skills.
