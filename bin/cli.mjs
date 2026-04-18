#!/usr/bin/env node
// Research Pipeline installer for Claude Code.
// Zero-dep Node CLI. Copies skills + agents from this package into ~/.claude/.
//
// Usage:
//   npx github:TorpedoD/claude-researcher add           # install everything
//   npx github:TorpedoD/claude-researcher add <name>    # install one skill or agent
//   npx github:TorpedoD/claude-researcher list          # list available + installed
//   npx github:TorpedoD/claude-researcher remove <name> # remove a skill or agent
//
// Flags:
//   --force / -f   overwrite existing without backup
//   --dry-run      print actions without writing
//   --no-backup    skip .bak backup when overwriting
//   --help / -h    show help

import { readdirSync, existsSync, mkdirSync, cpSync, rmSync, renameSync, statSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PKG_ROOT = resolve(__dirname, "..");
const SRC_SKILLS = join(PKG_ROOT, "skills");
const SRC_AGENTS = join(PKG_ROOT, "agents");

const CLAUDE_HOME = process.env.CLAUDE_HOME || join(homedir(), ".claude");
const DST_SKILLS = join(CLAUDE_HOME, "skills");
const DST_AGENTS = join(CLAUDE_HOME, "agents");

// --- pretty printing (ANSI, falls back to plain if NO_COLOR) -----------------
const useColor = !process.env.NO_COLOR && process.stdout.isTTY;
const c = (code, s) => (useColor ? `\x1b[${code}m${s}\x1b[0m` : s);
const bold = (s) => c("1", s);
const dim = (s) => c("2", s);
const green = (s) => c("32", s);
const yellow = (s) => c("33", s);
const red = (s) => c("31", s);
const cyan = (s) => c("36", s);

// --- arg parsing -------------------------------------------------------------
const argv = process.argv.slice(2);
const flags = new Set();
const positional = [];
for (const a of argv) {
  if (a.startsWith("--") || /^-[a-zA-Z]$/.test(a)) flags.add(a);
  else positional.push(a);
}
const has = (...names) => names.some((n) => flags.has(n));
const DRY = has("--dry-run");
const FORCE = has("--force", "-f");
const NO_BACKUP = has("--no-backup");
const HELP = has("--help", "-h");

const subcommand = positional[0];
const target = positional[1];

// --- inventory ---------------------------------------------------------------
function listSkills() {
  if (!existsSync(SRC_SKILLS)) return [];
  return readdirSync(SRC_SKILLS, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);
}

function listAgents() {
  if (!existsSync(SRC_AGENTS)) return [];
  return readdirSync(SRC_AGENTS, { withFileTypes: true })
    .filter((d) => d.isFile() && d.name.endsWith(".md"))
    .map((d) => d.name.replace(/\.md$/, ""));
}

function isInstalledSkill(name) {
  return existsSync(join(DST_SKILLS, name));
}
function isInstalledAgent(name) {
  return existsSync(join(DST_AGENTS, `${name}.md`));
}

// --- filesystem ops ----------------------------------------------------------
function ensureDir(p) {
  if (DRY) return;
  mkdirSync(p, { recursive: true });
}

function backup(path) {
  if (DRY) return;
  const bak = `${path}.bak`;
  if (existsSync(bak)) rmSync(bak, { recursive: true, force: true });
  renameSync(path, bak);
}

function installSkill(name) {
  const src = join(SRC_SKILLS, name);
  if (!existsSync(src)) {
    console.log(red(`  ✗ skill not found: ${name}`));
    return false;
  }
  const dst = join(DST_SKILLS, name);
  if (existsSync(dst)) {
    if (FORCE && !NO_BACKUP) {
      console.log(yellow(`  ⟳ ${name} exists — backing up to ${name}.bak`));
      backup(dst);
    } else if (FORCE && NO_BACKUP) {
      console.log(yellow(`  ⟳ ${name} exists — overwriting`));
      if (!DRY) rmSync(dst, { recursive: true, force: true });
    } else {
      console.log(yellow(`  ⟳ ${name} exists — backing up to ${name}.bak (use --force to skip prompt)`));
      backup(dst);
    }
  }
  if (!DRY) cpSync(src, dst, { recursive: true });
  console.log(green(`  ✓ skill: ${name}`));
  return true;
}

function installAgent(name) {
  const src = join(SRC_AGENTS, `${name}.md`);
  if (!existsSync(src)) {
    console.log(red(`  ✗ agent not found: ${name}`));
    return false;
  }
  const dst = join(DST_AGENTS, `${name}.md`);
  if (!DRY) cpSync(src, dst);
  console.log(green(`  ✓ agent: ${name}`));
  return true;
}

function removeSkill(name) {
  const dst = join(DST_SKILLS, name);
  if (!existsSync(dst)) {
    console.log(dim(`  - skill not installed: ${name}`));
    return false;
  }
  if (!DRY) rmSync(dst, { recursive: true, force: true });
  console.log(green(`  ✓ removed skill: ${name}`));
  return true;
}

function removeAgent(name) {
  const dst = join(DST_AGENTS, `${name}.md`);
  if (!existsSync(dst)) {
    console.log(dim(`  - agent not installed: ${name}`));
    return false;
  }
  if (!DRY) rmSync(dst, { force: true });
  console.log(green(`  ✓ removed agent: ${name}`));
  return true;
}

// --- commands ----------------------------------------------------------------
function cmdAdd() {
  const skills = listSkills();
  const agents = listAgents();

  console.log(bold("→ Research Pipeline installer"));
  console.log(dim(`  source: ${PKG_ROOT}`));
  console.log(dim(`  target: ${CLAUDE_HOME}`));
  if (DRY) console.log(yellow("  (dry run — no files will be written)"));
  console.log();

  ensureDir(DST_SKILLS);
  ensureDir(DST_AGENTS);

  if (target) {
    // specific thing
    const asSkill = skills.includes(target);
    const asAgent = agents.includes(target);
    if (!asSkill && !asAgent) {
      console.log(red(`Unknown skill or agent: ${target}`));
      console.log(dim("Run with `list` to see what's available."));
      process.exit(1);
    }
    if (asSkill) installSkill(target);
    if (asAgent) installAgent(target);
  } else {
    console.log(bold("Skills"));
    for (const s of skills) installSkill(s);
    console.log();
    console.log(bold("Agents"));
    for (const a of agents) installAgent(a);
  }

  console.log();
  console.log(green("✓ Done."));
  console.log();
  console.log(bold("Next steps:"));
  console.log(`  1. Install runtime prerequisites (see README):`);
  console.log(dim(`       pipx install crawl4ai==0.8.6 && crawl4ai-setup`));
  console.log(dim(`       pipx install docling==2.86.0`));
  console.log(dim(`       brew install --cask quarto`));
  console.log(`  2. Install Graphify: ${cyan("https://github.com/safishamsi/graphify")}`);
  console.log(`  3. Open Claude Code and run: ${cyan('/research "your topic"')}`);
}

function cmdList() {
  const skills = listSkills();
  const agents = listAgents();
  console.log(bold("Skills") + dim(`  (source → ~/.claude/skills)`));
  for (const s of skills) {
    const status = isInstalledSkill(s) ? green("installed") : dim("not installed");
    console.log(`  ${s}  ${status}`);
  }
  console.log();
  console.log(bold("Agents") + dim(`  (source → ~/.claude/agents)`));
  for (const a of agents) {
    const status = isInstalledAgent(a) ? green("installed") : dim("not installed");
    console.log(`  ${a}  ${status}`);
  }
}

function cmdRemove() {
  if (!target) {
    console.log(red("Usage: remove <name>"));
    process.exit(1);
  }
  const skills = listSkills();
  const agents = listAgents();
  const asSkill = skills.includes(target);
  const asAgent = agents.includes(target);
  if (!asSkill && !asAgent) {
    console.log(red(`Unknown skill or agent: ${target}`));
    process.exit(1);
  }
  if (asSkill) removeSkill(target);
  if (asAgent) removeAgent(target);
}

function cmdHelp() {
  console.log(`${bold("claude-researcher")} — Claude Code skills + agents installer
${dim("repo: https://github.com/TorpedoD/claude-researcher")}

${bold("Usage")}
  npx github:TorpedoD/claude-researcher ${cyan("add")}              install all skills + agents
  npx github:TorpedoD/claude-researcher ${cyan("add <name>")}       install one
  npx github:TorpedoD/claude-researcher ${cyan("list")}             show available / installed
  npx github:TorpedoD/claude-researcher ${cyan("remove <name>")}    uninstall one

${bold("Flags")}
  --force, -f     overwrite existing (still backs up to .bak unless --no-backup)
  --no-backup     skip .bak backup when overwriting
  --dry-run       print what would happen without touching the filesystem
  --help, -h      show this message

${bold("Environment")}
  CLAUDE_HOME     override target directory (default: ~/.claude)
  NO_COLOR        disable ANSI colors

${bold("Examples")}
  npx github:TorpedoD/claude-researcher add
  npx github:TorpedoD/claude-researcher add research-orchestrator
  npx github:TorpedoD/claude-researcher list
  CLAUDE_HOME=/tmp/claude-test npx github:TorpedoD/claude-researcher add --dry-run
`);
}

// --- entry -------------------------------------------------------------------
if (HELP || !subcommand) {
  cmdHelp();
  process.exit(subcommand ? 0 : HELP ? 0 : 0);
}

try {
  switch (subcommand) {
    case "add":
    case "install":
      cmdAdd();
      break;
    case "list":
    case "ls":
      cmdList();
      break;
    case "remove":
    case "uninstall":
    case "rm":
      cmdRemove();
      break;
    case "help":
      cmdHelp();
      break;
    default:
      console.log(red(`Unknown command: ${subcommand}`));
      console.log();
      cmdHelp();
      process.exit(1);
  }
} catch (err) {
  console.error(red("✗ Error:"), err.message);
  if (process.env.DEBUG) console.error(err.stack);
  process.exit(1);
}
