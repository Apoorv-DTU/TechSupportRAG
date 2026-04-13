# TechSupportRAG
This RAG system is a QnA engine that answers product questions related to Microsoft Dynamics 365 suite, based on the publicly available documentation.

## High Level Design
TechSupportRAG has two control flow paths:

1. **Ingestion**: This path processes the raw HTML documentation to add it to the knowledge-set based on which questions are answered.
2. **Query**: This path answers a given question based on the ingested data.

### Ingestion Pipeline

**Data Cleaning**
Each raw HTML documentation contains a whole lot of information, most of which is not relevant to answering questions, such as section sidebar, copyright information, etc. Luckily, the HTML nodes containing actual content belong to the "content" classes for CSS styling. We extract relevant information from each document by extracting the only the content of these nodes. 

**Chunking Strategy**
Each document is too large to directly add into the context, which is why we must divide each document into smaller "chunks" that can be retrieved and added to the context instead. We evaluate three chunking strategies:

1. Fixed Characters Split: Each document is divided into a blocks of 512 characters. While simple to implement and maintain, the main drawback is that it can break chunks mid-sentence before a thought is completed, which can results in critical context being destroyed, or in the worst case, even misinterpreted.
2. Line Split: This strategy seeks to avoid splitting sentences by only splitting on newlines once the chunk becomes than 512 characters. While this is an improvement over fixed character split, it can also break thoughts that span across several lines. Also, this can split apart step-by-step instructions because each step is usually on a different line.  
3. Structure-Aware Parent-Child Split: This strategy aims to avoid breaking up thoughts or instructions. The rough structure of each cleaned document contains an article heading, followed by a list of sections, where each section has a heading and the content. Each section can optionally contain a list of subsections that follow the same structure. We leverage this structure to maintain the contextual integrity. This is implemented by first breaking each document into "child" chunks using the line-split strategy. Each child chunk contains a reference to its "parent" chunk which is the entirety of the most granular section/subsection where the child appears. The child chunks are used to find the most relevant parent chunks. 

### Query Pipeline
A naive barebones setup for the query pipeline involves retrieving the relevant chunks (which are 5 closest chunks as per semantic search), and adding those chunks for the LLM prompt to generate an answer. In addition to this naive strategy, we also evaluate the performance with two enhancements

1. Query Rewriting: We use the HyDE (Hypothetical Document Embedding) strategy to generate the retrieval query against which relevant chunks are retrieved. This component generates a hypothetical documentation based on the user question. The rationale is that this hypothetical document might generate thoughts or keywords that are closer to the relevant chunks than the question alone. 

2. Re-ranking: This step re-ranks the initial set of retrieved chunks using a cross-encoder. In this the vanilla search returns 20 documents, which are cross-encoded with the original user query. The cross-encoder outputs a similarity score, based on which the set is reduced to 5 most similar chunks, in order. 

## Eval Metrics
We evaluate the performance of TechSupportRAG using LLM-as-a-judge with gpt-5.4-nano being the judge model. We choose the following eval metrics to measure the performance of TechSupportRAG

1. Context Recall: It uses a set of expected responses to measure the alignment of the retrieved document with those response. This measures the accuracy of the retriever   
2. Answer Relevancy: This score measures how well the generated response aligns with the question. This metric determines the usefulness of the system (regardless of factual accuracy).
3. Faithfulness: This score determines the groundedness of the generated response in the retrieved chunks. This represent the factual correctness of the system, and penalises hallucinations 

The success criteria for the project is: Answer Relevancy > 0.80 and Faithfulness > 0.85

### Golden eval dataset
We manually prepared a list of 50 question and answer pairs from online Dynamics 365 documentation. 

Result of the evaluations can be found in `eval_report.md`

## Implementation Design Choices
This project calls the OpenAI API directly and does not use any agentic library such as LlamaIndex or LangChain. We use ChromaDB for storing vectors because it can be run locally without an additional subscription. Furthermore, we use DeepEval library to run the evals over RAGAS because the metrics that we use are available in both libraries, and DeepEval is easier to run locally on our setup as compared to RAGAS. Primary LLM used to generate responses and hypothetical documents is gpt-3.5-turbo

### Note: Performance dip with HyDE
On observing the eval results, we notice something interesting: There is a dip in context recall (and pass rate) as compared to naive RAG when using HyDE. To dig deeper, we went through a few test cases where the HyDE approach failed, and observed the generated hypothetical document. We analyse two such examples here

Example 1: 
Q: What do I need to set up a multilingual contact center?

For this query, the hypothetical document mentions a complex setup to enable multilingual support. More specifically, the hypothetical document contains several mentions of enablement of translation services to enable multilingual support. This is a reasonable document without any prior product knowledge. However, in D365, enabling translation services are a completely different mechanism from a multilingual contact center. The focus on translation services derail the search and causes the search to retrieve documents pertaining to translation rather than multilingual support.

Example 2:
Q: Is there any ability to block phone numbers in the voice channel?

For this query, the hypothetical document said that there is no such ability, and provided several of alternate solutions to achieve the goal. However, the problem is that D365 documentation actually does support blocking phone numbers. Due to a heavy focus of the hypothetical document on alternatives, it skewed the search towards those alternatives, and the document containg blocking information does not make it into the results. 

The primary benefit of using HyDE is to broaden the search space to make retrieval easier. However, technical documents such as those in D365 contain product specific terminology, which while appears related on the surface, has actually completely different technical interpretation (such as translation and multilingual). Also, sometimes the search can become too broad (with irrelevant suggestions for blocking phone numbers for example), which degrades the retrieval.

However, re-ranking with a cross-encoder fixes some of these issues by measuring the similarity of the retrieved documents against the question directly. This is evident by recovery in performance when using HyDE with reranking 

### Conclusion
We select the final system to be a Reranker + HyDE approach because it demonstrated the highest pass rate on the golden eval dataset.

## Scope for Future Enhancements and Development
1. *Eval improvements*: QnA pairs in the current golden evaluation set only a few questions that rely on reading hard facts from a table (such as cost of running a feature in a particular configuration). And almost each question can be answered by just single webpage from the documentation. These enhancements can be used to make the evals harder and reflect real-world usage more closely.
2. *Judge LLM*: We are using a smaller model (gpt-5.4-nano) as a judge to save on costs for this project. However, using a larger model (such as gpt-4.1 for example) might yield more accurate evals.
3. *Hybrid search*: Currently, semantic search is used to find the relevant chunks from the corpus. However, because the product contains specific terminology, it might be helpful to introduce a keyword-based search component, and combine the results using Reciprocal Rank Fusion (RRF)
4. *Multi-turn conversations*: The current query workflow only supports single-turn conversation model. A multi-turn conversation model would allow users to ask for clarifications and follow-up questions to the generated answers
5. *Multi-modal support*: As it currently stands, only text from the documentation is added to the knowledge base. Multi-modal support would enable processing images, including screenshots, to improve the generated answers.