import faiss
import numpy as np
from transformers import AutoModel, AutoTokenizer


class FaissVectorSearch:
    def __init__(
        self,
        index_path,
        dim,
        metric=faiss.METRIC_INNER_PRODUCT,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.index_path = index_path
        self.dim = dim
        self.metric = metric
        self.index = self.load_index()
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def load_index(self):
        try:
            return faiss.read_index(self.index_path)
        except FileNotFoundError:
            return faiss.IndexFlatL2(self.dim)

    def save_index(self):
        faiss.write_index(self.index, self.index_path)

    def create_embedding(self, text):
        """
        Create embeddings for a piece of text.

        Args:
            text (str): Text to create embeddings for.

        Returns:
            embeddings (numpy array): Embeddings for the input text.
        """
        inputs = self.tokenizer(text, return_tensors="pt")
        outputs = self.model(**inputs)
        embeddings = outputs.pooler_output.detach().numpy()[0]
        return embeddings

    def upsert(self, texts, ids):
        """
        Upsert embeddings into the index.

        Args:
            texts (list): List of texts to upsert.
            ids (list): IDs corresponding to the texts.
        """
        embeddings = np.array([self.create_embedding(text) for text in texts])
        self.index.add_with_ids(embeddings, np.array(ids, dtype=np.int64))
        self.save_index()

    def search(self, query_text, k=10):
        """
        Search for similar texts in the index.

        Args:
            query_text (str): Query text to search for.
            k (int, optional): Number of nearest neighbors to return. Defaults to 10.

        Returns:
            distances (numpy array): Distances to the nearest neighbors.
            indices (numpy array): Indices of the nearest neighbors.
        """
        query_embedding = self.create_embedding(query_text)
        distances, indices = self.index.search(np.array([query_embedding]), k)
        return distances, indices

    def hybrid_search(self, query_text, k=10, filter_ids=None):
        """
        Perform a hybrid search, first filtering by ID and then searching for similar texts.

        Args:
            query_text (str): Query text to search for.
            k (int, optional): Number of nearest neighbors to return. Defaults to 10.
            filter_ids (list, optional): IDs to filter by. Defaults to None.

        Returns:
            distances (numpy array): Distances to the nearest neighbors.
            indices (numpy array): Indices of the nearest neighbors.
        """
        if filter_ids is not None:
            filter_ids = np.array(filter_ids, dtype=np.int64)
            filtered_index = faiss.IndexFlatL2(self.dim)
            filtered_index.add_with_ids(
                self.index.reconstruct_n(0, self.index.ntotal), self.index.id_map
            )
            filtered_index.filter(filter_ids)
            distances, indices = filtered_index.search(
                np.array([self.create_embedding(query_text)]), k
            )
        else:
            distances, indices = self.search(query_text, k)
        return distances, indices


if __name__ == "__main__":
    # Create a FaissVectorSearch instance
    search = FaissVectorSearch("index.faiss", 128)

    # Create some embeddings
    texts = ["This is a sample text.", "This is another sample text."]
    ids = [1, 2]
    search.upsert(texts, ids)

    # Search for similar texts
    query_text = "This is a sample query."
    distances, indices = search.search(query_text, k=10)

    # Perform a hybrid search
    filter_ids = [1]
    distances, indices = search.hybrid_search(query_text, k=10, filter_ids=filter_ids)
