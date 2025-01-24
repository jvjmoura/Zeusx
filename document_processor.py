from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(self, llm):
        self.llm = llm
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=6000,
            chunk_overlap=1000,
            separators=["\n\n", "\n", ".", " "]
        )
        
    def process_document(self, document):
        """Processa o documento, dividindo em chunks."""
        # Remove espaços extras e normaliza quebras de linha
        clean_text = " ".join(document.split())
        chunks = self.text_splitter.split_text(clean_text)
        return chunks
        
    def get_context(self, query, chunks):
        """Retorna os chunks mais relevantes para a query."""
        query_words = set(query.lower().split())
        scores = []
        
        for chunk in chunks:
            words = set(chunk.lower().split())
            score = len(query_words.intersection(words))
            scores.append((score, chunk))
        
        # Pega os 3 chunks mais relevantes
        relevant = sorted(scores, key=lambda x: x[0], reverse=True)[:3]
        return "\n\n".join(chunk for score, chunk in relevant)
