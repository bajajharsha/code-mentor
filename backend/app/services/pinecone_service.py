import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict

import httpx
from fastapi import HTTPException
from pinecone import Pinecone

from app.config.settings import get_settings
from app.utils.logging_util import pinecone_logger, logger

settings = get_settings()

class PineconeService:
    def __init__(self):
        self.pinecone_api_key = settings.PINECONE_API_KEY
        self.api_version = settings.PINECONE_API_VERSION
        self.index_url = settings.PINECONE_CREATE_INDEX_URL
        self.dense_embed_url = settings.PINECONE_EMBED_URL
        self.upsert_url = settings.PINECONE_UPSERT_URL
        self.query_url = settings.PINECONE_QUERY_URL
        self.list_index_url = settings.PINECONE_LIST_INDEXES_URL
        self.semaphore = asyncio.Semaphore(10)
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.timeout = httpx.Timeout(
                        connect=60.0,  # Time to establish a connection
                        read=120.0,    # Time to read the response
                        write=120.0,   # Time to send data
                        pool=60.0      # Time to wait for a connection from the pool
                    )

    async def list_pinecone_indexes(self):
        url = self.list_index_url

        headers = {
            "Api-Key": self.pinecone_api_key,
            "X-Pinecone-API-Version": self.api_version,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:

            logging.error(f"Error creating index: {e.response.text}")
            raise HTTPException(status_code=400, detail=e.response.text)
        except Exception as e:
            logging.error(f"Error creating index: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_index(
        self, index_name: str, dimension: int, metric: str
    ) -> Dict[str, Any]:
        if self.pc.has_index(index_name) == False:
            index_data = {
                "name": index_name,
                "dimension": dimension,
                "metric": metric,
                "spec": {"serverless": {"cloud": "aws", "region": "us-east-1"}},
            }

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Api-Key": self.pinecone_api_key,
                "X-Pinecone-API-Version": self.api_version,
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.index_url, headers=headers, json=index_data
                    )
                    response.raise_for_status()

                    retry_count = 0
                    max_retries = 30
                    while retry_count < max_retries:
                        status = (
                            self.pc.describe_index(index_name)
                            .get("status")
                            .get("state")
                        )
                        logger.info(f"Index status: {status}")

                        if status == "Ready":
                            logger.info(f"Index {index_name} is ready")
                            break

                        retry_count += 1
                        time.sleep(2)

                    if retry_count > max_retries:
                        raise HTTPException(
                            status_code=500, detail="Index creation timed out"
                        )

                    logger.info("Index Created")
                    return response.json()

            except httpx.HTTPStatusError as e:
                parsed_response = json.loads(response.content.decode("utf-8"))
                error_message = parsed_response.get("error", {}).get(
                    "message", "Unknown error occurred"
                )
                logging.error(f"Error creating index: {error_message}")
                raise HTTPException(status_code=400, detail=error_message)
            except Exception as e:
                logging.error(f"Error creating index: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        else:
            logger.info("index already created")
            return {"host": self.pc.describe_index(index_name).get("host")}

    async def upsert_format(
        self, chunks: list, vector_embeddings: list, sparse_embeddings: list
    ):
        results = []
        for i in range(len(chunks)):
            metadata = {key: value for key, value in chunks[i].items() if key != "_id"}

            metadata["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = {
                "id": chunks[i]["_id"],
                "values": vector_embeddings[i],
                "metadata": metadata,
                "sparse_values": {
                    "indices": sparse_embeddings[i]["indices"],
                    "values": sparse_embeddings[i]["values"],
                },
            }
            results.append(result)
        return results

    async def upsert_vectors(self, index_host, input, namespace):

        headers = {
            "Api-Key": self.pinecone_api_key,
            "Content-Type": "application/json",
            "X-Pinecone-API-Version": self.api_version,
        }

        url = self.upsert_url.format(index_host)

        payload = {"vectors": input, "namespace": namespace}
        try:
            async with httpx.AsyncClient(timeout= self.timeout) as client:
                response = await client.post(
                    url=url, headers=headers, json=payload
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logging.error(f"Error in upsert vectors http status error : {str(e)} - {e.response.text}")
            raise HTTPException(status_code=400, detail=e.response.text)    
        
        except httpx.HTTPError as e:    
            logging.error(f"Error in upsert vectors http error : {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

        except Exception as e:
            logging.error(f"Error in upsert vectors : {str(e)} ")
            raise HTTPException(status_code=500, detail=str(e))

    def hybrid_scale(self, dense, sparse, alpha: float):

        if alpha < 0 or alpha > 1:
            raise ValueError("Alpha must be between 0 and 1")
        hsparse = {
            "indices": sparse["indices"],
            "values": [v * (1 - alpha) for v in sparse["values"]],
        }
        hdense = [v * alpha for v in dense]
        return hdense, hsparse

    async def pinecone_hybrid_query(
        self,
        index_host,
        namespace,
        top_k,
        alpha: int,
        query_vector_embeds: list,
        query_sparse_embeds: dict,
        include_metadata: bool,
        filter_dict: dict = None,
    ):

        if query_vector_embeds is None or query_sparse_embeds is None:
            time.sleep(2)

        headers = {
            "Api-Key": self.pinecone_api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Pinecone-API-Version": self.api_version,
        }

        hdense, hsparse = self.hybrid_scale(
            query_vector_embeds, query_sparse_embeds, alpha
        )

        payload = {
            "includeValues": False,
            "includeMetadata": include_metadata,
            "vector": hdense, 
            "sparseVector": {
                "indices": hsparse.get(
                    "indices"
                ),  
                "values": hsparse.get(
                    "values"
                ),  
            },
            "topK": top_k,
            "namespace": namespace,
        }

        if filter_dict:
            payload["filter"] = filter_dict

        url = self.query_url.format(index_host)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                pinecone_logger.info(f"pinecone hybrid query read units: {response.json()['usage']}")
                return response.json()

        except httpx.HTTPError as e:
            if e.response is not None:
                parsed_response = json.loads(e.response.content.decode("utf-8"))
                error_message = parsed_response.get("error", {}).get("message", "Unknown error occurred")
                logging.error(f"Error from Pinecone: {error_message}")
                raise HTTPException(status_code=400, detail=error_message)
            else:
                logging.error(f"HTTP error without response: {str(e)}")
                raise HTTPException(status_code=400, detail="Unknown HTTP error occurred")

        except Exception as e:
            logging.error(f"Error performing hybrid query: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def pinecone_query(
        self,
        index_host: str,
        namespace: str,
        top_k: int,
        vector: list,
        include_metadata: bool,
        filter_dict: dict = None,
    ):

        headers = {
            "Api-Key": self.pinecone_api_key,
            "Content-Type": "application/json",
            "X-Pinecone-API-Version": self.api_version,
        }

        payload = {
            "namespace": namespace,
            "vector": vector,
            "topK": top_k,
            "includeValues": False,
            "includeMetadata": include_metadata,
        }

        if filter_dict:
            payload["filter"] = filter_dict

        url = self.query_url.format(index_host)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                pinecone_logger.info(f"pinecone Normal query read units: {response.json()['usage']}")
                return response.json()


        except httpx.HTTPStatusError as e:
            logger.error(f"httpx status error in pinecone query : {str(e)} - {e.response.text}")
            raise HTTPException(status_code=400, detail=f"httpx status error in pinecone query : {str(e)} - {e.response.text}")

        except httpx.HTTPError as e:
            logging.error(f"Error from Pinecone in pinecone query : {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error from Pinecone in pinecone query : {str(e)} ")
            

        except Exception as e:
            logging.error(f"Error creating index: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
