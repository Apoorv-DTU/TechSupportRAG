from tqdm import tqdm
import json
from query import QueryEngine
from deepeval.metrics import AnswerRelevancyMetric, ContextualRecallMetric, FaithfulnessMetric
from deepeval.models.llms.constants import OPENAI_MODELS_DATA, make_model_data
from deepeval.test_case import LLMTestCase
from deepeval.evaluate import AsyncConfig
from deepeval import evaluate

OPENAI_MODELS_DATA["gpt-5.4-nano"] = make_model_data(
    supports_log_probs=False,
    supports_multimodal=False,
    supports_structured_outputs=True,
    supports_temperature=False,
    supports_json=False,
    input_price=0.20 / 1e6,
    output_price=1.25 / 1e6,)


EVAL_LLM="gpt-5.4-nano"
COLLECTION_NAME="d365_parent_child"

def load_data(test_case_file, read_from_file=True, vector_collection_name=COLLECTION_NAME, rerank=False, hyde=False):
    file_content = ""
    with open("eval_dataset/golden_set.json") as file:
        file_content = file.read()

    answer_relevancy = AnswerRelevancyMetric(model=EVAL_LLM, verbose_mode=False)
    context_recall = ContextualRecallMetric(model=EVAL_LLM, verbose_mode=False)
    faithfulness = FaithfulnessMetric(model=EVAL_LLM, truths_extraction_limit=5, verbose_mode=False)
    
    eval_json = json.loads(file_content)
    tests = []
    tests_dump = []

    if read_from_file:
        print("Reading tests from file")
        with open(test_case_file, 'r') as file:
            json_str = file.read()
            tests_dump = json.loads(json_str)
        
        for case in tests_dump:
            tests.append(
                LLMTestCase(
                input=case['input'],
                retrieval_context=case['retrieval_context'],
                actual_output=case['actual_output'],
                expected_output=case['expected_output']
            ))

    else:
        print("Generating test cases")
        queryEngine = QueryEngine(vector_collection_name)
        for datapoint in tqdm(eval_json[20:30]):
            question = datapoint['question']
            reference = datapoint['answer']
            response, relevant_docs, query_text = queryEngine.query_d365(question, rerank=rerank, hyde=hyde)

            tests.append(
                LLMTestCase(
                input=question,
                retrieval_context=relevant_docs,
                actual_output=response,
                expected_output=reference
            ))

            tests_dump.append({
                "input":question,
                "retrieval_context":relevant_docs,
                "actual_output":response,
                "expected_output":reference,
                "query_text":query_text
            })

        tests_str = json.dumps(tests_dump)
        with open(test_case_file, 'w') as file:
            file.write(tests_str)

    metrics_list = [context_recall, answer_relevancy, faithfulness]
    result = evaluate(test_cases=tests, 
             metrics=metrics_list, 
             async_config=AsyncConfig(run_async=True, throttle_value=3, max_concurrent=5))

    metrics_avgs = [0.0, 0.0, 0.0]
    for test_result in result.test_results:
        for i in range(len(metrics_list)):
            metrics_avgs[i] += test_result.metrics_data[i].score

    metrics_avgs = [m / len(result.test_results) for m in metrics_avgs]
    print(metrics_avgs)
    return metrics_avgs


    # with open('output_faithfulness_15.json', 'w') as file:
    #     file_text = ""
    #     for test_result in result.test_results: 
    #         if test_result.metrics_data[2].score < 1.0:
    #             file_text += f"{str(test_result.metrics_data[2].verbose_logs)}\n"

    #     file.write(file_text)


#m1 = load_data("eval_dataset/rerank_hyde/pc_chunk_tests.json", read_from_file=True, rerank=True, hyde=True)
#m2 = load_data("eval_dataset/rerank/pc_chunk_tests.json", read_from_file=True, rerank=True)
#m3 = load_data("eval_dataset/naive/pc_chunk_tests.json", read_from_file=True)
m4 = load_data("eval_dataset/hyde/pc_chunk_tests_sample.json", read_from_file=False, hyde=True) # [0.5838571428571429, 0.8441666666666666, 0.9051096681096681] -> 50%
print(m4)