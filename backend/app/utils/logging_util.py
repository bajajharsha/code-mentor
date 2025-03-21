import logging
import os 

os.makedirs("logs", exist_ok=True)

pinecone_logger = logging.getLogger("pinecone")
pinecone_logger.setLevel(logging.INFO)
pinecone_handler = logging.FileHandler("logs/pinecone_usage.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
pinecone_handler.setFormatter(formatter)
pinecone_logger.addHandler(pinecone_handler)

cohere_logger = logging.getLogger("cohere")
cohere_logger.setLevel(logging.INFO)
cohere_handler = logging.FileHandler("logs/cohere_usage.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
cohere_handler.setFormatter(formatter)
cohere_logger.addHandler(cohere_handler)

jina_logger = logging.getLogger("jina")
jina_logger.setLevel(logging.INFO)
jina_handler = logging.FileHandler("logs/jina_usage.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
jina_handler.setFormatter(formatter)
jina_logger.addHandler(jina_handler)

openai_logger = logging.getLogger("openai")
openai_logger.setLevel(logging.INFO)
openai_handler = logging.FileHandler("logs/openai_usage.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
openai_handler.setFormatter(formatter)
openai_logger.addHandler(openai_handler)

voyageai_logger = logging.getLogger("voyageai")
voyageai_logger.setLevel(logging.INFO)
voyageai_handler = logging.FileHandler("logs/voyageai_usage.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
voyageai_handler.setFormatter(formatter)
voyageai_logger.addHandler(voyageai_handler)


evaluation_logger = logging.getLogger("evaluation")
evaluation_logger.setLevel(logging.INFO)
evaluation_handler = logging.FileHandler("logs/evaluation_metrices_time.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
evaluation_handler.setFormatter(formatter)
evaluation_logger.addHandler(evaluation_handler)

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("logs/main.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

anthropic_logger = logging.getLogger("anthropic")
anthropic_logger.setLevel(logging.INFO)
anthropic_handler = logging.FileHandler("logs/anthropic_usage.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
anthropic_handler.setFormatter(formatter)
anthropic_logger.addHandler(anthropic_handler)

groq_logger = logging.getLogger("groq")
groq_logger.setLevel(logging.INFO)
groq_handler = logging.FileHandler("logs/groq_usage.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
groq_handler.setFormatter(formatter)
groq_logger.addHandler(groq_handler)


