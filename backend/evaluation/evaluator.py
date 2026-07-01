from typing import List
import os

# Ensure OpenAI API key is set for evaluators
from backend.config import settings
import nest_asyncio

nest_asyncio.apply()
os.environ["OPENAI_API_KEY"] = settings.openai_api_key.get_secret_value()

def evaluate_with_ragas(question: str, answer: str, contexts: List[str]):
    """
    Evaluates the response using RAGAS.
    RAGAS usually operates on datasets (Dataset from datasets library).
    Here we wrap a single instance for demonstration.
    """
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        
        data_sample = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts]
        }
        dataset = Dataset.from_dict(data_sample)
        
        eval_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        eval_embeddings = OpenAIEmbeddings()
        
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy],
            llm=eval_llm,
            embeddings=eval_embeddings
        )
        return {"ragas": result}
    except Exception as e:
        print(f"RAGAS evaluation error: {e}")
        return {"ragas": {"error": str(e)}}

def evaluate_with_deepeval(question: str, answer: str, contexts: List[str]):
    """
    Evaluates the response using DeepEval metrics.
    """
    try:
        from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
        from deepeval.test_case import LLMTestCase
        
        test_case = LLMTestCase(
            input=question,
            actual_output=answer,
            retrieval_context=contexts
        )
        
        # Faithfulness (formerly Groundedness)
        faithfulness_metric = FaithfulnessMetric(threshold=0.5)
        faithfulness_metric.measure(test_case)
        
        # Relevancy
        relevancy_metric = AnswerRelevancyMetric(threshold=0.5)
        relevancy_metric.measure(test_case)
        
        return {
            "deepeval": {
                "faithfulness_score": faithfulness_metric.score,
                "relevancy_score": relevancy_metric.score
            }
        }
    except Exception as e:
        print(f"DeepEval evaluation error: {e}")
        return {"deepeval": {"error": str(e)}}

def evaluate_response(question: str, answer: str, contexts: List[str]) -> dict:
    """
    Runs both RAGAS and DeepEval metrics.
    """
    if not contexts:
        return {"error": "No contexts retrieved, skipping evaluation."}
        
    results = {}
    ragas_res = evaluate_with_ragas(question, answer, contexts)
    deepeval_res = evaluate_with_deepeval(question, answer, contexts)
    
    results.update(ragas_res)
    results.update(deepeval_res)
    
    return results
