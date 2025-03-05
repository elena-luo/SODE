import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import SOLUTION_CLASSIFICATION_PROMPT
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import json
import re
from openai import OpenAI

MAX_API_RETRY = 10
def get_response(prompt, system_prompt="you're a helpful ai assistant", model_name="gpt-4o-0806"):
    i, correct = 0, False
    client = OpenAI(
        api_key="", # fill in with your own openai api key and url
        base_url="",
    )
    j = 0
    while j < MAX_API_RETRY and not correct:
        j += 1
        messages = [{"role": "system", "content": system_prompt}]
        # role = list(dialog_prompt.keys())
        messages.append({"role": "user", "content": prompt})

        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=8192,
                temperature=0.8,
                # top_p=1,  # openai suggest altering top_p or temperature but not both
                n=1,  # completion choices to generate for each input message.
            )
            response = completion.choices[0].message.content
            return  response.replace("```json", "").replace("```",""), completion
        except Exception as e:
            print(e)
    return response.replace("```json", "").replace("```",""), completion

def get_solution_classification(js):
    question = js['prompt']
    ground_truth = js['ground_truth']
    solutions = js['split_result_part4_formate']['Solution_Explore']
    formatted_solutions = ""
    cnt = 0
    for i in range(100):  # less than 100 solutions
        if f'Solution{i+1}' in solutions:
            solution_js = solutions[f'Solution{i+1}']
            solution = "".join([solution_js[key] for key in solution_js])
            formatted_solutions += f"Solution{i+1}:\n{solution}\n\n"
            cnt += 1
        else:
            break
    prompt = SOLUTION_CLASSIFICATION_PROMPT.format(question, ground_truth, formatted_solutions)
    return (get_response(prompt), cnt)


def analyse_response(text):
    solution_pattern = re.compile(r"## Solution (\d+)\s*(.*?)(?=## Solution \d+|\Z)", re.DOTALL)
    
    # match label1 and label2
    label_pattern = re.compile(r"<label(\d+)>(.*?)</label(\d+)>")
    
    result = {'num_solutions': 0}
    
    solutions = solution_pattern.findall(text)
    result['num_solutions'] = len(solutions)
    
    for i, solution in enumerate(solutions, 1):
        solution_number, explanation = solution
        solution_dict = {}

        labels = label_pattern.findall(explanation)
        for label in labels:
            label_id = int(label[0])
            label_content = label[1].strip()
            
            if label_id == 1:
                solution_dict['label1'] = label_content
            elif label_id == 2:
                if 'label2' not in solution_dict:
                    solution_dict['label2'] = []
                solution_dict['label2'].append(label_content)
        
        # match explanation part
        explanation_for_label1 = re.search(r'Explanation for label1:(.*?)(?=<label2>|Quoted erroneous parts:|$)', explanation, re.DOTALL)
        if explanation_for_label1:
            solution_dict['explanation for label1'] = explanation_for_label1.group(1).strip()


        explanation_for_label2 = re.search(r'Explanation for label2:(.*)', explanation, re.DOTALL)
        if explanation_for_label2:
            explanation_label2 = explanation_for_label2.group(1).strip()
            explanation_label2 = re.sub(r'Quoted erroneous parts:.*', '', explanation_label2).strip()
            solution_dict['explanation for label2'] = explanation_label2
        
        quoted_erroneous_parts = re.search(r'Quoted erroneous parts:(.*)', explanation, re.DOTALL)
        if quoted_erroneous_parts:
            solution_dict['quoted_erroneous_parts'] = quoted_erroneous_parts.group(1).strip()
        
        result[f'solution{solution_number}'] = solution_dict

    return result

def parallel_LLM_check(js_list, max_workers=20):
    responses = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_prompt = {executor.submit(get_solution_classification, js): js for js in js_list}
        for future in tqdm(as_completed(future_to_prompt), total=len(js_list)):
            js = future_to_prompt[future]
            try:
                (response, completion), cnt = future.result()
                if response:
                    d = analyse_response(response)
                    new_d = {
                        'id': js['id'], 
                        'real_num_solutions': cnt, 
                        **d,
                        'raw_response': response
                        }
                    responses.append(new_d)
                else:
                    print(f"Failed to get response for js id {js['id']}")
            except Exception as e:
                print(f"js id {js['id']} generated an exception: {e}")
    return responses


if __name__ == '__main__':
    js_list = []
    with open("R1_split_part2_filtered_complete_answer_output.jsonl", "r") as f:
        cnt = 0
        for line in f:
            js = json.loads(line)
            js_list.append(js)
            cnt += 1
    print("total:", cnt)

    responses = parallel_LLM_check(js_list)
    for i in range(len(responses)):
        for js in js_list:
            if js['id'] == responses[i]['id']:
                responses[i]['solutions'] = js['split_result_part4_formate']['Solution_Explore']
                responses[i]['ground_truth'] = js['ground_truth']
                break
    
    with open("R1_split_part2_filtered_solution_classification.jsonl", "w") as f:
        for js in responses:
            f.write(json.dumps(js, ensure_ascii=False) + '\n')