# General Response #1: Comparisons to human expert solutions are limited.

**Raised by** NxFK, y7Xj, kanR, 5t8L

**Critique**: The comparison between AI and human experts "only provides information on one arena and only one expert bot created by a static expert" (`5t8L`), which weakens the generality of the claim.

**Response**: We agree with the reviewers.
To address this issue, we manually identified, then evaluate models against 58 RobotRumble and 264 Core War human expert solutions posted online.

However, evaluating every model against every human solution would be extremely expensive ([322 human solutions vs. 8 models] x 10 tournaments x 15 rounds/tournament x $1/round = $386400).

Therefore, to make evaluation against human experts affordable while retaining the multi-round, evolve-against-opponents, and codebase-as-memory attributes of the original CodeClash evaluation, we introduce **"CodeClash Ladder"** (referred to as **CC:Ladder** going forwards).
CC:Ladder works as follows.

First, we construct a relative ranking of human solutions for each arena as follows:

* We crawl `N` human solutions for a specific arena from online leaderboards
* We run all pairs of `N` human solutions against one another (`N*(N-1)/2` matchups).
* We then calculate Elo from competition outcomes (exactly as done for the paper's main leaderboard), which yields a relative ranking of experts' solutions.

To evaluate a model against a ladder, we see **how far up the list a model** can climb, i.e., we match the model with increasingly stronger human opponents until the first loss. The final score corresponds to the **highest-ranked opponent defeated**:

* A model's initial codebase competes against the *weakest* human solution.
* A model then competes in `n` rounds against the static human opponent (i.e., can perform `n` updates to its codebase)
* The model advances to the next-strongest opponent only if it wins `>1/3` of rounds **and** wins the final round.
    * We enforce the `>1/3` criteria because sometimes models make their codebase worse.
    * The "ladder run" terminates when either of this criteria is not met.
* The model's codebase **carries over** between opponents — it is never reset.
* Again, final score corresponds to the **highest-ranked opponent defeated**.

Experiment Setup:

* We run 4 models from the original leaderboard, along with 3 new ones released after the submission deadline.
* A model is given `n=7` rounds to beat each opponent.
* Each model is run on each ladder 5 times to account for variance.
  To be extra conservative, we keep the highest score across the 5 runs.

**Results**:

Score = highest rank opponent beat across 5 runs.

| Model | RobotRumble (58) | Core War (264) |
|-|-|-|
| Claude Sonnet 4.5 | 43 | 205 |
| Claude Sonnet 4.6 | 39 | 177 |
| GPT-5             | 51 | 201 |
| GPT-5 mini        | 57 | 260 |
| GPT-5.2 Codex     | 44 | 191 |
| Gemini 2.5 Pro    | 54 | 233 |
| Gemini 3 Pro      | 44 | 203 |

In this table, 58 corresponds to the 58 human solutions in the RobotRumble ladder, and 264 corresponds to the 264 human solutions in the Core War ladder.

**Takeaways**:

* The failure modes (drawing ungrounded conclusions, lack of inspection of competition logs) reported in Section 5.2 of the paper persist in this setting.
* With the exception of GPT-5 mini, all models' runs terminate because it failed to win the final round against the last opponent.
* Ladders can be created for the other 4 arenas with more time, but because of budget constraints and the manual effort required to crawl human expert solutions, our findings are grounded to these two arenas.

**Next Steps**: We plan to incorporate all these findings formally into the paper, then release the corresponding data soon.

We understand that this section introduces quite a few new ideas and mechanisms.
We provide a thorough [report](https://github.com/emagedoc/CodeClash/blob/main/updates/cc_ladder/report.md), uploaded to the anonymous codebase.
The report includes additional technical details for how human expert solution rankings were computed, along with the explicit ranking lists for each arena.

We are happy to provide any clarifications as needed during the discussion period.
