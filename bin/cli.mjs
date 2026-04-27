#!/usr/bin/env node
// Research Pipeline installer for Claude Code.
// Zero-dep Node CLI. Copies skills + agents from this package into ~/.claude/.
//
// Usage:
//   npx github:TorpedoD/claude-researcher install           # install everything
//   npx github:TorpedoD/claude-researcher update            # replace installed package files
//   npx github:TorpedoD/claude-researcher uninstall         # remove package files
//   npx github:TorpedoD/claude-researcher list              # list available + installed
//
// Flags:
//   --dry-run       print actions without writing
//   --help / -h     show help

import { readdirSync, existsSync, mkdirSync, cpSync, rmSync } from "node:fs";
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

function inventory() {
  return [
    ...listSkills().map((name) => ({
      kind: "skill",
      name,
      src: join(SRC_SKILLS, name),
      dst: join(DST_SKILLS, name),
      parent: DST_SKILLS,
      recursive: true,
    })),
    ...listAgents().map((name) => ({
      kind: "agent",
      name,
      src: join(SRC_AGENTS, `${name}.md`),
      dst: join(DST_AGENTS, `${name}.md`),
      parent: DST_AGENTS,
      recursive: false,
    })),
  ];
}

function selectItems(name) {
  const items = inventory();
  if (!name) return items;
  return items.filter((item) => item.name === name);
}

function requireItems(name) {
  const items = selectItems(name);
  if (name && items.length === 0) {
    console.log(red(`Unknown skill or agent: ${name}`));
    console.log(dim("Run with `list` to see what's available."));
    process.exit(1);
  }
  return items;
}

// --- filesystem ops ----------------------------------------------------------
function ensureDir(p) {
  if (DRY) return;
  mkdirSync(p, { recursive: true });
}

function copyItem(item, action) {
  const exists = existsSync(item.dst);
  ensureDir(item.parent);
  if (!DRY && exists) rmSync(item.dst, { recursive: item.recursive, force: true });
  if (!DRY) cpSync(item.src, item.dst, { recursive: item.recursive });

  const verb = action === "update" && exists ? "replace" : "install";
  const label = DRY ? `would ${verb}` : verb === "replace" ? "replaced" : "installed";
  console.log(green(`  ✓ ${label} ${item.kind}: ${item.name}`));
  return true;
}

function removeItem(item) {
  if (!existsSync(item.dst)) {
    console.log(dim(`  - ${item.kind} not installed: ${item.name}`));
    return false;
  }
  if (!DRY) rmSync(item.dst, { recursive: item.recursive, force: true });
  console.log(green(`  ✓ ${DRY ? "would remove" : "removed"} ${item.kind}: ${item.name}`));
  return true;
}

function printHeader(title) {
  console.log(bold(`→ ${title}`));
  console.log(dim(`  source: ${PKG_ROOT}`));
  console.log(dim(`  target: ${CLAUDE_HOME}`));
  if (DRY) console.log(yellow("  (dry run — no files will be written)"));
  console.log();
}

function printNextSteps() {
  console.log();
  console.log(green("✓ Done."));
  console.log();
  console.log(bold("Next steps:"));
  console.log(`  1. Install runtime prerequisites (see README):`);
  console.log(dim(`       pipx install crawl4ai==0.8.6 && crawl4ai-setup`));
  console.log(dim(`       pipx install docling==2.86.0`));
  console.log(dim(`       pip install graphifyy && graphify install`));
  console.log(dim(`       brew install quarto`));
  console.log(`  2. Open Claude Code and run: ${cyan("/research")}`);
}

function printGrouped(items, callback) {
  const skills = items.filter((item) => item.kind === "skill");
  const agents = items.filter((item) => item.kind === "agent");

  if (skills.length > 0) {
    console.log(bold("Skills"));
    for (const item of skills) callback(item);
  }
  if (skills.length > 0 && agents.length > 0) console.log();
  if (agents.length > 0) {
    console.log(bold("Agents"));
    for (const item of agents) callback(item);
  }
}

// --- commands ----------------------------------------------------------------
function cmdInstall() {
  const items = requireItems(target);
  printHeader("Research Pipeline installer");
  printGrouped(items, (item) => copyItem(item, "install"));
  printNextSteps();
}

function cmdUpdate() {
  const items = requireItems(target);
  printHeader("Research Pipeline updater");
  printGrouped(items, (item) => copyItem(item, "update"));
  console.log();
  console.log(green("✓ Done."));
}

function cmdList() {
  const items = inventory();
  const skills = items.filter((item) => item.kind === "skill");
  const agents = items.filter((item) => item.kind === "agent");
  console.log(bold("Skills") + dim(`  (source → ~/.claude/skills)`));
  for (const item of skills) {
    const status = existsSync(item.dst) ? green("installed") : dim("not installed");
    console.log(`  ${item.name}  ${status}`);
  }
  console.log();
  console.log(bold("Agents") + dim(`  (source → ~/.claude/agents)`));
  for (const item of agents) {
    const status = existsSync(item.dst) ? green("installed") : dim("not installed");
    console.log(`  ${item.name}  ${status}`);
  }
}

function cmdUninstall() {
  const items = requireItems(target);
  printHeader("Research Pipeline uninstaller");
  printGrouped(items, removeItem);
  console.log();
  console.log(green("✓ Done."));
}

function cmdHelp() {
  console.log(`${bold("claude-researcher")} — Claude Code skills + agents installer
${dim("repo: https://github.com/TorpedoD/claude-researcher")}

${bold("Usage")}
  npx github:TorpedoD/claude-researcher ${cyan("install")}          install all skills + agents
  npx github:TorpedoD/claude-researcher ${cyan("install <name>")}   install one matching skill and/or agent
  npx github:TorpedoD/claude-researcher ${cyan("update")}           replace all packaged skills + agents
  npx github:TorpedoD/claude-researcher ${cyan("update <name>")}    replace one matching skill and/or agent
  npx github:TorpedoD/claude-researcher ${cyan("uninstall")}        remove all packaged skills + agents
  npx github:TorpedoD/claude-researcher ${cyan("uninstall <name>")} remove one matching skill and/or agent
  npx github:TorpedoD/claude-researcher ${cyan("list")}             show available / installed

${bold("Flags")}
  --dry-run       print what would happen without touching the filesystem
  --help, -h      show this message

${bold("Environment")}
  CLAUDE_HOME     override target directory (default: ~/.claude)
  NO_COLOR        disable ANSI colors

${bold("Examples")}
  npx github:TorpedoD/claude-researcher install
  npx github:TorpedoD/claude-researcher update research
  npx github:TorpedoD/claude-researcher uninstall research-format
  npx github:TorpedoD/claude-researcher list
  CLAUDE_HOME=/tmp/claude-test npx github:TorpedoD/claude-researcher install --dry-run
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
      cmdInstall();
      break;
    case "update":
      cmdUpdate();
      break;
    case "list":
    case "ls":
      cmdList();
      break;
    case "remove":
    case "uninstall":
    case "rm":
      cmdUninstall();
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
