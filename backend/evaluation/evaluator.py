from typing import List
import os

from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

# Ensure OpenAI API key is set for evaluators
from backend.config import settings
import nest_asyncio

os.environ["OPENAI_API_KEY"] = settings.openai_api_key.get_secret_value()

async def evaluate_response(question: str, answer: str, contexts: List[str]) -> dict:
    """
    Evaluates the response using DeepEval metrics asynchronously.
    """
    if not contexts:
        return {"error": "No contexts retrieved, skipping evaluation."}
        
    try:
        test_case = LLMTestCase(
            input=question,
            actual_output=answer,
            retrieval_context=contexts
        )
        
        # Faithfulness (formerly Groundedness)
        faithfulness_metric = FaithfulnessMetric(threshold=0.5, model="o3-mini")
        await faithfulness_metric.a_measure(test_case)
        
        # Relevancy
        relevancy_metric = AnswerRelevancyMetric(threshold=0.5, model="o3-mini")
        await relevancy_metric.a_measure(test_case)
        
        return {
            "faithfulness": faithfulness_metric.score,
            "relevancy": relevancy_metric.score
        }
    except Exception as e:
        print(f"DeepEval evaluation error: {e}")
        return {"error": str(e)}
