import chromadb
from openai import OpenAI
from sentence_transformers.cross_encoder import CrossEncoder

COLLECTION_NAME="d365_parent_child"#"d365_fixed"
VECTOR_DIR="vectordb"
CHAT_QUERY_MODEL="gpt-3.5-turbo"

class QueryEngine():

    def __init__(self, collection_name=COLLECTION_NAME):
        self.chroma_client = chromadb.PersistentClient(VECTOR_DIR)
        self.collection = self.chroma_client.get_collection(collection_name)
        self.openai_client = OpenAI()
        self.reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2')
    
    def get_hypothetical_doc(self, question):
        print("Rewriting query...")
        prompt = f"""Write a Microsoft Dynamics365 product documentation that answers the following question:
        {question}
"""
        llm_response = self.openai_client.responses.create(
            model=CHAT_QUERY_MODEL,
            input=prompt,
            temperature=0.2
        )

        return llm_response.output_text

    def rerank(self, question, docs):
        ranks = self.reranker_model.rank(question, docs)
        idx = []
        for i in range(0, 5):
            idx.append(ranks[i]['corpus_id'])
        return idx

    def query_d365(self, question, hyde=False, rerank=False):

        num_results = 20 if rerank else 5
        query_text = question if not hyde else self.get_hypothetical_doc(question)

        #print(f"query_text:\n{query_text}")
        print("Finding relevant documents...")
        results = self.collection.query(
                    query_texts=[query_text],
                    n_results=num_results)
        
        retrieved_docs = []
        retrived_titles = results['ids'][0]
        if results['metadatas'][0][0] is not None:
            for metadata in results['metadatas'][0]:
                parent_chunk = metadata['parent']
                if parent_chunk not in retrieved_docs:
                    retrieved_docs.append(parent_chunk)
        else:
            retrieved_docs = results['documents'][0]

        if rerank:
            reranked_idx = self.rerank(question, retrieved_docs)
            reranked_docs = []
            reranked_titles = []
            for idx in reranked_idx:
                reranked_docs.append(retrieved_docs[idx])
                reranked_titles.append(retrived_titles[idx])

            retrived_titles = reranked_titles
            retrieved_docs = reranked_docs

        print("Composing Answer...")
        prompt = self.get_prompt(question, retrived_titles, retrieved_docs)
        
        llm_response = self.openai_client.responses.create(
            model=CHAT_QUERY_MODEL,
            input=prompt,
            temperature=0.2
        )

        return llm_response.output_text, retrieved_docs, query_text


    def get_prompt(self, query, ids, documents):
        
        formatted_docs = ""
        for i in range(len(documents)):
            #title = ids[i][:-3]
            #formatted_docs += f"Title: {title}\n"
            formatted_docs += f"Excerpt #{i}: ```html\n{documents[i]}\n```\n\n"
        
        prompt=f"""
You are a helpful assistant for Microsoft Dynamics365. Conscisely answer the given question based on the provided excerpts from the documentation.
Your answer should only contain claims and implications that can be INDISPUTABLY backed up by the documentation.

# Excerpts
{formatted_docs}

# Question
{query}
    """
        return prompt


if __name__ == '__main__':
    engine = QueryEngine()
    
    while True:
        question = input("\n> ")
        print("Thinking...")
        answer, prompt, queried_text = engine.query_d365(question, rerank=True, hyde=True)
        print(f"\nAnswer:\n{answer}")