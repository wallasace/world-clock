# AI Collaboration Progress Log

A personal, reusable log for tracking how I work with AI (Claude) across
projects — not a changelog of the code, but of *how the collaboration went*.
The goal is to look back later and see where I'm leaning on AI less, asking
sharper questions, or catching things myself before it does.

## How to use this template

Copy the **Entry template** section into a new project's repo (or append a
new entry here if it's a continuation of this one). Fill it in close to the
end of a work session, while it's fresh. Be honest rather than flattering —
the point is to see real trends over time, not to look good in retrospect.

Every few months, skim all your entries and answer the **Trend check**
questions at the bottom based on what you notice across them.

---

## Entry template

### [Date] — [Project name]

**Goal:** What were you building?

**Who decided what:**
- Decisions I made on my own:
- Decisions I asked Claude to make/recommend:
- Things Claude did that I didn't fully understand at the time:

**New to me this time:** Concepts, tools, or workflows you hadn't used
before (even small ones — a git command, a library, a debugging technique).

**Hardest moment:** What was the trickiest part, and what did *you*
contribute to solving it (not just what Claude did)?

**What I'd do differently / want to get better at:**

**Self-rating (1–5) — how much could I have done without AI this time?**
(1 = fully dependent, 5 = AI was mostly just faster hands)

---

## Entries

### 2026-09-08 — World Clock (KDE Plasma desktop app)

**Goal:** A minimalist desktop clock comparing a chosen country's time
against a home country's time, for KDE Plasma on Fedora.

**Who decided what:**
- Decisions I made on my own: overall concept and layout idea (rectangular
  UI, time on one side, country info on the other); chose standalone app
  over a native Plasma widget; picked the visual style direction (modern,
  minimalist, "bonito"); scoped each new feature into its own branch;
  decided GitHub repo visibility (public) and license (MIT); handled the
  two steps that needed my own credentials (`sudo dnf install gh`,
  `gh auth login`); decided to leave the first commit's message as-is
  rather than rewrite git history; drove the entire bug hunt by testing
  the real app and reporting exact symptoms.
- Decisions I asked Claude to make/recommend: tech stack (PySide6),
  color palette, exact spacing/margins, country list and their timezones,
  git commit message wording.
- Things Claude did that I didn't fully understand at the time: the
  QCompleter/editable-QComboBox search setup, and the specific Qt
  event-handling fixes (event filters, focus reasons, press-vs-release
  signal timing).

**New to me this time:** Seeing how a GUI bug that's invisible in a
"headless" test environment can still be root-caused through *precise
descriptions* of what I saw on screen ("aparece e some", "seta não
funcionou") rather than needing to read the code myself. Also: git
branches per feature, and that rewriting published git history is a
deliberate, riskier operation (not just a normal edit).

**Hardest moment:** The search-picker arrow silently failing. Claude
couldn't reproduce clicks/focus in its own sandbox, so it built ~10 small
throwaway test scripts and I ran each one, reporting back exactly what
happened. That back-and-forth is what actually isolated the three real
causes (window flags, flag/text coupling, click-vs-release timing) — none
of them were guessable from reading the code alone.

**What I'd do differently / want to get better at:** Try describing bugs
with a bit more structure up front (what I clicked, what I expected, what
happened) — it would've saved a couple of the diagnostic rounds. Also want
to get comfortable reading a `git diff` myself before asking "what
changed?".

**Self-rating (1–5) — how much could I have done without AI this time?** 2
— I directed scope, product decisions, and the entire debugging feedback
loop, but the Qt/PySide6 implementation and the actual bug diagnoses were
Claude's.

---

## Trend check (revisit periodically)

- Am I making more of the technical decisions over time, or still mostly
  approving suggestions?
- Are my bug reports getting more precise / needing fewer diagnostic
  rounds?
- Which concepts keep showing up as "new to me" — worth deliberately
  studying one?
- Is my self-rating trending up across similar-sized projects?
