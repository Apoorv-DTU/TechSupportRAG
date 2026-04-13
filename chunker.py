from typing import List
from bs4 import BeautifulSoup

CHUNK_SIZE_CHAR=512

class Chunker():
    def __init__(self, strategy: str):
        self.strategy = strategy

    def chunk_file(self, document: str):
        if self.strategy == 'FIXED_SIZE':
            return self.fixed_size_chunks(document)
        elif self.strategy == 'FIXED_SIZE_LINES':
            return self.line_chunks(document)
        elif self.strategy == 'PARENT_CHILD':
            return self.parent_child_chunks(document)

    def fixed_size_chunks(self, text):
        chunks = []
        for i in range(0, len(text), CHUNK_SIZE_CHAR):
            chunks.append(text[i:i+CHUNK_SIZE_CHAR])
        return chunks
    
    def line_chunks(self, text):
        chunks = []
        current_chunk = ""
        for line in text.split('\n'):
            current_chunk += f"{line}\n"
            if len(current_chunk) > CHUNK_SIZE_CHAR:
                chunks.append(current_chunk)
                current_chunk = ""
        
        if len(current_chunk) > 0:
            chunks.append(current_chunk)
        return chunks
    
    def parent_child_chunks(self, text):
        # Parent chunk is the entire h3/h2/h1 level section (whichever is most granular)
        # Child chunk is line chunks
        soup = BeautifulSoup(text, "html.parser")
        children = list(soup.children)[2].children
        parent_chunks = []
        current_chunk = [soup.find("h1")]
        for child in children:
            if child.name in ['h1','h2','h3']:
                chunk_text = ""
                for tag in current_chunk:
                    chunk_text += str(tag)
                parent_chunks.append(chunk_text)
                current_chunk = []
                
            current_chunk.append(child)

        if len(current_chunk) > 0:
            chunk_text = ""
            for tag in current_chunk:
                chunk_text += str(tag)
            parent_chunks.append(chunk_text)

    
        chunks = []
        for parent in parent_chunks:
            for child in self.line_chunks(parent):
                chunks.append({'parent': parent, 'child': child})
        return chunks
