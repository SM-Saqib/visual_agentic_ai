from pinecone import Pinecone
import boto3
from PyPDF2 import PdfReader
from typing import List, Dict
import json
import openai
import os
from dotenv import load_dotenv

load_dotenv()
PINE_API_KEY = os.getenv("PINE_API_KEY")
PINE_INDEX_NAME = os.getenv("PINE_INDEX_NAME")


class PineconeDataImporter:
    def __init__(
        self,
        api_key: str,
        index_name: str,
        # aws_access_key: str,
        # aws_secret_key: str,
        # aws_region: str,
    ):
        """
        Initialize the PineconeDataImporter with Pinecone and AWS credentials.

        Args:
            api_key (str): Pinecone API key.
            index_name (str): Name of the Pinecone index.
            aws_access_key (str): AWS access key for S3.
            aws_secret_key (str): AWS secret key for S3.
            aws_region (str): AWS region for S3.
        """
        self.api_key = api_key
        self.index_name = index_name

        # Initialize Pinecone
        pinecone = Pinecone(api_key=self.api_key)

        print(pinecone.list_indexes().names())
        if not pinecone.list_indexes() or self.index_name not in list(
            pinecone.list_indexes().names()
        ):
            raise ValueError(f"Index '{self.index_name}' does not exist in Pinecone.")
        self.index = pinecone.Index(self.index_name)

        # # Initialize AWS S3 client
        # self.s3_client = boto3.client(
        #     "s3",
        #     aws_access_key_id=self.aws_access_key,
        #     aws_secret_access_key=self.aws_secret_key,
        #     region_name=self.aws_region,
        # )

    def upsert_single_row(
        self,
        record_id: str,
        text: str,
        metadata: Dict[str, str],
        category: str,
        embedding_required: bool = False,
    ) -> None:
        """
        Upsert a single row into Pinecone.

        Args:
            record_id (str): Unique ID for the record.
            text (str): Text to be embedded and stored.
            metadata (Dict[str, str]): Metadata associated with the record.
            category (str): Category of the record.
            embedding_required (bool): Whether to generate an embedding for the text. Defaults to False.
        """
        # Generate embedding if required
        embedding = None
        if embedding_required:
            embedding = self._generate_embedding(text)
            if embedding is None:
                print(f"Failed to generate embedding for record ID: {record_id}")
                return

        # Prepare the record for upsertion
        record = {
            "id": record_id,
            "values": embedding if embedding_required else None,
            "metadata": {
                "chunk_text": text,
                "metadata": metadata,
                "category": category,
            },
        }

        # Upsert the record into Pinecone
        self.index.upsert(vectors=[record])
        print(f"Upserted record with ID: {record_id}")

    def upsert_all_rows(
        self,
        record_id: List[str],
        list_of_text: List[str],
        metadata_list: Dict[str, str],
        category: str,
        embedding_required: bool = False,
    ) -> None:
        """
        Upsert a single row into Pinecone.

        Args:
            record_id (str): Unique ID for the record.
            text (str): Text to be embedded and stored.
            metadata (Dict[str, str]): Metadata associated with the record.
            category (str): Category of the record.
            embedding_required (bool): Whether to generate an embedding for the text. Defaults to False.
        """
        # Generate embedding if required
        embedding = None
        if embedding_required:
            embeddings = self._generate_bulk_embedding_using_pinecone(list_of_text)
            if embeddings is None or len(embeddings) != len(list_of_text):
                print("Failed to generate embedding for record ID")
                return

            vectors = []
            for id, d, e, m in zip(record_id, list_of_text, embeddings, metadata_list):
                vectors.append(
                    {
                        "id": id,
                        "values": e,
                        "metadata": {
                            "chunk_text": d,
                            "metadata": m,
                            "category": category,
                        },
                    }
                )
            self.index.upsert(vectors=vectors, namespace=PINE_INDEX_NAME)

    def process_pdf(self, pdf_path: str) -> None:
        """
        Process a PDF file page by page and upsert each page into Pinecone.

        Args:
            pdf_path (str): Path to the PDF file.
        """
        reader = PdfReader(pdf_path)
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text:
                record_id = f"{pdf_path}_page_{page_number}"
                metadata = {"source": pdf_path, "page_number": str(page_number)}
                self.upsert_single_row(record_id, text, metadata, category="pdf_page")
        print(f"Processed and upserted all pages from PDF: {pdf_path}")

    def process_text_file(self, text_file_path: str) -> None:
        """
        Process a text file line by line and upsert each line into Pinecone.

        Args:
            text_file_path (str): Path to the text file.
        """
        with open(text_file_path, "r") as file:
            for line_number, line in enumerate(file, start=1):
                record_id = f"{text_file_path}_line_{line_number}"
                metadata = {"source": text_file_path, "line_number": str(line_number)}
                self.upsert_single_row(
                    record_id, line.strip(), metadata, category="text_file"
                )
        print(f"Processed and upserted all lines from text file: {text_file_path}")

    # def bulk_import_from_s3(self, bucket_name: str, s3_path: str) -> None:
    #     """
    #     Perform a bulk import from AWS S3 to Pinecone.

    #     Args:
    #         bucket_name (str): Name of the S3 bucket.
    #         s3_path (str): Path to the directory in the S3 bucket.
    #     """
    #     uri = f"s3://{bucket_name}/{s3_path}"
    #     # Retrieve objects from S3 and upsert them into Pinecone
    #     response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_path)
    #     if "Contents" in response:
    #         for obj in response["Contents"]:
    #             file_key = obj["Key"]
    #             file_obj = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)
    #             file_content = file_obj["Body"].read().decode("utf-8")
    #             record_id = file_key
    #             metadata = {"source": f"s3://{bucket_name}/{file_key}"}
    #             self.upsert_single_row(record_id, file_content, metadata)
    #     print(f"Processed and upserted all files from S3 path: {uri}")

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

    def _generate_bulk_embedding_using_pinecone(
        self, text_list: List[str]
    ) -> List[float]:
        """
        Generate an embedding for the given text using OpenAI's embedding model.

        Args:
            text (str): Text to generate an embedding for.

        Returns:
            List[float]: The generated embedding.
        """
        try:
            print(f"Generating embeddings for {len(text_list)} texts.")
            pc = Pinecone(api_key=self.api_key)
            embeddings = pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=text_list,
                parameters={"input_type": "passage"},
            )

            embeddings_list = [embedding["values"] for embedding in embeddings]

            # assert that embeddings_list has the same length as text_list
            assert len(embeddings_list) == len(text_list)

            print(f"Generated embeddings for {len(text_list)} texts.")

            return embeddings_list
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    api_key = os.getenv("PINE_API_KEY")
    index_name = os.getenv("PINE_INDEX_NAME")

    importer = PineconeDataImporter(
        api_key=api_key,
        index_name=index_name,
    )

    sales_records = [
        {
            "record_id": "1",
            "text": "Customer purchased a Smooth UltraBlend 5000 blender.",
            "metadata": {"source": "sales_database"},
            "category": "sales",
        },
        {
            "record_id": "2",
            "text": "Customer inquired about the warranty for Smooth AirMax Pro air purifiers.",
            "metadata": {"source": "customer_support"},
            "category": "inquiry",
        },
    ]

    for record in sales_records:
        importer.upsert_single_row(
            record["record_id"],
            record["text"],
            record["metadata"]["source"],
            record["category"],
        )

    print("Upserted sales records into Pinecone.")
