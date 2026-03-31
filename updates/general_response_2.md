# General Response #2: LLM-as-judge annotations' reliability not validated

**Raised by** kanR, 5t8L

**Critique**: The use of GPT-5 to judge the groundedness/hallucination/validation analysis presented in Section 5.2 is not validated with comparison against human annotators. `kanR` notes that "using an LLM to evaluate other LLMs carries inherent biases" and asks for "human-annotation overlap metrics to demonstrate the objectivity and accuracy of the GPT-5 judge." `5t8L` similarly flags "insufficient evidence provided for the reliability of those assessments, such as human validation and agreement analysis."

**Response**: We agree with the reviewers.
To address this issue, we randomly sampled 100 trajectories.
Three of the authors then annotated the following questions for each trajectory with Yes/No answers, which correspond to the three questions presented in Section 5.2:

* *Groundedness of edits*: Are changes to solutions grounded in the analysis of previous rounds or testing?
* *Hallucinated loss causality*: Are there hallucinated or unsubstantiated claims about why a round was lost?
* *Validation of edits*: Are changes validated by arena simulations or unit tests?

To keep annotation tractable, we collapse the validation dimension to a single binary label.
For instance, we just annotate whether edits were validated (as `True`/`False`), but not the validation technique (e.g., `Arena + Tests`, `Arena`, `Tests`) as shown in Figure 8.
This is a strictly coarser judgment than the paper's full annotation, but we believe agreement at this level meaningfully confirms the degree to which GPT-5's labels are reliable.

The annotation outcomes and code for computing agreement are all available in the anonymous codebase [here](https://github.com/emagedoc/CodeClash/tree/main/updates/human_annotations).

**Results**:

| Question | Fleiss' kappa | Human-GPT5 kappa | Agreement |
|-|-|-|-|
| Groundedness | 0.770 | 0.815 | 91% |
| Hallucinated | 0.675 | 0.737 | 88% |
| Validation   | 0.770 | 0.845 | 94% |

* Agreement = `(Human majority label == GPT 5 label) * 100 / N`
* Fleiss' kappa measures inter-annotator agreement beyond chance among the three human annotators.
* Human-GPT5 kappa (Cohen's kappa) compares agreement beyond chance between the human majority vote (i.e., label of 2+/3 annotators) against GPT-5's label

**Takeaways**:

* Since the paper's findings are based on aggregate proportions rather than individual labels, the 88-94% raw agreement is the most directly relevant metric and shows that the GPT-5 labels are reliable. The Human-GPT5 kappa scores further confirm this agreement is not an artifact of class imbalance.
* "Groundedness" and "Validation" are relatively easy to annotate and have higher agreement. This is expected, as both involve looking for concrete action(s) in a trajectory that reflect whether an edit was (a) based on prior competition logs, and (b) tested empirically for its effect. In practice, reading the first and last couple actions of a trajectory would usually answer this question.
* "Hallucination" is trickier, as extra effort is required to discern whether the conclusion the model draws from looking at competition logs is reasonable. Often times, it clearly is (not) because models will inspect a competition outcome and (mis)interpret it. However, labeling is trickier when the log outcomes are not easily human interpretable (e.g., grid positions in BattleSnake). We put in substantial annotation effort by actually looking and parsing these logs to the best of our abilities as human experts of these games.
* When humans and GPT-5 disagree on hallucination, it is surprinsingly a slight majority of GPT-5 flagging an incident that humans do not. Given that the sample size is a fairly small 100 trajectories, we note this as an observation, rather than a prominent trend.

**Next Steps**: We will incorporate these findings into the appendix of the paper and include a reference to these validation efforts in the caption of Figure 8.
