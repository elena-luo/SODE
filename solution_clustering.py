import json
import os
from redlines import Redlines
import re
import copy
from prompts import complete_answer, clustering_instruction, answer_simplification_instruction

class Solution_clustering:
    def __init__(self, file_name, input, status="clustering", is_upload_odps=False):
        self.file_name = file_name  # name prefix for saving
        self.input = input
        self.status = status
        self.is_upload_odps = is_upload_odps

    def parse_clusters(self, text):
        pattern = r'cluster(\d+) \[(.*?)\] (TOGETHER A COMPLETE SOLUTION|.*?)(?=\s*cluster|\Z)'
        matches = re.findall(pattern, text, re.DOTALL)

        result = {}
        for match in matches:
            cluster_number = f"cluster{match[0]}"
            solutions = [sol.strip() for sol in match[1].split(',')]
            is_complete_solution = match[2] == 'TOGETHER A COMPLETE SOLUTION'

            result[cluster_number] = {
                'solutions': solutions,
                'is_complete_solution': is_complete_solution
            }

        return result

    def merge_dicts(self, dicts):
        from collections import defaultdict

        merged = defaultdict(list)

        for d in dicts:
            for key, value in d.items():
                merged[key].append(value)

        result = {}
        for key, values in merged.items():
            if len(values) > 1:
                for i, value in enumerate(values):
                    new_key = f"{key}{i + 1}"
                    result[new_key] = value
            else:
                result[key] = values[0]

        return result

    def clustering(self, data):
        match_info = {}
        data = list(data.values())

        with open(self.file_name + "_clustering.jsonl", "w", encoding="utf-8") as fw:
            for j in range(len(data)):
                d = data[j]['split_result_part4_formate']
                id = data[j]["id"]
                m = {"final_split": d, "prompt": data[j]["prompt"]}
                solution = []
                i = 1
                if d.get("Solution_Explore"):
                    for k in d.get("Solution_Explore"):
                        s = f"Solution{i}:" + json.dumps(d["Solution_Explore"][k], ensure_ascii=False)
                        solution.append(s)
                        m[f"Solution{i}"] = k
                        i += 1

                if d.get("Verify"):
                    for k in d.get("Verify"):
                        s = f"Solution{i}:" + d["Verify"][k]
                        solution.append(s)
                        m[f"Solution{i}"] = k
                        i += 1
                Conclusion = d.get("Conclusion")
                if not Conclusion:
                    # if id != 785021:
                    print(d.keys())
                    Conclusion = ""
                clustering_instruction_prompt = clustering_instruction.replace("[question text here]", data[j]["prompt"]).replace("[conclusion text here]", Conclusion).replace("[solution text here]", "\n".join(solution))
                prompt = f"<|im_start|>user\n{clustering_instruction_prompt}\n<|im_end|>\n<|im_start|>assistant\n"
                line = {"id": id, "prompt": prompt, "answer": "", "tag": data[j]["task_l2"]}
                fw.write(json.dumps(line, ensure_ascii=False) + "\n")
                match_info[id] = m.copy()
        return match_info

    def run(self, info = {}):
        if self.status == "clustering":
            data = {}
            with open(self.input, "r") as f:
                for line in f.readlines():
                    line = json.loads(line)
                    data[line["id"]] = line
        
            complete_answer_result = []
            with open(f"R1_split_part2_filtered_complete_answer.jsonl", "r") as f:
                for d in f.readlines():
                    complete_answer_result.append(json.loads(d))

            complete_answer_dic = {}
            for c in complete_answer_result:
                complete_answer_dic[int(c["id"])] = c

            def parse_output(content):
                lines = content.split('\n')
                result = {}

                for line in lines:
                    if line.startswith('1. **Answer to Question 1:**'):
                        result['Answer to Question 1'] = line.split('**Answer to Question 1:**')[1].strip().replace(" ", "") == 'Yes'
                    elif line.startswith('2. **Answer to Question 2:**'):
                        answer = line.split('**Answer to Question 2:**')[1].strip().replace(" ", "")
                        result['Answer to Question 2'] = None if answer == 'N/A' else (answer == 'Yes')
                    elif line.startswith('3. **Answer to Question 3:**'):
                        result['Answer to Question 3'] = line.split('**Answer to Question 3:**')[1].strip().replace(" ", "") == 'Yes'
                    elif line.startswith('4. **Answer to Question 4:**'):
                        result['Answer to Question 4'] = line.split('**Answer to Question 4:**')[1]
                        pattern = r'"(.*?)"'
                        matches = re.findall(pattern, result['Answer to Question 4'])
                        result['Answer to Question 4'] = matches
                return result

            fw = open(self.file_name+"_complete_answer_output.jsonl", "w", encoding="utf-8")
            result_count = {"bad": 0}
            # {'bad': 1,
            #  'False_None_True': 1378,
            #  'True_True_False': 1260,
            #  'True_False_True': 2,
            #  'False_None_False': 4,
            #  'True_True_True': 2}
            temp_save = []
            for id in data.keys():
                data[id]['split_result_part4_formate'] = copy.deepcopy(data[id]["split_result_part3_formate"])
                if complete_answer_dic.get(id):
                    result = complete_answer_dic.get(id)["result"]
                    result_reformate = parse_output(result)
                    try:
                        result_reformate["Answer to Question 1"]
                        result_reformate["Answer to Question 2"]
                        result_reformate["Answer to Question 3"]
                        result_reformate["Answer to Question 4"]
                    except:
                        print(result_reformate)
                        result_count["bad"] += 1
                        continue
                    if result_reformate["Answer to Question 3"] and not result_reformate["Answer to Question 1"]:
                        temp_save.append(id)
                        k = list(data[id]['split_result_part4_formate']["Solution_Explore"].keys())[-1]
                        v_ks = list(data[id]['split_result_part4_formate']["Verify"].keys())
                        print(list(data[id]['split_result_part4_formate']["Verify"].keys()))
                        print(list(data[id]['split_result_part3_formate']["Verify"]))
                        print(id)
                        need_keys = result_reformate['Answer to Question 4']
                        max_need_index = -1
                        for need_key in need_keys:
                            try:
                                max_need_index = max(max_need_index, v_ks.index(need_key))
                            except:
                                print(f"{need_key} is not in Verify part")
                        if max_need_index >= 0:
                            for need_key in v_ks[:max_need_index + 1]:
                                data[id]['split_result_part4_formate']["Solution_Explore"][k][need_key] = \
                                data[id]['split_result_part4_formate']["Verify"][need_key]
                                del data[id]['split_result_part4_formate']["Verify"][need_key]
                    if result_count.get(str(result_reformate["Answer to Question 1"]) +"_"+str(result_reformate["Answer to Question 2"]) +"_"+str(result_reformate["Answer to Question 3"]) ):
                        result_count[str(result_reformate["Answer to Question 1"]) +"_"+str(result_reformate["Answer to Question 2"]) +"_"+str(result_reformate["Answer to Question 3"]) ] +=1
                    else:
                        result_count[str(result_reformate["Answer to Question 1"]) +"_"+str(result_reformate["Answer to Question 2"]) +"_"+str(result_reformate["Answer to Question 3"]) ] = 1
                fw.write(json.dumps(data[id], ensure_ascii=False)+"\n")
            fw.close()
            match_info = self.clustering(data)
            return match_info
        elif self.status == "clustering_extract":
            data = {}
            with open(self.input, "r") as f:
                for line in f.readlines():
                    line = json.loads(line)
                    data[line["id"]] = line
            
            correctness_data = {}
            with open("R1_split_part2_filtered_solution_classification.jsonl", "r") as f:
                for line in f.readlines():
                    line = json.loads(line)
                    correctness_data[line["id"]] = line
            with open(self.file_name + "_clustering.jsonl", "r") as f:
                clustering_result = [json.loads(d) for d in f.readlines()]
            clustering_result_dic = {}
            for c in clustering_result:
                clustering_result_dic[int(c["id"])] = c
            fw = open(self.file_name+"_need_filter.jsonl", "w", encoding="utf-8")
            aaa = 0
            for id in data.keys():
                # data[id]['split_result_part5_formate'] = copy.deepcopy(data[id]["split_result_part4_formate"])
                if not clustering_result_dic.get(id):
                    data[id]["Drop_Multipilation"] = []
                    fw.write(json.dumps(data[id], ensure_ascii=False) + "\n")
    #             output = """cluster1 [Solution1, Solution2] TOGETHER A COMPLETE SOLUTION
    # cluster2 [Solution3] verifying the solution through numerical examples
    # cluster3 [Solution4] providing an alternative conceptual approach"""
                else:
                    output = clustering_result_dic[id]["result"]
                    result = self.parse_clusters(output)
                    drop_solutions = []
                    for cluster, dic in result.items():
                        solutions = dic["solutions"]
                        is_complete_solution = dic["is_complete_solution"]
                        for i in range(len(solutions)):
                            if i > 0:
                                drop_solution_num = solutions[i]
                                try:
                                    drop_solution_key = info[id][drop_solution_num.replace(" ", "")]
                                    if drop_solution_key.startswith("Solution"):
                                        drop_solution = json.dumps(
                                            info[id]["final_split"]["Solution_Explore"][drop_solution_key],
                                            ensure_ascii=False)
                                    else:
                                        drop_solution = info[id]["final_split"]["Verify"][drop_solution_key]
                                    drop_solutions.append(f"Drop because of multipilation in method: {drop_solution}")
                                except:
                                    print(drop_solution_num)
                                    aaa += 1
                                    print(aaa)
                    data[id]["Drop_Multipilation"] = drop_solutions
                    data[id]["cluster"] = result
                    if not correctness_data.get(id):
                        data[id]["incorrect_solution"] = []
                        data[id]["incomplete_solution"] = []
                    else:
                        if correctness_data[id]["real_num_solutions"] != correctness_data[id]["num_solutions"]:
                            data[id]["incorrect_solution"] = []
                            data[id]["incomplete_solution"] = []
                        else:
                            incorrect_solution = []
                            incomplete_solution = []
                            num = correctness_data[id]["real_num_solutions"]
                            for i in range(num):

                                label = correctness_data[id][f"solution{i+1}"]["label1"].lower()
                                if label == "incorrect":
                                    incorrect_solution.append(f'Drop because of incorrectness in method: {json.dumps(data[id]["split_result_part4_formate"]["Solution_Explore"][f"Solution{i+1}"])}')
                                elif label == "incomplete":
                                    incomplete_solution.append(f'Drop because of incompleteness in method: {json.dumps(data[id]["split_result_part4_formate"]["Solution_Explore"][f"Solution{i+1}"])}')
                                elif label != "correct":
                                    print(label, "不为指定格式！")
                                else:
                                    print("error in cluster extract")
                            data[id]["incorrect_solution"] = incorrect_solution
                            data[id]["incomplete_solution"] = incomplete_solution
                    fw.write(json.dumps(data[id], ensure_ascii=False) +"\n")
            fw.close()
            print("aaa: ", aaa)
        elif self.status == "complete_answer":
            data = []
            with open(self.input, "r") as f:
                for line in f.readlines():
                    line = json.loads(line)
                    data.append(line)

            with open(self.file_name + "_complete_answer.jsonl", "w", encoding="utf-8") as fw:
                for j in range(len(data)):
                    id = data[j]["id"]
                    d = data[j]['split_result_part3_formate']
                    if d.get("Conclusion"):
                        ground_truth = d.get("Conclusion")
                    else:
                        ground_truth = data[j]["ground_truth"]
                    prompt = data[j]["prompt"]
                    solution_part1 = "".join(d["Solution_Explore"][list(d["Solution_Explore"].keys())[-1]].values())
                    solution_part2 = json.dumps(d["Verify"], ensure_ascii=False)

                    pattern = complete_answer.replace("[Insert the first part of the response here]", solution_part1).replace("[Insert the second part of the response here]",
                                                                                 solution_part2).replace(
                        "[Insert the correct answer here]", ground_truth).replace("[Insert the mathematical problem here]", prompt)
                    prompt = f"<|im_start|>user\n{pattern}\n<|im_end|>\n<|im_start|>assistant\n"
                    line = {"id": id, "prompt": prompt, "answer": "", "tag": data[j]["task_l2"]}
                    fw.write(json.dumps(line, ensure_ascii=False) + "\n")

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--status',
        type=str,
        choices=['complete_answer', 'clustering', 'clustering_extract'],
        required=True,
        help="choices include 'complete_answer', 'clustering', 'clustering_extract'"
    )
    
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    if args.status == 'complete_answer':
        file_name = "R1_split_part2_filtered"
        input = "R1_split_part2_filtered.jsonl"
        status = args.status
        op = Solution_clustering(file_name, input, status)
        op.run()
    elif args.status == 'clustering':
        file_name = "R1_split_part2_filtered"
        input = "R1_split_part2_filtered.jsonl"
        status = args.status
        op = Solution_clustering(file_name, input, status)
        match_info = op.run()
        with open("match_info.jsonl", "w") as fw:
            for d in match_info:
                fw.write(json.dumps(d, ensure_ascii=False) + "\n")

    elif args.status == 'clustering_extract':
        file_name = "R1_split_part2_filtered"
        input = "R1_split_part2_filtered_complete_answer_output.jsonl"
        status = "clustering_extract"
        op = Solution_clustering(file_name, input, status)
        with open("match_info.jsonl", "r") as fr:
            match_info = [json.loads(line) for line in fr.readlines()]
        result = op.run(match_info)