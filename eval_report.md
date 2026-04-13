# Chunking Strategy Result

These evals compare the performance different chunking strategies in a naive RAG setup

| Strategy | Context Recall | Answer Relevancy | Faithfulness
|---|---|---|---|
| Fixed Characters (512 characters) | 0.64 | 0.86 | 0.86 |
| Line Level | 0.73 | 0.90 | 0.88 |
| Parent-Child chunking | 0.69 | 0.92 | 0.88 |

# Enhanced RAG Result
These evals compares how the performance evolves with addition of enhanced RAG components such as a query-rewritter and a re-ranker. For these evals, parent-child chunking strategy is used.

In addition to these metrics, we define a pass rate as the percentage of datapoints in the golden eval sets, for which the system produced a response for which all scores are > 0.5

| RAG Components | Context Recall | Answer Relevancy | Faithfulness | Pass Rate |
|---|---|---|---|---|
| Naive RAG | 0.69 | 0.92 | 0.88 | 72% |
| Query rewriting (HyDE) | 0.58 | 0.84 | 0.90 | 50% |
| Reranking (cross-encoder) | 0.71 | 0.85 | 0.89 | 72% |
| Reranking (cross-encoder) + Query rewriting (HyDE) | 0.73 | 0.90 | 0.89 | 78% |