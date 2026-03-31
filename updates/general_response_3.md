# General Response #3: Robustness of findings to evaluation setup

**Raised by** kanR, 5t8L, y7Xj

**Critique**: Reviewers question whether CodeClash's findings are robust to changes in the evaluation setup. Two related concerns:

* *Scaffold choice*: `kanR` argues mini-SWE-agent's bash-only interface may cause the observed failures — "the observed phenomena of models performing poorly... might be due to the deprivation of standard linting, AST parsing, or code tree visualization tools... rather than a direct failure of the foundation models' reasoning capabilities."
* *Hyperparameter sensitivity*: `5t8L` notes "little evidence from the paper that the results will be stable across varying budgets or prompting, or different action interfaces." `y7Xj` similarly observes the paper "does not study how results change under different prompt settings or editing budgets."

**Response**:

We appreciate the reviewers raising this point.
We agree these are good questions, but believe that both our existing findings and the infeasibility of the budget for such experiments stand point address these concerns.

First, a full ablation — varying scaffolds, budgets, and prompts across all 8 models and 6 arenas — would require on the order of hundreds of additional tournament runs ([3+ scaffold variants x 3+ budget settings x 8 models x 6 arenas] x 10 tournaments x $1/round) and 6 figures of cost, well beyond the budget of this study.

That said, we do not believe such toggling would meaningfully change our findings.
Evidence across our results and analyses suggestthat the observed performance gaps reflect strategic reasoning limitations, not limitations imposed by the scaffold or budget effects:

*On scaffold choice*:

* **[Section 5.2, Figure 7]** Models achieve 85%+ bash command success rates with rapid error recovery, demonstrating proficiency with the interface.
* **[Section 5.2, Figure 8]** The dominant failure modes — hallucinated loss causality, deploying untested edits — are strategic failures. A linter or AST parser is unlikely to help a model that misinterprets competition logs.
* **[Section 5.1, Figure 6]** Even strong models struggle to recover after losing rounds: Claude Sonnet 4.5's comeback probability drops below 1/3 after a single loss. This pattern reflects strategic rigidity, not interface limitations.
* **[Section 5.1, Figure 5]** Models' solutions diverge more with each round, yet this divergence does not correlate with win rate — again pointing to reasoning, not tooling, as the bottleneck.
* **[Section 3.1]** mini-SWE-agent's minimalist design is intentional: it isolates the foundation model's capabilities from scaffold-specific advantages. Prior works (e.g., SWE-bench Multimodal) are a precedent for such a decision. Richer toolchains would confound attribution.

*On hyperparameter sensitivity*:

* **[Section 4.1 vs. General Response #2]** The main evaluation uses 15 rounds per tournament; CC:Ladder uses 7 rounds per opponent — a substantially different budget — yet model rankings remain consistent across both.
* **[Section 5.1]** Qualitative findings (self-crafted memory strategies, file organization patterns, messy codebases) emerge consistently across all 8 models and 6 arenas, suggesting they are not artifacts of a specific budget.
* **[Appendix B]** CodeClash's system prompt is deliberately minimal and arena-agnostic, leaving little room for prompt-specific sensitivity.

We will add an explicit discussion of these robustness considerations in the revised paper.
A more comprehensive ablation over scaffolds and budgets is a valuable direction for future work.
