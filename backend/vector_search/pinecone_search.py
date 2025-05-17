from pinecone import Pinecone
from typing import List, Dict

import openai
from dotenv import load_dotenv
import os

load_dotenv()
PINE_API_KEY = os.getenv("PINE_API_KEY")
PINE_INDEX_NAME = os.getenv("PINE_INDEX_NAME")


class PineconeSearch:
    def __init__(self, api_key: str, index_name: str):
        """
        Initialize the PineconeSemanticSearch class with Pinecone credentials.

        Args:
            api_key (str): Pinecone API key.
            index_name (str): Name of the Pinecone index.
        """
        self.api_key = PINE_API_KEY
        self.index_name = PINE_INDEX_NAME

        # Initialize Pinecone
        pinecone = Pinecone(api_key=self.api_key)
        if (
            not pinecone.list_indexes().names()
            or self.index_name not in pinecone.list_indexes().names()
        ):
            raise ValueError(f"Index '{self.index_name}' does not exist in Pinecone.")

        self.pinecone = pinecone
        self.index = pinecone.Index(self.index_name)

    def search(
        self, query: str, requires_embedding: bool = False, top_k: int = 5
    ) -> List[Dict[str, any]]:
        """
        Perform a semantic search on Pinecone and retrieve the top-k results.

        Args:
            query (str): The query string to search for.
            requires_embedding (bool): Whether to generate an embedding for the query.
            top_k (int): The number of top results to retrieve. Defaults to 5.

        Returns:
            List[Dict[str, any]]: A list of dictionaries containing the search results.
        """
        # Validate the query
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty or None.")

        try:
            # Optionally generate an embedding for the query
            query_embedding = None
            if requires_embedding:
                query_embedding = self.pinecone.inference.embed(
                    model="llama-text-embed-v2",
                    inputs=[query],
                    parameters={"input_type": "query"},
                )
                if not query_embedding:
                    raise ValueError("Failed to generate embedding for the query.")

                # Perform semantic search using the embedding
                results = self.index.query(
                    namespace=os.getenv("PINE_INDEX_NAME"),
                    vector=query_embedding[0].values,
                    top_k=top_k,
                    include_metadata=True,
                )
            else:
                # Perform keyword-based search
                results = self.index.query(
                    namespace=os.getenv("PINE_INDEX_NAME"),
                    filter={"text": {"$contains": query}},
                    top_k=top_k,
                    include_metadata=True,
                )

            # Check if results are empty
            if not results or "matches" not in results:
                print("No matches found in Pinecone results.")
                return []

            # Format the results
            formatted_results = [
                {
                    "id": match["id"],
                    "score": match["score"],
                    "metadata": match["metadata"],
                }
                for match in results["matches"]
            ]

            return formatted_results

        except Exception as e:
            print(f"Error during Pinecone search: {e}")
            return []

    def rerank(self, results: List[Dict[str, any]], query: str) -> List[Dict[str, any]]:
        """
        Rerank the search results based on custom logic.

        Args:
            results (List[Dict[str, any]]): The initial search results.
            query (str): The query string to use for reranking.

        Returns:
            List[Dict[str, any]]: The reranked search results.
        """
        # Example reranking logic: prioritize results with higher relevance to the query
        for result in results:
            metadata = result.get("metadata", {})
            if "important" in metadata.get(
                "tags", []
            ):  # Example: prioritize "important" tags
                result["score"] += 1.0  # Boost score for important results

        # Sort results by score in descending order
        reranked_results = sorted(results, key=lambda x: x["score"], reverse=True)
        return reranked_results

    def hybrid_search(
        self, query: str, top_k: int = 5, keyword_weight: float = 0.5
    ) -> List[Dict[str, any]]:
        """
        Perform a hybrid search combining semantic and keyword-based search.

        Args:
            query (str): The query string to search for.
            top_k (int): The number of top results to retrieve. Defaults to 5.
            keyword_weight (float): Weight for keyword-based scores (0.0 to 1.0).

        Returns:
            List[Dict[str, any]]: A list of dictionaries containing the hybrid search results.
        """
        # Generate an embedding for the query
        query_embedding = self._generate_embedding(query)

        # Perform semantic search
        semantic_results = self.index.search(
            namespace=os.getenv("PINE_INDEX_NAME"), query=query_embedding
        )

        # Perform keyword-based search (mocked here, replace with actual implementation)
        keyword_results = [
            {
                "id": "keyword1",
                "score": 0.8,
                "metadata": {"text": "Keyword match example 1"},
            },
            {
                "id": "keyword2",
                "score": 0.7,
                "metadata": {"text": "Keyword match example 2"},
            },
        ]

        # Combine semantic and keyword results
        combined_results = []
        for semantic_result in semantic_results["matches"]:
            combined_score = semantic_result["score"] * (
                1 - keyword_weight
            )  # Semantic score contribution
            for keyword_result in keyword_results:
                if semantic_result["id"] == keyword_result["id"]:
                    combined_score += keyword_result["score"] * keyword_weight
            combined_results.append(
                {
                    "id": semantic_result["id"],
                    "score": combined_score,
                    "metadata": semantic_result["metadata"],
                }
            )

        # Sort combined results by score in descending order
        combined_results = sorted(
            combined_results, key=lambda x: x["score"], reverse=True
        )
        return combined_results

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text using OpenAI's embedding model.

        Args:
            text (str): Text to generate an embedding for.

        Returns:
            List[float]: The generated embedding.
        """
        try:
            response = openai.embeddings.create(
                input=text, model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None


from pinecone import Pinecone
import time
from pinecone import ServerlessSpec


def create_index():
    pc = Pinecone(api_key=os.getenv("PINE_API_KEY"))
    index_name = os.getenv("PINE_INDEX_NAME")
    if not pc.has_index(index_name):
        index = pc.create_index(
            name=index_name,
            vector_type="dense",
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            deletion_protection="disabled",
            tags={"environment": "development"},
        )

    print(f"Index '{index_name}' created successfully.")


def delete_index():
    pc = Pinecone(api_key=os.getenv("PINE_API_KEY"))
    index_name = os.getenv("PINE_INDEX_NAME")
    if pc.has_index(index_name):
        pc.delete_index(index_name)
        print(f"Index '{index_name}' deleted successfully.")


def test_search_pinecone():
    from dotenv import load_dotenv
    import os

    load_dotenv()

    # Initialize PineconeSearch
    api_key = os.getenv("PINE_API_KEY")
    index_name = os.getenv("PINE_INDEX_NAME")
    searcher = PineconeSearch(api_key=api_key, index_name=index_name)

    # Perform a search
    query = "Q: What is Smooth AI, and how does it work?\nA: Smooth AI is an interactive AI Advisor that engages website visitors in real-time, answering questions, guiding them through sales, and booking meetings.'"
    results = searcher.search(query=query, requires_embedding=True, top_k=5)

    # Print the results
    if results:
        print("Search Results:")
        for result in results:
            print(
                f"ID: {result['id']}, Score: {result['score']}, Metadata: {result['metadata']}"
            )
    else:
        print("No results found.")


# if __name__ == "__main__":

#     # delete_index()
#     create_index()


def check_saved_data_pinecone():
    from pinecone import Pinecone
    from dotenv import load_dotenv
    import os

    load_dotenv()

    # Initialize Pinecone
    api_key = os.getenv("PINE_API_KEY")
    index_name = os.getenv("PINE_INDEX_NAME")
    pc = Pinecone(api_key=api_key)  # Initialize the Pinecone client
    if not pc.has_index(index_name):
        raise ValueError(f"Index '{index_name}' does not exist.")
    index = pc.Index(index_name)  # Access the specified index

    # Fetch specific vectors by their IDs
    vector_ids = ["qa_1", "qa_2", "qa_3"]  # Replace with your vector IDs
    fetched_vectors = index.fetch(ids=vector_ids)

    # print("Fetched Vectors:")
    # print(fetched_vectors)

    # # Get index statistics
    # stats = index.describe_index_stats()
    # print("Index Statistics:")
    # print(stats)

    # take one embedding directly from fetched_vectors, and test index.query
    text = "Q: How are you"
    searcher = PineconeSearch(api_key=api_key, index_name=index_name)
    vector_embedding = searcher._generate_embedding(text)
    query_response = index.query(
        vector=vector_embedding,
        top_k=5,
        include_metadata=True,
    )
    print("Query Response:")
    print(query_response)


if __name__ == "__main__":
    # check_saved_data_pinecone()

    delete_index()
    create_index()
