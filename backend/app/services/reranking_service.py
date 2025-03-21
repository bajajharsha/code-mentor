import json
import logging

import httpx
from fastapi import HTTPException

from app.config.settings import get_settings
from app.utils.logging_util import pinecone_logger, cohere_logger, jina_logger, voyageai_logger, logger

settings = get_settings()


class RerankerService:
    def __init__(self):
        self.pinecone_api_key = settings.PINECONE_API_KEY
        self.cohere_api_key = settings.COHERE_API_KEY
        self.jina_api_key = settings.JINA_API_KEY
        self.voyage_api_key=settings.VOYAGEAI_API_KEY
        self.pinecone_rerank_url = settings.PINECONE_RERANK_URL
        self.pinecone_api_version = settings.PINECONE_API_VERSION
        self.cohere_base_url = settings.COHERE_BASE_URL
        self.jina_base_url = settings.JINA_BASE_URL
        self.voyage_base_url=settings.VOYAGEAI_BASE_URL
        self.RERANK_SUFFIX = "rerank"
        self.timeout = httpx.Timeout(
                        connect=60.0,  # Time to establish a connection
                        read=120.0,    # Time to read the response
                        write=120.0,   # Time to send data
                        pool=60.0      # Time to wait for a connection from the pool
                    )

    async def pinecone_reranker(
        self, model_name: str, query: str, documents: list, top_n: int
    ):

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Pinecone-API-Version": self.pinecone_api_version,
            "Api-Key": self.pinecone_api_key,
        }

        payload = {
            "model": model_name,
            "query": query,
            "return_documents": True,
            "top_n": top_n,
            "documents": documents,
            "parameters": {
                "truncate": "END",
            },
        }

        url = self.pinecone_rerank_url

        try:
            async with httpx.AsyncClient(timeout = self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                logging.info("reranking done")
                pinecone_logger.info(f"Reranking model hosted by Pinecone tokens usage : {response.json()['usage']}")
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

    async def cohere_rerank(
        self, model_name: str, query: str, documents: list, top_n: int
    ):
        rerank_url = f"{self.cohere_base_url}/{self.RERANK_SUFFIX}"

        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "Authorization": f"bearer {self.cohere_api_key}",
        }

        payload = {
            "model": model_name,
            "query": query,
            "top_n": top_n,
            "documents": documents,
        }

        try:
            async with httpx.AsyncClient(verify=False, timeout = self.timeout) as client:
                response = await client.post(
                    rerank_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                logging.info("reranking done by cohere")
                cohere_logger.info(f"Reranking model hosted by Cohere tokens usage : {response.json().get('meta',{}).get('billed_units', {})}")
                return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e.response.status_code} - {str(e)}")
            raise HTTPException(
                status_code=e.response.status_code, detail=str(e)
            )
        except httpx.RequestError as e:
            logging.error(f"Request error:  {str(e)}")
            raise HTTPException(
                status_code=502, detail="Failed to connect to API"
            )
        except Exception as e:
            logging.error(f"Error in reranking in cohere {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def jina_rerank(
        self, model_name: str, query: str, documents: list, top_n: int
    ):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.jina_api_key}",
        }

        payload = {
            "model": model_name,
            "query": query,
            "top_n": top_n,
            "documents": documents,
        }

        rerank_url = f"{self.jina_base_url}/{self.RERANK_SUFFIX}"

        try:
            async with httpx.AsyncClient(verify=False, timeout = self.timeout) as client:
                response = await client.post(
                    rerank_url, headers=headers, json=payload
                )
                response.raise_for_status()
                logging.info("reranking done by jina")
                jina_logger.info(f"Reranking model hosted by Jina tokens usage : {response.json().get('usage', {})}")
                return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e.response.status_code} - {str(e)}")
            raise HTTPException(
                status_code=e.response.status_code, detail=str(e)
            )
        except httpx.RequestError as e:
            logging.error(f"Request error:  {str(e)}")
            raise HTTPException(
                status_code=502, detail="Failed to connect to API"
            )
        except Exception as e:
            logging.error(f"Error in reranking in jina {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        

    async def voyage_rerank(
            self, model_name: str, query: str, documents: list, top_n: int
    ):
        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.voyage_api_key}",
        }

        payload = {
            "model": model_name,
            "query": query,
            "top_k": top_n,
            "documents": documents,
        }

        rerank_url = f"{self.voyage_base_url}/{self.RERANK_SUFFIX}"

        try:
            async with httpx.AsyncClient(verify=False, timeout = self.timeout) as client:
                response = await client.post(
                    rerank_url, headers=headers, json=payload
                )
                response.raise_for_status()
                logging.info("reranking done by voyage")
                voyageai_logger.info(f"Reranking model hosted by Voyage tokens usage : {response.json().get('usage', {})}")
                jina_logger.info(f"Reranking model hosted by Voyage tokens usage : {response.json().get('usage', {})}")
                return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e.response.status_code} - {e.response.text} - {str(e)}")
            raise HTTPException(
                status_code=e.response.status_code, detail = f"HTTP error: {e.response.status_code} - {e.response.text} - {str(e)}"
            )
        except httpx.RequestError as e:
            logging.error(f"Request error:  {str(e)}")
            raise HTTPException(
                status_code=502, detail="Failed to connect to API"
            )
        except Exception as e:
            logging.error(f"Error in reranking in Voyage {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
