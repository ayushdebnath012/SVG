"""Replace pending MCTS status with completed, scorer-grounded pilot results."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'paper/network'
EXP=ROOT/'experiments/mcts-astra-20261007-final'
c=json.loads((EXP/'comparison.json').read_text())
assert json.loads((EXP/'selection-audit.json').read_text())['passed']
assert json.loads((EXP/'search-summary.json').read_text())['api_completed']>0
p=PAPER/'main.tex';s=p.read_text()
if '\\input{mcts-results}' not in s:s=s.replace('\\input{tier-results}','\\input{tier-results}\n\\input{mcts-results}')
p.write_text(s)
p=PAPER/'sections/mechanical/abstract.tex';s=p.read_text()
s=s.replace('this small gain does not isolate training from extra inference.',r'''this small gain does not isolate training from extra inference. A separate bounded MCTS pilot reaches \mctsAfter/\mctsN{} with \mctsCalls{} new candidate-generation attempts; unequal compute and one seed limit attribution.''')
p.write_text(s)
p=PAPER/'sections/mechanical/conclusion.tex';s=p.read_text()
s=s.replace('with substantial false rejections.',r'''with substantial false rejections. A separate development-calibrated MCTS pilot reaches \mctsAfter/\mctsN{}; additional sampling and changed observations preclude attributing its outcome to search topology alone.''')
p.write_text(s)
p=PAPER/'sections/mechanical/experiments.tex';s=p.read_text()
old='A proposed MCTS search space over CAD edit thoughts appears in Appendix~\\ref{sec:mcgot-design}; it has not been run and contributes no reported result.'
new=r'''A separate bounded MCTS pilot appears in Appendix~\ref{sec:mcgot-design} and Figure~\ref{fig:mcts-results}: it reaches \mctsAfter/\mctsN{} (\mctsRate\,\%), against \mctsBefore/\mctsN{} for Astra and \mctsPrior/\mctsN{} for the single-repair loop. It uses \mctsCalls{} additional generation attempts and development-calibrated selection; the comparison is not equal-compute.'''
assert old in s;s=s.replace(old,new);p.write_text(s)
p=PAPER/'sections/mechanical/appendix.tex';s=p.read_text()
s=s.replace('\\subsection{Proposed MCTS search space for CAD thoughts}','\\subsection{Bounded MCTS pilot over CAD edit thoughts}')
s=s.replace('This is a design extension, not a completed experiment: the reported \\agentBefore/\\agentN{} to \\agentAfter/\\agentN{} result belongs exclusively to the single-repair protocol above. No Monte Carlo search result or additional improvement is claimed.',r'''The \agentBefore/\agentN{} to \agentAfter/\agentN{} result belongs to the single-repair protocol above. We separately run a bounded seed-17 MCTS pilot with the same initial answers and frozen verifier; its outcome is \mctsAfter/\mctsN{} overall and \mctsValidAfter/\mctsValidN{} among valid references.''')
s=s.replace('presents a proposed Monte Carlo tree search (MCTS) space','presents the Monte Carlo tree search (MCTS) space')
s=s.replace('\\textbf{Proposed Monte Carlo tree search space for CAD editing.}','\\textbf{Monte Carlo tree search space for the bounded CAD pilot.}')
s=s.replace('The root contains source CAD and the requested edit.','The root contains source CAD, the requested edit and the saved initial Astra patch.')
s=s.replace('This proposal has not been run; the completed \\agentBefore/\\agentN{} to \\agentAfter/\\agentN{} gain belongs to the single-repair experiment.',r'''The \agentBefore/\agentN{} to \agentAfter/\agentN{} outcome belongs to the single-repair experiment; the separate MCTS pilot reaches \mctsAfter/\mctsN{}. This is an architecture diagram, not a logged task tree.''')
marker='\\paragraph{State and tree construction.}'
addition=r'''\paragraph{Completed pilot configuration and outcome.}
Search is gated on the same 60 initial verifier rejections; the 64 initially accepted answers remain unchanged. Each searched task receives up to four fresh low-effort Astra generations, with width two, depth two, UCT coefficient 0.7, a 2,500-token completion cap and three concurrent API workers. First-level expansions sample alternatives to the initial patch; later expansions revise a selected parent, always indexing the original source. Rollouts execute the new candidate and query the frozen verifier after both target-free observations. Repeated terminal rollouts reuse the deterministic proxy value; no reference is available to search.

We fit L2 Platt calibration on the 238 component-disjoint development candidates before held-out sampling. Numeric-check weights in $\{0,0.1,0.2\}$ and eligibility thresholds maximize development balanced accuracy with fixed tie breaking; the selected numeric weight is \mctsNumericWeight{} and threshold \mctsThreshold{}. Numeric observations remain model-visible even when their direct score weight is zero. A depth penalty of 0.005 favors shorter revisions. An executable, eligible child replaces the initial answer only if its penalized proxy score is strictly higher; otherwise retain the initial answer. Calibration replay matches the saved development result. This is post-training calibration, not new GRPO training.

The pilot completes \mctsCompleted{} of \mctsCalls{} new generation attempts, selects \mctsReplaced{} replacements and costs approximately \$\mctsCost{} including its credential diagnostic, below the approved \$5 cap. Search and target-free verification take approximately \mctsSeconds{} seconds, excluding initial model loading, development calibration and final reference scoring. Against Astra, \mctsRecovered{} tasks recover and \mctsRegressed{} regress (paired exact $p=\mctsP$ among valid references). Against the earlier single-repair loop, \mctsPriorGained{} tasks are gained and \mctsPriorLost{} lost ($p=\mctsPriorP$). These are one-seed, unequal-compute outcomes and do not isolate MCTS from extra generation, different verifier observations or calibration. Selections and their SHA-256 digest are frozen and audited before released STEP solids enter the offline scorer. A configured-project quota error and a local pre-dispatch request-building error are preserved separately; neither produced candidates or informs geometry-based selection.

\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{figures/mcts-astra-comparison.pdf}
\caption{\textbf{Completed bounded MCTS pilot versus Astra and one repair.} Left: strict geometry success counts on all 124 attempted BenchCAD tasks. Right: paired counts within descriptive edit tiers on 123 valid-reference tasks. All systems share the same initial answers; MCTS searches only the 60 previously rejected candidates. Additional generation budgets differ, so this comparison cannot attribute an improvement to tree search alone. One invalid reference is retained in the overall denominator.}
\label{fig:mcts-results}
\end{figure*}

'''
assert marker in s;s=s.replace(marker,addition+marker)
s=s.replace('Each proposed patch is validated and executed','Each sampled patch is validated and executed')
p.write_text(s)
p=PAPER/'README.md';s=p.read_text();s+='\nCompleted MCTS pilot: `../../experiments/mcts-astra-20261007-final`. `mcts-results.tex` and `figures/mcts-astra-comparison` come from `../../scripts/mcts_paper_results.py`; selections were audited before offline reference scoring. Earlier failed initialization/request attempts remain separate. This is one seed and not an equal-compute comparison. Student-editor GRPO remains pending.\n';p.write_text(s)
