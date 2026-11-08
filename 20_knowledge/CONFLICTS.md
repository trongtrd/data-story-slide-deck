# Cross-Source Conflicts Registry (`20_knowledge/CONFLICTS.md`)

When a secondary source (`SRC-SEC-*`) contradicts a primary *storytelling with data* (`SRC-SWD-*`) principle, agents must **not** silently override SWD. Instead, log the conflict here with status `open`, present the trade-offs to the user, and once the user rules, update the status to `ruled` and record the decision in `00_admin/DECISIONS.md` (D-003).

---

## Template

```markdown
### CONF-NNN — <Topic Title>
- **Status:** open | ruled (see D-MMM)
- **Stage:** CTX | STR | TTL | VIS | DSN | AI | REV | PRS
- **Primary Position (SWD):** <Summary + SRC-SWD-* citation>
- **Secondary Position:** <Summary + SRC-SEC-* citation>
- **Agent Analysis & Recommendation:** <When do they conflict, or can they be reconciled by context?>
- **User Ruling:** <Pending, or summary of ruling + link to D-MMM>
```

---

## Logged Conflicts

### CONF-001 — Dropping the Slide Title to Enlarge a Chart or Photo
- **Status:** ruled (see D-026)
- **Stage:** TTL
- **Primary Position (SWD):** Every data slide carries a point-of-view takeaway title that tells the audience what to see (`PRIN-TTL-001`, `PRIN-TTL-002`; `SRC-SWD-000`, `SRC-SWD-010`).
- **Secondary Position:** Slide titles are optional and may be removed when they make a chart or photo too small (`SRC-SEC-005`).
- **Agent Analysis & Recommendation:** Keep SWD. The secondary example uses topic titles, which carry little value, so dropping them costs little; a takeaway title carries the slide's message. When space is tight, shorten the title (`PAT-TTL-001`) or split the slide rather than drop it. The idea can still apply to a full-bleed photo slide with no data, which our spec does not build.
- **User Ruling:** Keep SWD. Data slides always carry a takeaway title; when space is tight, shorten the title or split the slide (`D-026`).

### CONF-002 — Pie Charts With Up to Five or Six Slices, and Radar Charts
- **Status:** ruled (see D-026)
- **Stage:** VIS
- **Primary Position (SWD):** Default to six workhorse charts; pie or donut charts with more than two slices and radar charts are banned for general audiences (`PRIN-VIS-002`, `ANTI-VIS-002`; `SRC-SWD-004`).
- **Secondary Position:** Pie charts are fine with up to five or six slices ordered largest first from 12 o'clock; radar charts suit multi-attribute profiles; only donuts are discouraged (`SRC-SEC-005`).
- **Agent Analysis & Recommendation:** Keep SWD. Angles and areas are judged less accurately than lengths, and a sorted horizontal bar shows the same part-to-whole data more precisely. Keep the secondary ordering advice (largest first, from 12 o'clock) only for the two-slice exception that `PRIN-VIS-002` still allows.
- **User Ruling:** Keep the ban. Keep only the ordering advice for the two-slice exception; radar charts stay limited to the existing domain-specialist override (`D-026`).

### CONF-003 — A Universal 28 pt Minimum Font Size
- **Status:** ruled (see D-025)
- **Stage:** DSN
- **Primary Position (SWD):** Our SWD sources set no numeric font floor; text density follows `delivery_mode` (`PRIN-PRS-001`), and decluttering must keep axis labels and source notes (`PRIN-DSN-002`).
- **Secondary Position:** All slide text should be at least 28 pt (`SRC-SEC-005`, written for live academic talks).
- **Agent Analysis & Recommendation:** A single 28 pt floor would strip the labels that make charts verifiable in standalone decks. The real gap is that projected decks currently use 8.5–9.5 pt labels. Replace the single floor with floors by text role and delivery mode (`PRIN-DSN-005`).
- **User Ruling:** The owner rejected adopting the 28 pt rule wholesale; floors depend on role and delivery mode, with thresholds set when `PRIN-DSN-005` is reviewed (`D-025`).

### CONF-004 — WCAG 3:1 for Every Data Mark vs. SWD's Quiet Greyscale Context
- **Status:** ruled (see D-028)
- **Stage:** DSN
- **Primary Position (SWD):** Context series recede in light-to-medium grey so the single accent wins; the greyscale baseline is deliberately low-contrast (`PRIN-DSN-004`, `ANTI-DSN-001`; `SRC-SWD-008`).
- **Secondary Position:** Graphic elements should reach 3:1 against adjacent colours (WCAG, as discussed in `SRC-SEC-006` §09). The author also notes the rule is hard to meet for tints, was not written for charts, and is applied with judgment by most organizations.
- **Agent Analysis & Recommendation:** Reconcile by role and delivery mode (`PRIN-DSN-007` option A):
  - focal marks always ≥ 3:1;
  - context grey ≥ 2.4:1 when read on screen, ≥ 3.0:1 when projected;
  - tier-2 tint ≥ 1.6:1 on screen, ≥ 2.0:1 projected.

  Today the benchmarks use grey `#A6A6A6` (2.43:1) and tints of 1.63–2.08:1, which pass standalone floors but not live ones.
- **User Ruling:** Option A. Focal marks ≥ 3:1 everywhere; context grey ≥ 2.4:1 standalone and ≥ 3.0:1 live/hybrid; tier-2 tint ≥ 1.6:1 standalone and ≥ 2.0:1 live/hybrid (`D-028`).

### CONF-005 — Confidence Intervals on Presentation Charts vs. SWD Decluttering
- **Status:** ruled (see D-041)
- **Stage:** VIS
- **Primary Position (SWD):** Remove every element that does not help the main message; one clean view per point, grey context plus one accent (`PRIN-DSN-002`, `PRIN-DSN-004`; `SRC-SWD-008`). SWD does not ask for interval whiskers on slides.
- **Secondary Position:** Model estimates need their uncertainty to be read honestly, especially by audiences who assess inference (proposed `PRIN-VIS-006`, from the `D-040` test evidence; candidate source `SRC-SEC-004`).
- **Agent Analysis & Recommendation:** Reconcile by audience: show 95% intervals for `model_estimate` panels by default, as thin muted whiskers that do not compete with the accent; allow omission with a recorded `uncertainty_omitted_reason` for non-technical audiences when every shown estimate is clearly significant. Accept `PRIN-VIS-006` on that basis.
- **User Ruling:** Default on: 95% intervals as thin muted whiskers on `model_estimate` panels; omit only with `uncertainty_omitted_reason`. `PRIN-VIS-006` accepted (`D-041`).

> `CONF-006` is not used: it was proposed in `50_evals/reports/2026-10-30_p7-explorable-deck-review-proposal.md` (reveal frequency) and not logged (`D-048`). Numbering continues at `CONF-007` to keep that reference unambiguous.

### CONF-007 — Unusual Chart Types for Attention or Variety
- **Status:** ruled (see D-053)
- **Stage:** VIS
- **Primary Position (SWD):** Choose the familiar form unless a less common one shows something the familiar form cannot; never choose a form for aesthetic or personal reasons; every unfamiliar form must be taught (built up live, or annotated when read alone) or replaced by a simpler one (`PRIN-VIS-002`, `ANTI-VIS-002`; `SRC-SWD-004`, `SRC-SWD-011` §03, §04, §14, §20).
- **Secondary Position:** Unusual forms (stream graph, arrow plot) can earn attention by looking different, act as a stronger visual metaphor, and break the monotony of a report with many line charts (`SRC-SEC-008` #7, #9 and its "exciting chart types" box). The same article also says familiar charts make comparison easiest.
- **Agent Analysis & Recommendation:** Keep SWD. Novelty or variety is not a valid reason on its own; our users present evidence to decision-makers, where decoding cost is paid by the audience. The secondary point that survives is narrower and already in SWD: once a less common form is justified and taught, reuse it across parallel slides (`PAT-VIS-001`). Stream graphs stay out; the arrow plot's job is covered by the connected dot plot (`SRC-SWD-011` §08) under the conditions proposed in the 2026-10-30 chart-selection report.
- **User Ruling:** Keep SWD: novelty, variety or attention is not a reason to choose a form; a justified, taught form may be reused across parallel slides (`D-053`).

### CONF-008 — Area Charts for Composition Over Time
- **Status:** ruled (see D-052)
- **Stage:** VIS
- **Primary Position (SWD):** Area graphs are rarely the best choice: overlapping fills hide data, readers cannot tell stacked from overlapping baselines, and irregular areas are nearly impossible to compare. Narrow uses remain: the gap between exactly two series or between a series and 100 %, single-series small-multiple panels, or one dominant part (`SRC-SWD-011` §01). For composition at a few time points, stacked or 100 % stacked bars work (`SRC-SWD-011` §19). Area charts are outside the workhorse list (`PRIN-VIS-002`).
- **Secondary Position:** Area charts are a good, intuitive way to show how a total's internal breakdown changed over time, for example an energy mix (`SRC-SEC-008` #3). `SRC-SEC-009` lists area under change over time with "use with care", noting that the total reads well and the components poorly.
- **Agent Analysis & Recommendation:** Keep SWD; do not add an area chart family now. Route composition-over-time messages to: (a) 100 % stacked bars for a few time points, with the focal segment on a baseline; (b) small-multiple lines for many time points; (c) a line of the focal share when one component is the story. Revisit only for the SWD-endorsed gap shading between two lines, as an annotation on `line_chart`, after milestone B.
- **User Ruling:** Keep SWD. Area is allowed only for SWD's narrow uses (shaded gap between two series, a series against 100 %, single-series small-multiple panels); no stacked area (`D-052`).

### CONF-009 — Line + Column (Dual-Axis) Charts for an Amount and a Rate
- **Status:** ruled (see D-051)
- **Stage:** VIS
- **Primary Position (SWD):** Dual-axis charts are banned for general audiences; each question gets its own view (`PRIN-VIS-002` testable check, `PRIN-VIS-003`, `ANTI-VIS-001`; `SRC-SWD-004`, `SRC-SWD-009`).
- **Secondary Position:** A column series for an amount with a line for a rate is a good way to show their relationship, under correlation and change over time (`SRC-SEC-009`). Its own reading list links warnings about dual axes and spurious correlation.
- **Agent Analysis & Recommendation:** Keep SWD. Two value axes let the designer make any two series appear to track each other by choosing the scales, and readers often assume causation (a point `SRC-SEC-009` itself makes for correlation). Use two vertically aligned panels sharing the time axis (`PAT-DSN-001` two-sided or stacked layout), or plot the rate alone when it carries the message.
- **User Ruling:** Keep SWD: no dual-axis charts; use two aligned panels (`D-051`).

### CONF-010 — Topic Titles, and Titles That Introduce Rather Than Conclude
- **Status:** ruled (see D-062)
- **Stage:** TTL
- **Primary Position (SWD):** Every data slide carries a takeaway title that states the point the audience should see (`PRIN-TTL-001`, `PRIN-TTL-002`, `D-026`; `SRC-SWD-000`, `SRC-SWD-010`). The punchline may be withheld until the evidence lands, but only by deliberate design (`PAT-STR-001`).
- **Secondary Position:** A deck may use short topic titles ("Market Research", "Team Structure") or short action titles, in one grammar throughout; titles should open a slide rather than deliver its conclusion (`SRC-SEC-011` §03, `claude-slides` skill in `JimLiu/baoyu-design`).
- **Agent Analysis & Recommendation:** Keep SWD. Topic titles move the message into the speaker's voice, so a standalone or forwarded deck loses it. The secondary source's real target is formulaic drama ("not X — Y" constructions), which a lint can catch without giving up takeaway titles (proposal R3). Its "one grammar throughout" point already holds for our takeaway titles.
- **User Ruling:** Keep SWD takeaway titles; the formula-drama lint (R3) is adopted instead (`D-062`).

### CONF-011 — Marking Many Outlier Cells in a Large Table
- **Status:** ruled (see D-073)
- **Stage:** VIS
- **Primary Position (SWD):** Emphasis is spent sparingly: one focal element, everything else quiet; a table carries one row, one column or at most three cells in the focal colour (`PRIN-DSN-004`, `PRIN-DSN-008`, `PAT-VIS-006`; `SRC-SWD-008`, `SRC-SWD-011` §07).
- **Secondary Position:** In a large table (for example 20 rows by 10 years) mark every outlier value in bold, shade or colour so readers can find them, in the example all the negative values (`SRC-SEC-013` p.158-159, guideline 8).
- **Agent Analysis & Recommendation:** The two agree on purpose (guide the eye) and differ on count. Keep the SWD budget on main-deck tables, where a live audience reads while listening. Where marking many cells is the message, the diverging heatmap (`D-068`) already encodes "below zero" as one rule rather than many marks. The example's red-on-white negatives also clash with `PRIN-DSN-004` (accessible focus colour), which the source itself warns about on p.170. Recommend no change to the budget.
- **User Ruling:** Keep the SWD budget: one row, one column or at most three cells; a large table does not earn more. The diverging heatmap carries "below zero" as one rule (`D-073`).

### CONF-012 — Answer First (Executive Summary on Slide 2) vs. Evidence Before Indictment
- **Status:** ruled (see D-075)
- **Stage:** STR
- **Primary Position (SWD):** Order the deck on a narrative arc that builds tension before the resolution; with skeptics or policy owners in the room, do not state the overarching indictment of the status quo on slide 1 or 2, land it after the evidence (`PRIN-STR-003`, `PAT-STR-001`; `SRC-SWD-003`). `PAT-STR-001` already allows a bottom-line-up-front sequence when there is no resistance and the audience prefers it.
- **Secondary Position:** Put the main conclusion first: a title slide, then an executive summary with findings, recommendation and next steps, then the grouped evidence (`SRC-SEC-014` §Pyramid Principle, §Executive Summary).
- **Agent Analysis & Recommendation:** The two can be reconciled by context, which the brief already records (`delivery_mode`, `resistance_assessment`, skeptics). Recommend an optional executive-summary slide: on by default for a `standalone` or `hybrid` pre-read with no mapped resistance; off by default for a live talk; when skeptics are mapped, the summary states the question, the scope and the recommended action but leaves the indictment of the status quo to `falling_action`. Its title is a claim, never "Executive summary" (`CONF-010`). SWD stays the default order.
- **User Ruling:** Adapt: an optional executive summary after the title slide, on by default for a standalone or hybrid pre-read with no mapped resistance, off by default for live; with skeptics it leaves the indictment to `falling_action`; title is a claim (`D-075`).

### CONF-013 — Side-Banner Titles and Icons Beside Text
- **Status:** ruled (see D-075)
- **Stage:** DSN
- **Primary Position (SWD):** The takeaway title sits at the top left, where the Z scan starts (`PRIN-DSN-001`); every element earns its place, and decoration that carries no data is removed (`ANTI-DSN-002`, `PRIN-DSN-002`; `SRC-SWD-005`, `SRC-SWD-006`).
- **Secondary Position:** A title may sit in a coloured banner covering a third of the slide beside an infographic; icons beside text items aid recall and break up text (`SRC-SEC-014` §Infographics and Text, §Text and Icons).
- **Agent Analysis & Recommendation:** Keep SWD. The banner moves the title out of the reading start and spends the accent colour on a frame rather than on data; icons add a second visual vocabulary that the audience must decode. No change recommended.
- **User Ruling:** Keep SWD: title at the top left, no side banner, no icons beside text (`D-075`).

### CONF-014 — Closing Slide With Three to Five Points
- **Status:** ruled (see D-075)
- **Stage:** STR
- **Primary Position (SWD):** The last main-deck slide restates the Big Idea and the primary action with at most three evidence points already shown (`PAT-STR-003`; `SRC-SWD-003`, `SRC-SWD-010`).
- **Secondary Position:** Close with three to five concise points, then prioritised actions and an implementation outline (`SRC-SEC-014` §Conclusion Slides).
- **Agent Analysis & Recommendation:** Keep the cap of three evidence points. Implementation steps already fit as step cards under the action (`statement_or_transition`), so the secondary advice is covered without raising the count.
- **User Ruling:** Keep SWD: at most three evidence points on the closing slide; steps go in step cards (`D-075`).

### CONF-015 — A Signature Mark on Title, Divider and Closing Slides
- **Status:** ruled (see D-080)
- **Stage:** DSN
- **Primary Position (SWD):** Every element on a slide must earn its place; decoration that carries no message is clutter and competes with the content (`PRIN-DSN-002`, `ANTI-DSN-002`; `SRC-SWD-000`, `SRC-SWD-005`). SWD says nothing specific about title or divider slides.
- **Secondary Position:** A deck should carry one small graphic system: a single mark (for example a thin accent rule down the left edge) on the "document moments" only (cover, section dividers, close), never on working slides; the contrast between the two kinds of slide is the point (`SRC-SEC-015` §consulting style, Graphic system). The same source also puts paper grain and an oversized cropped numeral on those slides.
- **Agent Analysis & Recommendation:** The two meet on non-data slides, where there is no chart for decoration to compete with. A mark that replaces an existing ornament (the short accent rule on today's title slide, `D-075`) adds no element and ties the title slide to the dividers. Recommend allowing at most one flat mark, in the kit colour, on title, divider and closing slides only, with a validator error if it appears on any slide with a chart, table or diagram; reject grain, watermark numerals and any second ornament. Keep SWD as the rule for all content slides.
- **User Ruling:** Adapt, narrowly: one short accent stroke on the title slide only; dividers and the closing key slide carry no extra mark (`D-080` §2).

### CONF-016 — "No Half-Empty Slide" vs. Deliberate White Space
- **Status:** ruled (see D-078)
- **Stage:** DSN
- **Primary Position (SWD):** Remove what does not help the message and let white space do its job; a slide with one or two numbers as large text, and little else, is a valid and strong form (`PRIN-DSN-002`, `PRIN-DSN-003`; `SRC-SWD-000`, `SRC-SWD-005`, `SRC-SWD-012`).
- **Secondary Position:** No slide should be half-empty; if a slide cannot be filled it should not exist, and an automatic gate flags empty bands (`SRC-SEC-015` §consulting style, Density; top-level skill, design rules).
- **Agent Analysis & Recommendation:** Keep SWD. A fill rule pushes agents to add text or decoration to reach a density target, the failure `ANTI-DSN-002` and `D-035` guard against. The useful part of the secondary view is already covered by our layout grid (empty thirds are allowed only by rule, `D-064` §2) and by the HTML and PowerPoint QA. No change recommended.
- **User Ruling:** Keep SWD: white space stays a deliberate tool; no fill-the-slide gate (`D-078` §1).

### CONF-017 — Colouring One Phrase of a Title
- **Status:** ruled (see D-078)
- **Stage:** DSN
- **Primary Position (SWD):** Tie the words of the takeaway title to the data they describe by setting those words in the focal colour of the matching marks (Color Tie, `PAT-DSN-002`, `PRIN-DSN-004`; `SRC-SWD-000`, `SRC-SWD-005`).
- **Secondary Position:** Accenting a single word or phrase of a headline in another colour, weight or italic is one of the commonest signs of a generated, templated page; emphasis should come from size and weight of the whole heading (`SRC-SEC-019` §typography; `SRC-SEC-018` craft floor, gradient and accent habits).
- **Agent Analysis & Recommendation:** The secondary advice is about decorative accents on web pages; a Color Tie is a functional legend that links words to marks. Keep SWD. The redesign may refine how the span looks (same weight as its block, `D-035` Q1; one span family per title) but never removes it.
- **User Ruling:** Keep SWD: Color Tie stays; only its styling may change (`D-078` §1).

### CONF-018 — Big-Number Tiles vs. the "Hero-Metric Template"
- **Status:** ruled (see D-078)
- **Stage:** DSN
- **Primary Position (SWD):** When one or two numbers are the message, show them as large text with a short caption; this is a strong, simple form (`SRC-SWD-012`; `D-064` §3).
- **Secondary Position:** A big number with a small label, supporting stats and an accent is the default page scaffold of generated design and should be refused unless the brief earns it (`SRC-SEC-018` craft floor; `SRC-SEC-019` §design principles).
- **Agent Analysis & Recommendation:** Our tiles are earned by rule: traced numbers, at most three, one focal tile, only on statement slides. Keep SWD; the redesign improves the tiles' typography and spacing.
- **User Ruling:** Keep SWD: big-number tiles stay under `D-064`; styling may change (`D-078` §1).

### CONF-019 — Distinct Hues for Every Group vs. Grey Plus One Accent
- **Status:** ruled (see D-085)
- **Stage:** DSN
- **Primary Position (SWD):** Draw context in grey and give the accent only to what the title names; use more hues only when the audience must tell every group apart, and label them directly (`PAT-DSN-002`, `PRIN-VIS-005`, `ANTI-DSN-001`; `SRC-SWD-008`).
- **Secondary Position:** Shades of one hue are hard to tell apart and suggest an order among groups; give each category its own clearly different hue (`SRC-SEC-022` §24).
- **Agent Analysis & Recommendation:** The secondary point against same-hue shades for unordered groups is sound and already matches `PRIN-VIS-005`; its fix (five distinct hues) answers a different question from a story slide. Keep SWD: grey plus one accent by default; distinct hues only when every group must be told apart, kept few and labelled directly.
- **User Ruling:** Keep SWD (`D-085` §6).
