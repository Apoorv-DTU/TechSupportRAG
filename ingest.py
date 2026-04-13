from chunker import Chunker
from reader import document_from_html
import chromadb
import glob
from tqdm import tqdm

CHUNK_STRATEGY = 'PARENT_CHILD'
COLLECTION_NAME = 'd365_parent_child'
chunker = Chunker(CHUNK_STRATEGY)
client = chromadb.PersistentClient("vectordb")
collection = client.get_or_create_collection(name=COLLECTION_NAME)

files = glob.glob("docs/*")
for fname in tqdm(files):
    html_content, title = document_from_html(fname)
    chunks = chunker.chunk_file(html_content)
    ids = [f"{title} #{i}" for i in range(0, len(chunks))]

    if len(chunks) == 0:
        print(f"{fname} is empty")
        continue 

    if CHUNK_STRATEGY == 'PARENT_CHILD':
        parent_chunks = []
        children_chunks = []
        for chunk in chunks:
            children_chunks.append(chunk['child'])
            parent_chunks.append({
                "parent": chunk['parent']
            })
        collection.add(ids=ids, documents=children_chunks, metadatas=parent_chunks)
    else:
        collection.add(ids=ids, documents=chunks)