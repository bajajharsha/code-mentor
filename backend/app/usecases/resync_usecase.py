import asyncio
import time
import json 
import os

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from app.models.schema.file_upload_schema import FileUploadRequest

from app.config.settings import get_settings
from app.utils.upload_file_local_util import store_file_locally
from app.utils.folder_structure_util import folder_struct_util

from app.services.embedding_service import EmbeddingService
from app.services.pinecone_service import PineconeService
from app.services.reranking_service import RerankerService
from app.utils.logging_util import logger



settings = get_settings()

class ResyncUseCase:
    def __init__(
        self,
        embedding_service: EmbeddingService = Depends(EmbeddingService),
        pinecone_service: PineconeService = Depends(PineconeService),
        reranker_service: RerankerService = Depends(RerankerService),
    ):
        self.embedding_service = embedding_service
        self.pinecone_service = pinecone_service
        self.reranker_service = reranker_service
        self.file_path = "uploads/raw_dataset.json"
        self.chunk_size = 90
        self.semaphore = asyncio.Semaphore(5)
        self.upsert_batch_size = 90
        self.process_batch_size = 90
        self.embed_model_name = "voyage-code-3"
        self.dimension = 1024
        self.similarity_metric = "dotproduct"

    async def process_chunk(self, chunk, embed_model, dimension = 1024):
        async with self.semaphore:
            try:
                embeddings = await self.embedding_service.voyageai_dense_embeddings(
                    embed_model, dimension, chunk
                )
                return embeddings
            except Exception as e:
                logger.error(
                    f"Error processing chunk while embedding it : {str(e)}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error processing chunk while embedding it : {str(e)}"
                )

    async def _get_embeddings_for_batch(self, data_batch, embed_model,  dimension = 1024):
        try:
            inputs = [item.get('text', item.get("code")) for item in data_batch]

            chunks = [
                inputs[i : i + self.chunk_size]
                for i in range(0, len(inputs), self.chunk_size)
            ]

            tasks = [
                self.process_chunk(
                    chunk, embed_model, dimension
                )
                for chunk in chunks 
            ]

            chunk_results = await asyncio.gather(*tasks)
            all_embeddings = []
            for embeddings in chunk_results:
                all_embeddings.extend(embeddings)
            return all_embeddings
        except Exception as e:
            logger.error(f"Error getting embeddings for batch : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting embeddings for batch : {str(e)}"
            )

    
    async def _upsert_batch(self, index_host, batch, namespace_name):
        try:
            upsert_result = await self.pinecone_service.upsert_vectors(
                index_host, batch, namespace_name
            )
            return upsert_result
        except Exception as e:
            logger.error(f"Error upserting batch : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error upserting batch : {str(e)}"
            )

    async def _process_and_upsert_batch(
        self,
        data_batch,
        embed_model,
        dimension, 
        index_host, 
        namespace_name
    ):
        try:
            embeddings = await self._get_embeddings_for_batch(data_batch, embed_model, dimension)

            text_list = [item["text"] for item in data_batch]
            sparse_embeds = self.embedding_service.pinecone_sparse_embeddings(text_list)

            upsert_data = await self.pinecone_service.upsert_format(data_batch, embeddings, sparse_embeds)

            upsert_batches = [
                upsert_data[i : i + self.upsert_batch_size]
                for i in range(0, len(upsert_data), self.upsert_batch_size)
            ]

            upsert_tasks = [
                self._upsert_batch(index_host, batch, namespace_name)
                for batch in upsert_batches
            ]

            batch_results = await asyncio.gather(*upsert_tasks)

            total_upserted = sum(result.get("upserted_count", 0) for result in batch_results)

            return {
                "upserted_count": total_upserted,
                "batches_processed": len(batch_results),
                "message": "Batch upserted successfully",
            }
        except Exception as e:
            logger.error(f"Error processing and upserting batch : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing and upserting batch : {str(e)}"
            )

    async def _process_data_in_batches(self, data, embed_model, dimension, index_host, namespace_name):
        try:
            processing_batches = [
                data[i : i + self.process_batch_size]
                for i in range(0, len(data), self.process_batch_size)
            ]

            logger.info(f"Processing {len(data)} items in {len(processing_batches)} batches")
            
            total_results = {
                "upserted_count": 0,
                "batches_processed": 0,
                "batch_results": []
            }

            for i, batch in enumerate(processing_batches):
                logger.info(f"Processing batch {i+1}/{len(processing_batches)} with {len(batch)} items")
                
                batch_result = await self._process_and_upsert_batch(
                    batch, embed_model, dimension, index_host, namespace_name
                )
                
                # Update totals
                total_results["upserted_count"] += batch_result["upserted_count"]
                total_results["batches_processed"] += batch_result["batches_processed"]
                total_results["batch_results"].append(batch_result)
                
                logger.info(f"Completed batch {i+1}: upserted {batch_result['upserted_count']} vectors")
            
            time.sleep(5) # add a delay to allow pinecone to upsert vectors in background
            return total_results

        except Exception as e:
            logger.error(f"Error processing data in batches : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing data in batches : {str(e)}"
            )


    async def resync_index(self, file, file_request: FileUploadRequest):
        file_path_local = await store_file_locally(file, file)

        try:
            with open(file_path_local, "r") as f:
                data = json.load(f)

            email = file_request.email
            file_path = file_request.filepath
            is_first_time = file_request.is_first_time

            namespace_name = f"{email}-{file_path}"
            index_name = f"{self.similarity_metric}-{self.dimension}"
            list_index_result = await self.pinecone_service.list_pinecone_indexes()
            indexes = list_index_result.get("indexes", [])
            index_names = [index.get("name") for index in indexes]

            if len(indexes) == 0 or index_name not in index_names:
                response = await self.pinecone_service.create_index(
                    index_name=f"{self.similarity_metric}-{self.dimension}",
                    dimension=self.dimension,
                    metric=self.similarity_metric
                )

                index_host = response.get("host")

                upsert_result = await self._process_data_in_batches(
                    data, self.embed_model_name, self.dimension, index_host, namespace_name
                )
            
            else:
                for index in indexes:
                    if index.get("name") == index_name:
                        index_host = index.get("host")
                        break

                upsert_result = await self._process_data_in_batches(
                    data, self.embed_model_name, self.dimension, index_host, namespace_name
                )
        
            # comment this code if backend breaks
            folder_structure = folder_struct_util()
            os.makedirs("folder_structs", exist_ok=True)
            with open(f"folder_structs/{email}_{file_path}.txt", "w") as f:
                f.write(folder_structure)
        finally:
            # Ensure the local file is deleted after processing
            if os.path.exists(file_path_local):
                os.remove(file_path_local)
        
        return {
            "filepath": file_path,
            "data": file_request.model_dump(),
            "message": "Resynced successfully",
            "upsert_result": upsert_result
        }

