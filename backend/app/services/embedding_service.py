import json
import logging
import pickle

import httpx
from fastapi import HTTPException, status
from pinecone_text.sparse import BM25Encoder

from app.config.settings import get_settings
from app.utils.logging_util import pinecone_logger, cohere_logger, jina_logger, voyageai_logger, logger

settings = get_settings()

with open("bm25_encoder.pkl", "rb") as f:
    bm25 = pickle.load(f)

class EmbeddingService:
    def __init__(self):
        self.pinecone_api_key = settings.PINECONE_API_KEY
        self.dense_embed_url = settings.PINECONE_EMBED_URL
        self.pinecone_embedding_url = settings.PINECONE_EMBED_URL
        self.pinecone_api_version = settings.PINECONE_API_VERSION
        self.cohere_base_url = settings.COHERE_BASE_URL
        self.cohere_api_key = settings.COHERE_API_KEY
        self.jina_api_key = settings.JINA_API_KEY
        self.togetherai_api_key = settings.TOGETHERAI_API_KEY
        self.voyageai_api_key = settings.VOYAGEAI_API_KEY
        self.jina_base_url = settings.JINA_BASE_URL
        self.togetherai_base_url = settings.TOGETHERAI_BASE_URL
        self.voyageai_base_url = settings.VOYAGEAI_BASE_URL
        self.EMBED_SUFFIX = "embed"
        self.JINA_EMBED_SUFFIX = "embeddings"
        self.timeout = httpx.Timeout(
                        connect=60.0,  # Time to establish a connection
                        read=300.0,    # Time to read the response
                        write=300.0,   # Time to send data
                        pool=60.0      # Time to wait for a connection from the pool
                    )

    async def pinecone_dense_embeddings(
        self,
        inputs: list,
        embedding_model: str = "llama-text-embed-v2",
        input_type: str = "passage",
        truncate: str = "END",
        dimension: int = 1024,
    ):
        payload = {
            "model": embedding_model,
            "parameters": {
                "input_type": input_type,
                "truncate": truncate,
            },
            "inputs": inputs,
        }

        if embedding_model != "multilingual-e5-large":
            payload["parameters"]["dimension"] = dimension 

        headers = {
            "Api-Key": self.pinecone_api_key,
            "Content-Type": "application/json",
            "X-Pinecone-API-Version": self.pinecone_api_version,
        }

        url = self.dense_embed_url

        try:
            async with httpx.AsyncClient(timeout = self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                response = response.json()
                list_result = [item["values"] for item in response["data"]]
                return list_result

        except httpx.HTTPStatusError as e:
            logging.error(f"Error dense embeddings in pinecone dense embeddings: {e.response.text}")
            raise HTTPException(status_code=400, detail=f"{str(e)}-{e.response.text}")
        except Exception as e:
            logging.error(f"Error dense embeddings in pinecone dense embeddings: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def pinecone_sparse_embeddings(self, inputs):
        try:
            sparse_vector = bm25.encode_documents(inputs)
            return sparse_vector

        except Exception as e:
            logging.error(f"Error creating sparse embeddings: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def cohere_dense_embeddings(
        self,
        model_name: str,
        texts: list[str],
        input_type: str = "search_document",
    ):

        url = f"{self.cohere_base_url}/{self.EMBED_SUFFIX}"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.cohere_api_key}",
        }
        data = {
            "model": model_name,
            "texts": texts,
            "input_type": input_type,
            "embedding_types": ["float"],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout,verify=False) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                response = response.json()
                cohere_logger.info(f"cohere hosted embedding model tokens usage: { response.get('meta', {}).get('billed_units', {})}")
                result = response["embeddings"]["float"]
                return result
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e.response.status_code} - {str(e)}")
            raise HTTPException(
                status_code=e.response.status_code, detail=f"{str(e)}-{e.response.text}"
            )
        except httpx.RequestError as e:
            logging.error(f"Request error:  {str(e)}")
            raise HTTPException(
                status_code=502, detail="Failed to connect to API"
            )
        except Exception as e:
            logging.error(f"Error creating dense cohere embeddings {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def jina_dense_embeddings(
        self, model_name: str, dimension: int, inputs: list[str], input_type :str
    ):

        url = f"{self.jina_base_url}/{self.JINA_EMBED_SUFFIX}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.jina_api_key}",
        }
        data = {
            "model": model_name,
            "embedding_type": "float",
            "input": inputs,
        }

        if model_name == "jina-embeddings-v3":
            data["task"] = input_type
            data["late_chunking"] = False
            data['dimensions'] = dimension
        elif model_name == "jina-embeddings-v2-base-code":
            data["normalized"] = True
        else:
            data["normalized"] = True
            data['dimensions'] = dimension

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                response = response.json()
                jina_logger.info(f"jina hosted embedding model tokens usage: {response.get('usage', {})}")
                result = [item["embedding"] for item in response["data"]]
                return result

        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e.response.status_code} - {e.response.content} - {str(e)}")
            raise HTTPException(
                status_code=e.response.status_code, detail=f"{str(e)}, {e.response.text}"
            )
        except httpx.RequestError as e:
            logging.error(f"Request error:  {str(e)}")
            raise HTTPException(
                status_code=502,  # Bad Gateway (Failed to connect)
                detail= f"Failed to connect to API httpx Request error : {str(e)}",
            )
        except Exception as e:
            logging.error(f"Error creating dense jina embeddings {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def togetherai_dense_embeddings(
        self, model_name: str, dimension: int, inputs: list[str], input_type :str
    ):
        url = f"{self.togetherai_base_url}/{self.JINA_EMBED_SUFFIX}"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.togetherai_api_key}",
            "content-type": "application/json"
        }
        payload = {
            "model": model_name,
            "input": inputs
        }

        try:
            async with httpx.AsyncClient(verify = False, timeout = self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error occurred in httpx status error  : {str(e)}")
            raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error:{str(e)} {e.response.text}")
        
        except httpx.HTTPError as e:
            logging.error(f"HTTP request failed in httpx http error : {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"HTTP error in httpx : {str(e)}")
        
        except Exception as e:
            logging.error(f"Unexpected error in togetherai_dense_embedding: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unknown Exception occured : {str(e)}")



    async def voyageai_dense_embeddings(
        self, model_name: str, dimension: int, inputs: list, input_type: str = "document"
    ):
        url = f"{self.voyageai_base_url}/{self.JINA_EMBED_SUFFIX}"
        
        headers = {
            "Authorization": f"Bearer {self.voyageai_api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "input": inputs,
            "model": model_name,
            "input_type": input_type,
            "output_dimension": dimension
        }

        try:

            async with httpx.AsyncClient(verify=False, timeout = self.timeout) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                response = response.json()
                voyageai_logger.info(f"pinecone hosted embedding model tokens usage: {response['usage']}")
                embedding_list = [item["embedding"] for item in response["data"]]
                return embedding_list
            
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error occurred in httpx status error  : {str(e)}")
            logging.error(f"detail message of voyage embed failure: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error occurred in httpx status error  : {str(e)} - {e.response.text}")
        
        except httpx.HTTPError as e:
            logging.error(f"HTTP request failed in httpx http error : {str(e)}")
            logging.error(f"detail message of voyage embed failure: {response.json().get('detail', '')}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"HTTP error in httpx voyage dense embed: {str(e)}")
        
        except Exception as e:
            logging.error(f"Unexpected error in voyageai_dense_embedding: {str(e)}")
            logging.error(f"detail message of voyage embed failure: {response.json().get('detail', '')}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unknown Exception occured in voyageai_dense_embedding: {str(e)}, ")