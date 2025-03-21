import asyncio
import time
import json 

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from app.models.schema.file_upload_schema import FileUploadRequest

from app.config.settings import get_settings
from app.utils.upload_file_local_util import store_file_locally
from app.models.schema.query_schema import QueryRequest

from app.services.query_analysis_pipeline_service import QueryAnalysisPipeline
from app.services.embedding_service import EmbeddingService
from app.services.pinecone_service import PineconeService
from app.services.reranking_service import RerankerService
from app.services.llm_service import LLMService
from app.utils.logging_util import logger, pinecone_logger, voyageai_logger
from app.utils.folder_structure_util import folder_struct_util
import json

from app.prompts.query.response_prompts import (
    RAG_SYSTEM_PROMPT, 
    RAG_USER_PROMPT_TEMPLATE, 
    NON_RAG_SYSTEM_PROMPT, 
    NON_RAG_USER_PROMPT_TEMPLATE,
    STREAMING_SYSTEM_PROMPT, 
    STREAMING_USER_PROMPT_TEMPLATE,
    STREAMING_NON_RAG_SYSTEM_PROMPT,
    STREAMING_NON_RAG_USER_PROMPT_TEMPLATE
    )

from app.prompts.query.compliance_prompts import (
    COMPLIANCE_SYSTEM_PROMPT,
    COMPLIANCE_USER_PROMPT_TEMPLATE
)

settings = get_settings()


class QueryUseCase:
    def __init__(
        self,
        embedding_service: EmbeddingService = Depends(EmbeddingService),
        pinecone_service: PineconeService = Depends(PineconeService),
        reranker_service: RerankerService = Depends(RerankerService),
        qap_service: QueryAnalysisPipeline = Depends(QueryAnalysisPipeline),
        llm_service: LLMService = Depends(LLMService)
    ):
        self.embedding_service = embedding_service
        self.pinecone_service = pinecone_service
        self.reranker_service = reranker_service
        self.qap_service = qap_service
        self.llm_service = llm_service
        self.embedding_model = "voyage-code-3"
        self.reranker_model = "rerank-2"
        self.similarity_metric = "dotproduct"
        self.dimension = 1024
        self.query_input_type = "query"
        self.index_host = "dotproduct-1024-npedpix.svc.aped-4627-b74a.pinecone.io"
        self.llm_model = "claude-3-7-sonnet-20250219"  # Or the latest Claude 3.7 Sonnet model name
        self.top_k = 20  # Number of results to retrieve from vector DB
        self.top_n = 10   # Number of results after reranking
        

    async def get_chunks_by_metadata(
        self,
        index_host: str,
        namespace: str,
        metadata_filter: dict,
        max_results: int = 50
    ):
       
    
        zero_vector = [0.0] * self.dimension
        
        results = await self.pinecone_service.pinecone_query(
            index_host=index_host,
            namespace=namespace,
            top_k=max_results,
            vector=zero_vector,
            include_metadata=True,
            filter_dict=metadata_filter
        )

        matches = results.get("matches",[])
        documents = []
        doc_metadata = []

        for match in matches:
            if match.get("metadata") and match.get("metadata").get("text"):
                documents.append(match["metadata"]["text"])
                doc_metadata.append({
                    "score": match.get("score", 0),
                    "file_path": match.get("metadata", {}).get("file_path", "unknown"),
                    "start_line": match.get("metadata", {}).get("start_line", "unknown"),
                    "end_line": match.get("metadata", {}).get("end_line", "unknown"),
                    "file_name": match.get("metadata", {}).get("file_name", "unknown")
                })

        return documents, doc_metadata


    async def analyze_query(self, query: str):
        logger.info(f"Analyzing query: {query}")
        analysis_result = await self.qap_service.process_query(query)
        logger.info(f"Query analysis complete: use_rag={analysis_result['use_rag']}")
        return analysis_result
    
    async def perform_rag(self, reformulated_query: str, email: str, workspace_name: str):
        # Step 1: Generate embeddings for the query
        logger.info(f"Generating embeddings for query: {reformulated_query}")
        query_embedding = await self.embedding_service.voyageai_dense_embeddings(
            self.embedding_model, 
            dimension= self.dimension,
            inputs = [reformulated_query],
            input_type = self.query_input_type
        )
        query_embedding = query_embedding[0]
        # Step 2: Query Pinecone with the embeddings
        index_name = f"{self.similarity_metric}-{self.dimension}"
        namespace = f"{email}-{workspace_name}"
        index_host = self.index_host
        logger.info(f"Querying Pinecone index {index_name} with embeddings")
        vector_search_results = await self.pinecone_service.pinecone_query(
            index_host = index_host,
            namespace = namespace,
            top_k=self.top_k,
            vector = query_embedding,
            include_metadata = True
        )
        
        if not vector_search_results or not vector_search_results.get("matches"):
            logger.warning("No matches found in vector database")
            return []

        # Step 3: Extract text passages and metadata from results
        documents = []
        doc_metadata = []
        file_paths = []
        for match in vector_search_results.get("matches", []):
            if match.get("metadata") and match.get("metadata").get("text"):
                file_paths.append(match.get("metadata", {}).get("file_path", "unknown"))
                documents.append(match["metadata"]["text"])
                doc_metadata.append({
                    "score": match.get("score", 0),
                    "file_path": match.get("metadata", {}).get("file_path", "unknown"),
                    "start_line": match.get("metadata", {}).get("start_line", "unknown"),
                    "end_line": match.get("metadata", {}).get("end_line", "unknown"),
                    "file_name": match.get("metadata", {}).get("file_name", "unknown")
                })

        unique_file_paths = list(set(file_paths))
            
        if not documents:
            logger.warning("No valid documents found in vector search results")
            return []
        
        filter_dict = {
            "file_path": {"$in": unique_file_paths}
        }
        metadata_documents, metadata_docs_metadata = await self.get_chunks_by_metadata(
            index_host = index_host,
            namespace = namespace,
            metadata_filter = filter_dict,
            max_results = 200
        )
        
        # Step 4: Rerank the documents
        logger.info(f"Reranking {len(documents)} documents")
        reranked_results = await self.reranker_service.voyage_rerank(
            self.reranker_model,
            reformulated_query,
            documents,
            self.top_n
        )
        
        # Step 5: Combine reranked results with metadata
        final_results = []
        for result in reranked_results.get("data", []):
            index = result.get("index")
            if index is not None and 0 <= index < len(doc_metadata):
                final_results.append({
                    "text": documents[index],
                    "relevance_score": result.get("relevance_score", 0),
                    "metadata": doc_metadata[index]
                })
        
        merged_final_results = []
        for i in range(len(metadata_docs_metadata)):
            merged_final_results.append({
                "text": metadata_documents[i],
                "relevance_score": 1.0,
                "metadata": metadata_docs_metadata[i]
            })
        
        full_final_results = final_results + merged_final_results 
        logger.info(f"Retrieved {len(final_results)} relevant documents after reranking")
        return full_final_results

    async def generate_response_with_rag(self, folder_structure,  query: str, reformulated_query: str, retrieved_docs: list, context_from_query: str, error_from_query: str):
        
        retrieved_context_text = ""
        metadata_context_text = ""
        if retrieved_docs:
            retrieved_context_text = "Here are relevant code snippets from the codebase:\n\n"
            for i, doc in enumerate(retrieved_docs[:self.top_n]):
                file_path = doc.get("metadata", {}).get("file_path", "Unknown file")
                retrieved_context_text += f"--- Document {i+1} (from {file_path}) ---\n"
                retrieved_context_text += f"{doc['text']}\n\n"
            
            metadata_context_text = "Here is additional context around the relevant code snippets:\n\n"
            for i, doc in enumerate(retrieved_docs[self.top_n:], start=self.top_n):
                file_path = doc.get("metadata", {}).get("file_path", "Unknown file")
                metadata_context_text += f"--- Document {i+1} (from {file_path}) ---\n"
                metadata_context_text += f"{doc['text']}\n\n"
        
        # Add context from the query analysis if available
        query_context_text = ""
        if context_from_query:
            query_context_text = "Additional context from your message:\n\n"
            query_context_text += f"{context_from_query}\n\n"
        
        # Add error information if available
        error_text = ""
        if error_from_query:
            error_text = "Error information from your message:\n\n"
            error_text += f"{error_from_query}\n\n"
            
        user_prompt = RAG_USER_PROMPT_TEMPLATE.format(
            query = query, 
            query_context_text = query_context_text,
            error_text = error_text,
            retrieved_context_text = retrieved_context_text,
            metadata_context_text = metadata_context_text,
            folder_structure = folder_structure
        )
        
        overall_prompt = RAG_SYSTEM_PROMPT + user_prompt
        logger.info("Generating response with RAG using Claude 3.7 Sonnet")
        response = await self.llm_service.anthropic_api_call(
            model_name=self.llm_model,
            system_prompt=RAG_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            user_query=reformulated_query
        )
        text = response.get("content", [])[0].get("text","")
        return text
    
    async def generate_response_without_rag(self,folder_structure, query: str, reformulated_query: str, context_from_query: str, error_from_query: str):
        """
        Generate a response using Claude 3.7 Sonnet without RAG context
        """
        
        query_context_text = ""
        if context_from_query:
            query_context_text = "Here is some code context you provided:\n\n"
            query_context_text += f"{context_from_query}\n\n"
        
        error_text = ""
        if error_from_query:
            error_text = "Here is the error information you provided:\n\n"
            error_text += f"{error_from_query}\n\n"
        
        user_prompt = NON_RAG_USER_PROMPT_TEMPLATE.format(
            query = query,
            query_context_text = query_context_text,
            error_text = error_text,
            folder_structure = folder_structure
        )
        
        logger.info("Generating response without RAG using Claude 3.7 Sonnet")
        response = await self.llm_service.anthropic_api_call(
            model_name=self.llm_model,
            system_prompt=NON_RAG_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            user_query=reformulated_query
        )
        text = response.get("content", [])[0].get("text","")
        return text
    
    async def check_compliance(self, query: str):

        user_prompt = COMPLIANCE_USER_PROMPT_TEMPLATE.format(
            query = query
        )

        response = await self.llm_service.groq_api_call(
            model_name="gemma2-9b-it",
            system_prompt = COMPLIANCE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        text = response.get("choices",[])[0].get("message",{}).get("content","")
        return text

    
    async def process_query(self, request: QueryRequest):
        start_time = time.time()
        user_query = request.user_query
        current_file_content = request.current_file_content
        email = request.email
        workspace_name = request.workspace_name
        current_file_content = request.current_file_content
        current_file_path = request.current_file_path
        folder_structure = ""

        try:
            with open(f"folder_structs/{email}_{workspace_name}.txt", "r") as f:
                folder_structure = f.read()
                logger.info(f"folder structure : {folder_structure}")
        except FileNotFoundError:
            logger.error("Error: File not found.")
        except Exception as e:
            logger.error(f"Error: {e}")

        groq_response = await self.check_compliance(user_query)

        coding_related_question = "True" in groq_response.split(" ")[0]
        if coding_related_question == False:
            parts = groq_response.split(" ", 1)
            result = parts[1] if len(parts) > 1 else ""

            if len(result) == 0:
                return {"response" : "I am coding assistant created by DhiWise my name is CodeMentor and I am here to help you with your coding related queries only"}
            return {"response" : result}

        # Step 1: Analyze the query to determine if RAG is needed
        analysis_result = await self.analyze_query(user_query)

        use_rag = analysis_result.get("use_rag", True)
        reformulated_query = analysis_result.get("reformulated_query", user_query).get("reformulated_query", user_query)
        user_query = analysis_result.get("orignal_query", user_query)
        
        context_from_query = analysis_result.get("reformulated_query", "").get("context", "")
        error_from_query = analysis_result.get("reformulated_query", "").get("error", "")
        
        if current_file_content and current_file_path:
            final_query = f"this is {user_query} and this is enhanced query if incase user query is not sufficient {reformulated_query}, current file path is this (Current file: {current_file_path}) and current file content is this {current_file_content}"
        else:
            final_query = f"this is {user_query} and this is enhanced query if incase user query is not sufficient {reformulated_query}"
        # Step 2: Generate response based on RAG decision
        
        if use_rag:
            retrieved_docs = await self.perform_rag(final_query, email, workspace_name)
            
            response = await self.generate_response_with_rag(
                folder_structure,
                user_query, 
                reformulated_query, 
                retrieved_docs,
                context_from_query,
                error_from_query
            )
        else:
            response = await self.generate_response_without_rag(
                folder_structure,
                user_query, 
                reformulated_query,
                context_from_query,
                error_from_query
            )
        
        # Step 3: Format and return the final response
        end_time = time.time()
        processing_time = end_time - start_time
        
        return {
            "response": response ,#response.get("content", [{}])[0].get("text", ""),
            "analysis": analysis_result,
            "processing_time": processing_time,
            "used_rag": use_rag,
            "model": self.llm_model
        }
    


    
    async def stream_response_generator(self, query: str, reformulated_query: str, retrieved_docs: list, context_from_query: str, error_from_query: str):
        """
        Generate a streaming response for RAG
        """
        
        # Format the retrieved documents as context
        retrieved_context_text = ""
        if retrieved_docs:
            retrieved_context_text = "Here are relevant code snippets from the codebase:\n\n"
            for i, doc in enumerate(retrieved_docs[:10]):  # Limit to 10 docs for streaming
                file_path = doc.get("metadata", {}).get("file_path", "Unknown file")
                retrieved_context_text += f"--- Document {i+1} (from {file_path}) ---\n"
                retrieved_context_text += f"{doc['text']}\n\n"
        
        # Add context from the query analysis if available
        query_context_text = ""
        if context_from_query:
            query_context_text = "Additional context from your message:\n\n"
            query_context_text += f"{context_from_query}\n\n"
        
        # Add error information if available
        error_text = ""
        if error_from_query:
            error_text = "Error information from your message:\n\n"
            error_text += f"{error_from_query}\n\n"
            
        user_prompt = STREAMING_USER_PROMPT_TEMPLATE.format(
            query = query,
            query_context_text = query_context_text,
            error_text = error_text,
            retrieved_context_text = retrieved_context_text
        )
        
        logger.info("Generating streaming response")
        async for chunk in self.llm_service.anthropic_api_call_streaming(
            model_name=self.llm_model,
            system_prompt=STREAMING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            user_query=reformulated_query
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    async def process_query_streaming(self, request: QueryRequest):
        """
        Process a query request and generate a streaming response
        """
        user_query = request.user_query
        email = request.email
        workspace_name = request.workspace_name
        current_file_content = request.current_file_content
        current_file_path = request.current_file_path
        
        # Check if query is coding-related
        groq_response = await self.check_compliance(user_query)
        coding_related_question = "True" in groq_response.split(" ")[0]
        
        if coding_related_question == False:
            parts = groq_response.split(" ", 1)
            result = parts[1] if len(parts) > 1 else ""
            if len(result) == 0:
                result = "I am coding assistant created by DhiWise my name is CodeMentor and I am here to help you with your coding related queries only"
            # Return a non-streaming response for non-coding questions
            return StreamingResponse(
                self._string_to_generator(result),
                media_type="text/event-stream"
            )
            
        # Step 1: Analyze the query to determine if RAG is needed
        analysis_result = await self.analyze_query(user_query)
        use_rag = analysis_result.get("use_rag", True)
        reformulated_query = analysis_result.get("reformulated_query", user_query).get("reformulated_query", user_query)
        
        # Extract additional context
        context_from_query = analysis_result.get("reformulated_query", "").get("context", "")
        error_from_query = analysis_result.get("reformulated_query", "").get("error", "")
        
        # Add current file context if available
        if current_file_content and current_file_path:
            final_query = f"{user_query} (Current file: {current_file_path})"
        else:
            final_query = user_query
            
        # Step 2: Generate streaming response based on RAG decision
        if use_rag:
            # Perform RAG retrieval
            retrieved_docs = await self.perform_rag(final_query, email, workspace_name)
            
            # Return streaming response with retrieved documents
            return StreamingResponse(
                self.stream_response_generator(
                    user_query, 
                    reformulated_query, 
                    retrieved_docs,
                    context_from_query,
                    error_from_query
                ),
                media_type="text/event-stream"
            )
        else:
            # Generate streaming response without RAG
            return StreamingResponse(
                self.stream_non_rag_generator(
                    user_query, 
                    reformulated_query,
                    context_from_query,
                    error_from_query
                ),
                media_type="text/event-stream"
            )
    
    async def stream_non_rag_generator(self, query: str, reformulated_query: str, context_from_query: str, error_from_query: str):
        """Stream response without RAG context"""
        
        # Add context from the query analysis if available
        query_context_text = ""
        if context_from_query:
            query_context_text = "Here is some code context you provided:\n\n"
            query_context_text += f"{context_from_query}\n\n"
        
        # Add error information if available
        error_text = ""
        if error_from_query:
            error_text = "Here is the error information you provided:\n\n"
            error_text += f"{error_from_query}\n\n"
        
        user_prompt = STREAMING_NON_RAG_USER_PROMPT_TEMPLATE.format(
            query = query,
            query_context_text = query_context_text,
            error_text = error_text
        )
        
        logger.info("Generating streaming response without RAG")
        async for chunk in self.llm_service.anthropic_api_call_streaming(
            model_name=self.llm_model,
            system_prompt=STREAMING_NON_RAG_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            user_query=reformulated_query
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    async def _string_to_generator(self, text: str):
        """Helper to convert a string to a streaming generator"""
        yield f"data: {json.dumps({'text': text, 'done': False})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
        
        
        