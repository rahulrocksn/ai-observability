# in run_evals.py
import yaml
import requests
import json

AGENT_API_URL = "http://localhost:8000/query" # Assumes your app is running

def run_evaluation():
    with open("evaluation_dataset.yml", "r") as f:
        test_cases = yaml.safe_load(f)

    passed_cases = 0
    total_cases = len(test_cases)
    results = []

    for i, case in enumerate(test_cases):
        print(f"--- Running Case {i+1}/{total_cases}: {case['question']} ---")
        
        try:
            # We need to get the trace data, so we'd ideally get it from Elasticsearch
            # For simplicity here, we'll assume the API could return it or we fetch it.
            # This part requires more advanced integration with your trace store.
            # A simpler approach is to just check the final answer for now.
            
            response = requests.post(AGENT_API_URL, json={"question": case['question']})
            response_data = response.json()
            final_answer = response_data.get("answer", "").lower()

            # Simple check for answer correctness
            answer_correct = all(keyword.lower() in final_answer for keyword in case['expected_answer_keywords'])
            
            if answer_correct:
                passed_cases += 1
                result = "✅ PASSED"
            else:
                result = "❌ FAILED"
            
            print(f"Result: {result}\n")
            results.append({"question": case['question'], "result": result, "answer": final_answer})

        except Exception as e:
            print(f"Error running case: {e}\n")
            results.append({"question": case['question'], "result": "ERROR", "answer": str(e)})

    print("--- EVALUATION SUMMARY ---")
    print(f"Passed {passed_cases}/{total_cases} cases ({ (passed_cases/total_cases)*100 :.2f}% accuracy)")

if __name__ == "__main__":
    run_evaluation()