
import random, json
import re
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts.answer_simplification import ANSWER_SIMPLIFICATION_PROMPT
from tqdm import tqdm


# find the index of first correct solution
def find_first_correct_index(js):
    for i in range(1, js['num_solutions']+1):
        if f"solution{i}" in js and js[f"solution{i}"]["label1"] == "Correct":
            return i
    return -1

# Identify the cluster to which the current solution belongs, and return it after sorting.
def find_cluster_by_index(cluster, index):
    target = None
    for key, c in cluster.items():
        if f"Solution{index}" in c["solutions"]:
            target = c
    if target is not None:
        return sorted(target['solutions'])
    else:
        return None

def simplify_solutions(js):
    # find the index of first correct solution
    deleted_set = set()
    first_correct_index = find_first_correct_index(js)
    if first_correct_index == -1:
        return None  # no correct solution: skip
    veri_nums = len(js['verifications']) 
    if veri_nums > 0:
        first_verify_index = js['num_solutions']+1
    else:
        first_verify_index = -1
    # handle the redundancy
    for index in range(1, first_correct_index+1):
        if index in deleted_set:
            continue
        cur_cluster = find_cluster_by_index(js['cluster'], index)
        if cur_cluster == None:
            print(f"cur_cluster is None for solution{index} in question id{js['id']}")
            break
        for solution in cur_cluster[1:]:  # consider deleting only non-first solution
            match = re.search(r'Solution(\d+)', solution)
            if match:
                i = int(match.group(1))
                if i >= 1 and i <= first_correct_index and js[f"solution{i}"]["label1"] == "Correct":
                    continue  # If it is a part that contains the correct path and is correct, do not delete it.
                deleted_set.add(i) 
            else:
                print(f"index analysis failed in {cur_cluster} in question id{js['id']}")
    
    # Handle the redundancy outside of the main path
    for index in range(first_correct_index+1, first_verify_index+veri_nums):
        if index in deleted_set:
            continue
        cur_cluster = find_cluster_by_index(js['cluster'], index)
        if cur_cluster is None:
            print(f"cur_cluster is None for solution{index} in question id{js['id']}")
            continue
        for solution in cur_cluster[1:]: 
            match = re.search(r'Solution(\d+)', solution)
            if match:
                i = int(match.group(1))
            deleted_set.add(i)

    delete_set_for_incorrection = set() # The complete solution that was deleted due to label2 will be placed in the "incorrect_parts" section of the final json file
    # Handle the erroneous parts at the label1 level.
    js["incorrect_parts"] = {}
    for i in range(1, js['num_solutions']):
        if js[f"solution{i}"]["label2"][0] == "Calculation and Derivation Error":
            if i >= 1 and i <= first_correct_index: # If it is on the main path, only delete the erroneous parts
                js["incorrect_parts"][f"solution{i}"] = js[f"solution{i}"]["quoted_erroneous_parts"]
            else:  
                if js[f"solution{i}"]["label1"] == "Correct": # If it is not on the main path but yields a correct result, only delete the erroneous parts to ensure diversity
                    js["incorrect_parts"][f"solution{i}"] = js[f"solution{i}"]["quoted_erroneous_parts"]
                else:  # If it is not on the main path and does not yield a correct result, delete the entire solution
                    if i not in deleted_set:
                        delete_set_for_incorrection.add(i)


    tmp = 1
    for key, veri in js['verifications'].items():
        js["solutions"][f"Solution{tmp+js['num_solutions']}"] = veri
        tmp += 1
    js["solution_to_delete"] = {
        key: js['solutions'][f'Solution{key}'] for key in deleted_set if f'Solution{key}' in js['solutions']
    }
    for i in delete_set_for_incorrection:
        js["incorrect_parts"][f"solution{i}"] = js['solutions'][f"Solution{i}"]

    js["first_correct_solution_index"] = first_correct_index
    js["first_verify_solution_index"] = first_verify_index
    return js

def collect_data():
    f_ori = open("data/R1_split_part2_filtered_complete_answer_output.jsonl", "r")
    f_classification = open("R1_split_part2_filtered_solution_classification.jsonl", "r")
    js_c_list = [json.loads(line) for line in f_classification.readlines()]
    js_ori_list = [json.loads(line) for line in f_ori.readlines()]
    f_cluster = open("data/R1_split_part2_filtered_need_filter.jsonl", "r")
    js_cluster_list = [json.loads(line) for line in f_cluster.readlines()]
    target = []
    for js_c in js_c_list:
        for js_ori in js_ori_list:
            if js_c["id"] == js_ori["id"]:
                js_c["question"] = js_ori["prompt"]
                js_c["full_cot"] = js_ori["result"]
                js_c['verifications'] = js_ori["split_result_part4_formate"]["Verify"]
                js_c["task_l2"] = js_ori["task_l2"]
                target.append(js_c)
    for js_t in target:
        for js_cluster in js_cluster_list:
            if js_t["id"] == js_cluster["id"]:
                js_t["cluster"] = js_cluster["cluster"]
    # save
    with open("data/R1_split_part2_ablation.jsonl", "w") as f:
        for js in target:
            f.write(json.dumps(js, ensure_ascii=False) + "\n")

    f_ori.close()
    f_classification.close()
    f_cluster.close()

    with open("data/R1_split_part2_ablation.jsonl", "r") as f:
        js_list = [json.loads(line) for line in f.readlines()]
        for js in js_list:
            for key in js['cluster']:
                for i in range(len(js['cluster'][key]["solutions"])):
                    js['cluster'][key]["solutions"][i] = js['cluster'][key]["solutions"][i].replace(" ", "")
                    if not js['cluster'][key]["solutions"][i].startswith("Solution"):
                        print("id: ", js["id"])
    # save
    with open("data/R1_split_part2_ablation.jsonl", "w") as f:                
        for js in js_list:
            f.write(json.dumps(js, ensure_ascii=False) + "\n")


# final intermediate data format
'''
{
    "incorrect_parts": {"solution1": "...", "solution2": "...", ...},
    "solution_to_delete": {"solution1": "...", "solution2": "...", ...},
    "first correct solution": 2  (solution number)
    "first verify solution": 4  (first verify solution number)
}
'''

class IncorrectnessSimplifier:
    def __init__(self, input_file, output_prefix, label1_setting, label2_setting, is_upload_odps=False):
        self.input_file = input_file
        self.output_prefix = output_prefix
        self.label1_setting = label1_setting
        self.label2_setting = label2_setting
        self.is_upload_odps = is_upload_odps
    
    def run(self):
        with open(self.input_file, "r") as f:
            data = [json.loads(line) for line in f.readlines()]
        print(len(data))
        for s_label1 in self.label1_setting:
            for s_label2 in self.label2_setting:
                fw = open(f"{self.output_prefix}_{s_label1}_{s_label2}_need_simplize.jsonl", "w", encoding="utf-8")
                for js in tqdm(data):
                    problem = js["question"]
                    full_cot = js["full_cot"]
                    prompt = ANSWER_SIMPLIFICATION_PROMPT.replace("[Mathematical problem here]", problem+"\n\n").replace("[Original answer here]", full_cot+"\n\n")
                    """ - **Mathematical Problem:** [Mathematical problem here]  
                        - **Answer:** [Original answer here]  
                        - **Part to Remove:** [Removed Part]"""
                    solution_to_delete = ""
                    if s_label1 == "keep_one_global":
                        parts = []
                        for key, value in js["solution_to_delete"].items():
                            if isinstance(value, dict):
                                parts.append("".join(list(value.values())))
                            elif isinstance(value, str):
                                parts.append(value)
                        solution_to_delete_part1 = "\n\n\n\n".join(parts)
                    else:
                        pass
                    if s_label2 == "delete_all":
                        parts = []
                        for key, value in js["incorrect_parts"].items():
                            if isinstance(value, dict):
                                parts.append("".join(list(value.values())))
                            elif isinstance(value, str):
                                parts.append(value)
                        solution_to_delete_part2 = "\n\n\n\n" + "\n\n\n\n".join(parts)
                    elif s_label2 == "delete_solution":  # only delete entire solution
                        parts = []
                        for _ , value in js["incorrect_parts"].items():
                            if isinstance(value, dict):
                                parts.append("".join(list(value.values())))
                        solution_to_delete_part2 = "\n\n\n\n" + "\n\n\n\n".join(parts)
                    else: 
                        pass
                    solution_to_delete = solution_to_delete_part1 + solution_to_delete_part2
                    prompt = prompt.replace("[Removed Part]", solution_to_delete+"\n\n")
                    prompt = f"<|im_start|>user\n{prompt}\n<|im_end|>\n<|im_start|>assistant\n"
                    line = {"id": js["id"], "prompt": prompt, "answer": "", "tag": js["task_l2"]}
                    fw.write(json.dumps(line, ensure_ascii=False) +"\n")
                fw.close()

if __name__ == "__main__":
    collect_data()
    models = ["R1"]
    for model_name in models:
        with open(f"data/{model_name}_split_part2_ablation.jsonl", "r") as f:
            js_list = [json.loads(line) for line in f.readlines()]
        output_list = []
        for js in tqdm(js_list):
            if js["num_solutions"] != js["real_num_solutions"]:  
                continue
            output_list.append(simplify_solutions(js))
        with open(f"data/{model_name}_split_part2_ablation_filtered.jsonl", "w") as f:
            for js in output_list:
                if js is not None:
                    f.write(json.dumps(js, ensure_ascii=False) + "\n")
        simplifier = IncorrectnessSimplifier(f"data/{model_name}_split_part2_ablation_filtered.jsonl", f"data/{model_name}_split_part2_ablation_need_simplize", ["keep_one_global"], ["delete_solution"], is_upload_odps=True)
        simplifier.run()

