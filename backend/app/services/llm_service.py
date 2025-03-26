import httpx
from fastapi import HTTPException, status
from app.config.settings import get_settings
from app.utils.logging_util import logger, openai_logger, anthropic_logger, groq_logger
import time
import json

settings = get_settings()
class LLMService():
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.groq_api_key = settings.GROQ_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        self.openai_base_url = settings.OPENAI_BASE_URL
        self.groq_base_url = settings.GROQ_BASE_URL
        self.openai_chat_url = f"{self.openai_base_url}/chat/completions"
        self.groq_chat_url = f"{self.groq_base_url}/chat/completions"
        self.anthropic_chat_url = f"{settings.ANTHROPIC_BASE_URL}/messages"
        self.anthropic_version = "2023-06-01"
        self.timeout = httpx.Timeout(
                        connect=60.0,  # Time to establish a connection
                        read=300.0,    # Time to read the response
                        write=300.0,   # Time to send data
                        pool=60.0      # Time to wait for a connection from the pool
                    )



    async def openai_api_call(self, model_name, system_prompt, user_prompt, **params):
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            **params
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                s = time.perf_counter()
                response = await client.post(self.openai_chat_url, headers=headers, json=payload)
                e = time.perf_counter()
                response_time = e - s
                response.raise_for_status()
                response_data = response.json()
                
            
                result = response_data["choices"][0]["message"]["content"]
                usage = response_data["usage"]
                openai_logger.info(f"openai response token usage : {usage}")
                return response_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"httpx status error in openai api call : {str(e)} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"httpx status error in openai api call : {str(e)} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"httpx request error in openai api call : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"httpx request error in openai api call : {str(e)}"
            )
        except httpx.HTTPError as e:
            logger.error(f"httpx http error in openai api call : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"httpx http error in openai api call : {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error in openai api call : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in openai api call : {str(e)}"
            )
        

    async def anthropic_api_call(self, model_name, system_prompt, user_prompt, user_query, **params):
        
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": self.anthropic_version,
            "content-type": "application/json"
        }

        final_prompt = f"{user_prompt}, here is the query : {user_query}"

        payload = {
            "model": model_name,
            "max_tokens":  64000,
            "messages": [
                # {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_prompt}
            ],
            **params
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.post(self.anthropic_chat_url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()
                anthropic_logger.info(f"anthropic response token usage : {response_data.get('usage', {})}")
                return response_data
        except httpx.HTTPStatusError as e:
            logger.error(f"httpx status error in anthropic api call : {str(e)} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"httpx status error in anthropic api call : {str(e)} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"httpx request error in anthropic api call : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"httpx request error in anthropic api call : {str(e)}"
            )
        except httpx.HTTPError as e:
            logger.error(f"httpx http error in anthropic api call : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"httpx http error in anthropic api call : {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error in anthropic api call : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in anthropic api call : {str(e)}"
            )



    async def groq_api_call(self, model_name, system_prompt, user_prompt, **params):

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.groq_api_key}"
        }

        # final_prompt = f"{user_prompt}, here is the query : {user_query}"

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            **params
        }

        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(self.groq_chat_url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()
                groq_logger.info(f"groq response token usage : {response_data.get('usage', {})}")
                return response_data
        except httpx.HTTPStatusError as e:
            logger.error(f"httpx status error in groq api call : {str(e)} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"httpx status error in groq api call : {str(e)} - {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"httpx request error in groq api call : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"httpx request error in groq api call : {str(e)}"
            )
        except httpx.HTTPError as e:
            logger.error(f"httpx http error in groq api call : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"httpx http error in groq api call : {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error in groq api call : {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in groq api call : {str(e)}"
            )
        
    
    async def anthropic_api_call_streaming(self, model_name, system_prompt, user_prompt, user_query):
        """
        Make a streaming API call to Anthropic API
        """
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": self.anthropic_version,
            "content-type": "application/json"
        }

        final_prompt = f"{user_prompt}, here is the query : {user_query}"

        payload = {
            "model": model_name,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": final_prompt}
            ],
            "system": system_prompt,
            "stream": True
        }

        async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
            try:
                async with client.stream("POST", self.anthropic_chat_url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Error from Anthropic API: {error_text.decode()}"
                        )
                        
                    # Process streaming response
                    async for line in response.aiter_lines():
                        # Skip empty lines
                        if not line or line.isspace():
                            continue
                            
                        # Handle SSE format
                        if line.startswith('event:'):
                            event_type = line.split(':', 1)[1].strip()
                            continue
                            
                        if line.startswith('data:'):
                            data_str = line[5:].strip()
                            # Check if we have valid data
                            if not data_str:
                                continue
                                
                            try:
                                data = json.loads(data_str)
                                
                                # Handle different event types
                                if data.get("type") == "content_block_delta":
                                    delta = data.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        text = delta.get("text", "")
                                        if text:
                                            yield {"text": text, "done": False}
                                            
                                elif data.get("type") == "message_stop":
                                    yield {"done": True}
                                    
                            except json.JSONDecodeError as e:
                                logger.error(f"Error parsing JSON: {e}, Line: {line}")
                                continue
                    
                    # Final done message
                    yield {"done": True}
                    
            except httpx.RequestError as e:
                logger.error(f"Request error in streaming anthropic api call: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Request error in streaming anthropic api call: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Error in streaming anthropic api call: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error in streaming anthropic api call: {str(e)}"
                )
        
    # async def anthropic_api_call_streaming(self, model_name, system_prompt, user_prompt, user_query):
    #     """
    #     Make a streaming API call to Anthropic API
    #     """
    #     headers = {
    #         "x-api-key": self.anthropic_api_key,
    #         "anthropic-version": self.anthropic_version,
    #         "content-type": "application/json"
    #     }

    #     final_prompt = f"{user_prompt}, here is the query : {user_query}"

    #     payload = {
    #         "model": model_name,
    #         "max_tokens": 1024,
    #         "messages": [
    #             {"role": "user", "content": final_prompt}
    #         ],
    #         "system": system_prompt,
    #         "stream": True
    #     }

    #     async with httpx.AsyncClient(timeout=self.timeout) as client:
    #         try:
    #             async with client.stream("POST", self.anthropic_chat_url, headers=headers, json=payload) as response:
    #                 if response.status_code != 200:
    #                     error_text = await response.aread()
    #                     raise HTTPException(
    #                         status_code=response.status_code,
    #                         detail=f"Error from Anthropic API: {error_text.decode()}"
    #                     )
                        
    #                 # Process the streaming response
    #                 buffer = b""
    #                 async for chunk in response.aiter_bytes():
    #                     buffer += chunk
                        
    #                     # Check if we have complete events
    #                     if b"\n\n" in buffer:
    #                         events = buffer.split(b"\n\n")
    #                         # Keep the last incomplete event in the buffer
    #                         buffer = events.pop() if not buffer.endswith(b"\n\n") else b""
                            
    #                         for event in events:
    #                             if not event or event.startswith(b":"):  # Skip empty lines or comments
    #                                 continue
                                    
    #                             try:
    #                                 if event.startswith(b"data: "):
    #                                     event = event[6:]  # Remove "data: " prefix
                                    
    #                                 if event == b"[DONE]":
    #                                     yield {"done": True}
    #                                     continue
                                        
    #                                 data = json.loads(event)
                                    
    #                                 # Extract the relevant content from the model response
    #                                 if "content_block" in data and "text" in data["content_block"]:
    #                                     yield {"text": data["content_block"]["text"], "done": False}
    #                                 elif "delta" in data and "text" in data["delta"]:
    #                                     yield {"text": data["delta"]["text"], "done": False}
    #                                 elif "content" in data and len(data["content"]) > 0:
    #                                     yield {"text": data["content"][0]["text"], "done": False}
                                        
    #                             except Exception as e:
    #                                 logger.error(f"Error parsing event: {str(e)}, Event: {event}")
    #                                 continue
                            
    #                 # Process any remaining data in buffer
    #                 if buffer and not buffer.startswith(b":") and buffer != b"[DONE]":
    #                     try:
    #                         data = json.loads(buffer)
    #                         if "content_block" in data and "text" in data["content_block"]:
    #                             yield {"text": data["content_block"]["text"], "done": False}
    #                         elif "delta" in data and "text" in data["delta"]:
    #                             yield {"text": data["delta"]["text"], "done": False}
    #                         elif "content" in data and len(data["content"]) > 0:
    #                             yield {"text": data["content"][0]["text"], "done": False}
    #                     except:
    #                         pass
                            
    #                 yield {"done": True}
                    
    #         except httpx.RequestError as e:
    #             logger.error(f"Request error in streaming anthropic api call: {str(e)}")
    #             raise HTTPException(
    #                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                 detail=f"Request error in streaming anthropic api call: {str(e)}"
    #             )
    #         except Exception as e:
    #             logger.error(f"Error in streaming anthropic api call: {str(e)}")
    #             raise HTTPException(
    #                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                 detail=f"Error in streaming anthropic api call: {str(e)}"
    #             )
        
