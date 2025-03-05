from tqdm import tqdm
import json
import os
import difflib
from prompts import pattern_split_instruction_1, Solution_Explore_split_instruction, Verification_split_instruction

class AnswerSplitOperator():
    def __init__(self, partition, part, stat=""):
        self.input_partition = partition
        self.part = part
        self.stat = stat
        
    def part1_split(self, split_result):
        result = {}
        current_key = None
        current_value = []
        split_result = split_result.split("\n# Structure")[0]
        lines = split_result.split("\n")

        for line in lines:
            if line.startswith('## '):
                if current_key is not None:
                    result[current_key] = '\n'.join(current_value).strip()
                    current_value = []
                # a new title
                current_key = line[3:].strip()
            else:
                if current_key is not None:
                    # content under current title
                    current_value.append(line)

        # last one
        if current_key is not None:
            result[current_key] = '\n'.join(current_value).strip()

        return result

    def solution_explore_split(self, split_result):
        result = {}
        current_key = None
        current_value = []
        split_result = split_result.split("\n# Structure")[0]
        split_result = split_result.split("\n# structure")[0]
        lines = split_result.split("\n")

        for line in lines:
            # print(line)
            if line.startswith('## '):
                if current_key is not None:
                    if sub_current_key is not None and sub_current_value != []:
                        sub_result[sub_current_key] = '\n'.join(sub_current_value).strip()
                    result[current_key] = sub_result
                current_key = line[3:].strip()
                sub_result = {}
                sub_current_key = None
                sub_current_value = []
            else:
                if current_key is not None:
                    if line.startswith('### '):
                        if sub_current_key is not None:
                            sub_result[sub_current_key] = '\n'.join(sub_current_value).strip()
                            sub_current_value = []
                        sub_current_key = line[4:].strip()
                    else:
                        if sub_current_key is not None:
                            sub_current_value.append(line)
        if current_key is not None:
            if sub_current_key is not None and sub_current_value != []:
                sub_result[sub_current_key] = '\n'.join(sub_current_value).strip()
            result[current_key] = sub_result

        return result

    def find_str_in_list(self, A, B):
        for index, element in enumerate(B):
            if A in element:
                return index
        return -1

    def jaccard_similarity(self, A, B):
        A = set(A.replace("\n", "").split(" "))
        B = set(B.replace("\n", "").split(" "))
        intersection = A.intersection(B)
        union = A.union(B)
        return len(intersection) / len(union)

    def split_refine(self, data):
        Solution_Explore_save = []
        Verify_Explore_save = []
        split_dic_save = []
        for d in tqdm(data):
            try:
                # dict_keys(['id', 'prompt', 'task_l1', 'task_l2', 'ground_truth', 'result', 'split_result'])
                # get_response(d)
                result = d['result']
                result_list = result.split(".")
                split_result = d["split_result"]
                if self.part == "basic_structure":
                    split_dic = self.part1_split(split_result)
                    pre_key = None
                    for k, v in split_dic.items():
                        # dict_keys(['Question_Repeat', 'Problem_Understand', 'Solution_Explore', 'Verify', 'Conclusion'])
                        v_list = v.split(".")
                        if ((v_list[0] in result_list) or ("\n" + v_list[0] in result_list) or (
                                "\n\n" + v_list[0] in result_list)) and pre_key is not None:
                            if (v_list[0] in result_list):
                                start = result_list.index(v_list[0])
                            elif "\n" + v_list[0] in result_list:
                                start = result_list.index("\n" + v_list[0])
                            else:
                                start = result_list.index("\n\n" + v_list[0])
                            if start > 0:
                                v_real = split_dic[pre_key] + ".".join(result_list[: start]) + "."
                                split_dic[pre_key] = v_real
                                result_list = result_list[start:]
                        else:
                            a1 = self.find_str_in_list(v_list[0], result_list)
                            a2 = self.find_str_in_list("\n\n" + v_list[0], result_list)
                            if a2 >= 0 and pre_key is not None:
                                if a2 > 0 or (a2 == 0 and not result_list[0].startswith("\n\n" + v_list[0])):
                                    v_real = split_dic[pre_key] + ".".join(result_list[: a2]) + result_list[
                                        a2].replace("\n\n" + v_list[0], "")
                                    split_dic[pre_key] = v_real
                                    result_list[a2] = "\n\n" + v_list[0]
                                    result_list = result_list[a2:]
                            elif a1 >= 0 and pre_key is not None:
                                if a1 > 0 or (a1 == 0 and not result_list[0].startswith(v_list[0])):
                                    v_real = split_dic[pre_key] + ".".join(result_list[: a1]) + result_list[
                                        a1].replace(v_list[0], "")
                                    split_dic[pre_key] = v_real
                                    result_list[a1] = v_list[0]
                                    result_list = result_list[a1:]
                        if v_list[-1] == "":
                            v_list = v_list[:-1]
                        for i in range(len(v_list)):
                            flag = -i - 1
                            if v_list[flag] in result_list:
                                end = result_list.index(v_list[flag])
                                v_real = ".".join(result_list[: end + 1]) + "."
                                split_dic[k] = v_real
                                result_list = result_list[end + 1:]
                                break
                            elif "\n\n" + v_list[flag] in result_list:
                                end = result_list.index("\n\n" + v_list[flag])
                                v_real = ".".join(result_list[: end + 1]) + "."
                                split_dic[k] = v_real
                                result_list = result_list[end + 1:]
                                break
                            elif " " + v_list[flag] in result_list:
                                end = result_list.index(" " + v_list[flag])
                                v_real = ".".join(result_list[: end + 1]) + "."
                                split_dic[k] = v_real
                                result_list = result_list[end + 1:]
                                break
                            else:
                                # print(flag)
                                pass
                        # print("after refine: ")
                        # print(split_dic)
                        pre_key = k
                    if result_list:
                        if split_dic[pre_key] in result:
                            v_real = split_dic[pre_key] + ".".join(result_list)
                            split_dic[pre_key] = v_real
                        else:
                            split_dic[pre_key] = ".".join(result_list)
                    Solution_Explore = split_dic.get("Solution_Explore")
                    Verify = split_dic.get("Verify")
                    if Solution_Explore:
                        if Verify:
                            Solution_Explore_split_input = "<|im_start|>user\n{Solution_Explore_split_instruction}<|im_end|>\n<|im_start|>assistant\n".format(
                                Solution_Explore_split_instruction=Solution_Explore_split_instruction.replace(
                                    "{solution}",
                                    Solution_Explore))
                            Verify_Explore_split_input = "<|im_start|>user\n{Verification_split_instruction}<|im_end|>\n<|im_start|>assistant\n".format(
                                Verification_split_instruction=Verification_split_instruction.replace("{solution}",
                                                                                                      Solution_Explore).replace(
                                    "{reflection}", Verify))
                            solution = {"id": d['id'], "prompt": Solution_Explore_split_input, "answer": "",
                                        "tag": d["task_l2"]}
                            verify = {"id": d['id'], "prompt": Verify_Explore_split_input, "answer": "",
                                      "tag": d["task_l2"]}
                            Solution_Explore_save.append(solution)
                            Verify_Explore_save.append(verify)
                            split_dic_save.append(split_dic)
                        else:
                            # print(len(Solution_Explore), 0)
                            pass
                    else:
                        # print(0)
                        pass
                elif self.part == "solution_verification_explore":
                    split_dic = self.solution_explore_split(split_result)
                    pre_key1, pre_key = None, None
                    for k1, v1 in split_dic.items():
                        for k, v in v1.items():
                        # dict_keys(['Question_Repeat', 'Problem_Understand', 'Solution_Explore', 'Verify', 'Conclusion'])
                            v_list = v.split(".")
                            if ((v_list[0] in result_list) or ("\n" + v_list[0] in result_list) or (
                                    "\n\n" + v_list[0] in result_list)) and pre_key is not None:
                                if (v_list[0] in result_list):
                                    start = result_list.index(v_list[0])
                                elif "\n" + v_list[0] in result_list:
                                    start = result_list.index("\n" + v_list[0])
                                else:
                                    start = result_list.index("\n\n" + v_list[0])
                                if start > 0:
                                    v_real = split_dic[pre_key1][pre_key] + ".".join(result_list[: start]) + "."
                                    split_dic[pre_key1][pre_key] = v_real
                                    result_list = result_list[start:]
                            else:
                                a1 = self.find_str_in_list(v_list[0], result_list)
                                a2 = self.find_str_in_list("\n\n" + v_list[0], result_list)
                                if a2 >= 0 and pre_key is not None:
                                    if a2 > 0 or (a2 == 0 and not result_list[0].startswith("\n\n" + v_list[0])):
                                        v_real = split_dic[pre_key1][pre_key] + ".".join(result_list[: a2]) + result_list[a2].replace("\n\n" + v_list[0], "")
                                        split_dic[pre_key1][pre_key] = v_real
                                        result_list[a2] = "\n\n" + v_list[0]
                                        result_list = result_list[a2:]
                                elif a1 >= 0 and pre_key is not None:
                                    if a1 > 0 or (a1 == 0 and not result_list[0].startswith(v_list[0])):
                                        v_real = split_dic[pre_key1][pre_key] + ".".join(result_list[: a1]) + result_list[
                                            a1].replace(v_list[0], "")
                                        split_dic[pre_key1][pre_key] = v_real
                                        result_list[a1] = v_list[0]
                                        result_list = result_list[a1:]
                            if v_list[-1] == "":
                                v_list = v_list[:-1]
                            for i in range(len(v_list)):
                                flag = -i - 1
                                if v_list[flag] in result_list:
                                    end = result_list.index(v_list[flag])
                                    v_real = ".".join(result_list[: end + 1]) + "."
                                    split_dic[k1][k] = v_real
                                    result_list = result_list[end + 1:]
                                    break
                                elif "\n\n" + v_list[flag] in result_list:
                                    end = result_list.index("\n\n" + v_list[flag])
                                    v_real = ".".join(result_list[: end + 1]) + "."
                                    split_dic[k1][k] = v_real
                                    result_list = result_list[end + 1:]
                                    break
                                elif " " + v_list[flag] in result_list:
                                    end = result_list.index(" " + v_list[flag])
                                    v_real = ".".join(result_list[: end + 1]) + "."
                                    split_dic[k1][k] = v_real
                                    result_list = result_list[end + 1:]
                                    break
                                else:
                                    # print(flag)
                                    pass
                            # print("after refine: ")
                            # print(split_dic)
                            pre_key1 = k1
                            pre_key = k
                    if result_list:
                        if split_dic[pre_key1][pre_key] in result:
                            v_real = split_dic[pre_key1][pre_key] + ".".join(result_list)
                            split_dic[pre_key1][pre_key] = v_real
                        else:
                            split_dic[pre_key1][pre_key] = ".".join(result_list)
                    Solution_Explore_save.append({"id": d['id'], "split_dic": split_dic, "tag": d["task_l2"]})
                elif self.part == "verify":
                    split_dic = self.part1_split(split_result)
                    pre_key = None
                    for k, v in split_dic.items():
                        # dict_keys(['Question_Repeat', 'Problem_Understand', 'Solution_Explore', 'Verify', 'Conclusion'])
                        v_list = v.split(".")
                        if ((v_list[0] in result_list) or ("\n" + v_list[0] in result_list) or (
                                "\n\n" + v_list[0] in result_list)) and pre_key is not None:
                            if (v_list[0] in result_list):
                                start = result_list.index(v_list[0])
                            elif "\n" + v_list[0] in result_list:
                                start = result_list.index("\n" + v_list[0])
                            else:
                                start = result_list.index("\n\n" + v_list[0])
                            if start > 0:
                                v_real = split_dic[pre_key] + ".".join(result_list[: start]) + "."
                                split_dic[pre_key] = v_real
                                result_list = result_list[start:]
                        else:
                            a1 = self.find_str_in_list(v_list[0], result_list)
                            a2 = self.find_str_in_list("\n\n" + v_list[0], result_list)
                            if a2 >= 0 and pre_key is not None:
                                if a2 > 0 or (a2 == 0 and not result_list[0].startswith("\n\n" + v_list[0])):
                                    v_real = split_dic[pre_key] + ".".join(result_list[: a2]) + result_list[
                                        a2].replace("\n\n" + v_list[0], "")
                                    split_dic[pre_key] = v_real
                                    result_list[a2] = "\n\n" + v_list[0]
                                    result_list = result_list[a2:]
                            elif a1 >= 0 and pre_key is not None:
                                if a1 > 0 or (a1 == 0 and not result_list[0].startswith(v_list[0])):
                                    v_real = split_dic[pre_key] + ".".join(result_list[: a1]) + result_list[
                                        a1].replace(v_list[0], "")
                                    split_dic[pre_key] = v_real
                                    result_list[a1] = v_list[0]
                                    result_list = result_list[a1:]
                        if v_list[-1] == "":
                            v_list = v_list[:-1]
                        for i in range(len(v_list)):
                            flag = -i - 1
                            if v_list[flag] in result_list:
                                end = result_list.index(v_list[flag])
                                v_real = ".".join(result_list[: end + 1]) + "."
                                split_dic[k] = v_real
                                result_list = result_list[end + 1:]
                                break
                            elif "\n\n" + v_list[flag] in result_list:
                                end = result_list.index("\n\n" + v_list[flag])
                                v_real = ".".join(result_list[: end + 1]) + "."
                                split_dic[k] = v_real
                                result_list = result_list[end + 1:]
                                break
                            elif " " + v_list[flag] in result_list:
                                end = result_list.index(" " + v_list[flag])
                                v_real = ".".join(result_list[: end + 1]) + "."
                                split_dic[k] = v_real
                                result_list = result_list[end + 1:]
                                break
                            else:
                                print(flag)
                        # print("after refine: ")
                        # print(split_dic)
                        pre_key = k
                    if result_list:
                        if split_dic[pre_key] in result:
                            v_real = split_dic[pre_key] + ".".join(result_list)
                            split_dic[pre_key] = v_real
                        else:
                            split_dic[pre_key] = ".".join(result_list)
                    Verify_Explore_save.append({"id": d['id'], "split_dic": split_dic, "tag": d["task_l2"]})

                # print(split_dic)
                # start, end = 0, 0
            except:
                print(f"error occured in processing {d['id']}")
        if self.part == "basic_structure":
            return Solution_Explore_save, Verify_Explore_save, split_dic_save
        elif self.part == "solution_verification_explore":
            output = {}
            for d in Solution_Explore_save:
                output[d["id"]] = d["split_dic"]
            return output
        elif self.part == "verify":
            output = {}
            for d in Verify_Explore_save:
                output[d["id"]] = d["split_dic"]
            return output

    def run(self):
        if self.part == "basic_structure":
            data = []
            with open("20250209_deepseek_r1_math_26K.jsonl") as f:
                for line in f.readlines():
                    data.append(json.loads(line))

            Solution_Explore_save, Verify_Explore_save, split_dic_save = self.split_refine(data)
            fw_Solution_Explore = open("R1_solution_explore.jsonl", "w", encoding="utf-8")
            fw_Verify_Explore = open("R1_verify_explore.jsonl", "w", encoding="utf-8")
            fw_split_part1 = open("R1_split_part1.jsonl", "w", encoding="utf-8")
            j, cnt = 0, 0
            for d in tqdm(data):
                if Solution_Explore_save[j]["id"] == d["id"]:
                    change = "".join(split_dic_save[j].values())
                    origin = d["result"]
                    diff = difflib.SequenceMatcher(None, change, origin).quick_ratio()
                    jaccard_diff = self.jaccard_similarity(change, origin)
                    # print("diff: ", diff, "jaccard_diff: ", jaccard_diff)
                    if diff >= 0.90 or jaccard_diff >= 0.95:
                        cnt += 1
                        d["split_result_part1_formate"] = split_dic_save[j]
                        d["flag"] = True
                        fw_Solution_Explore.write(json.dumps(Solution_Explore_save[j], ensure_ascii=False) + "\n")
                        fw_Verify_Explore.write(json.dumps(Verify_Explore_save[j], ensure_ascii=False) + "\n")
                        fw_split_part1.write(json.dumps(d, ensure_ascii=False) + "\n")
                    else:
                        d["flag"] = False
                    j += 1
                else:
                    d["flag"] = False
            print(f"{cnt} data samples are kept and saved from {len(data)} data samples in total")
            fw_Solution_Explore.close()
            fw_Verify_Explore.close()
            fw_split_part1.close()
        elif self.part == "solution_verification_explore":
            orgin_data = {}
            with open("R1_split_part1.jsonl", "r") as f:
                for d in f.readlines():
                    d = json.loads(d)
                    orgin_data[d["id"]] = d
            data = []
            with open("R1_solution_explore.jsonl", "r") as f:
                for d in f.readlines():
                    js = json.loads(d)
                    js['task_l1'] = "math"
                    js['task_2'] = js['tag']
                    js['split_result'] = js['result']
                    js['result'] = js['prompt'].apply(
                        lambda x: str(x).split("# Mathematical Solution:\n")[1]
                                    .split("\n\nRemember double check original mathematical solution hasn't been rewritten.")[0]
                        if "# Mathematical Solution:\n" in str(x) else ""
                    )
                    data.append(js)
            # data = o.execute_select(sql)
            Solution_Explore_split = self.split_refine(data)
            keys = Solution_Explore_split.keys()
            print(f"{len(keys)} data samples passed Solution_Explore_split")
            cnt = 0
            for k in tqdm(orgin_data.keys()):
                d = orgin_data[k]
                d["split_result_part2_formate"] = d["split_result_part1_formate"].copy()
                if str(k) in keys:
                    # print("id: ", d["id"],"Reformate match: ", "".join(["".join(Solution_Explore_split[str(k)][kk].values()) for kk in Solution_Explore_split[str(k)].keys()]) == d["split_result_part2_formate"]['Solution_Explore'])
                    origin = d["split_result_part2_formate"]['Solution_Explore']
                    change = "".join(["".join(Solution_Explore_split[str(k)][kk].values()) for kk in Solution_Explore_split[str(k)].keys()])
                    diff = difflib.SequenceMatcher(None, change, origin).quick_ratio()
                    jaccard_diff = self.jaccard_similarity(change, origin)
                    # print("diff: ", diff, "jaccard_diff: ", jaccard_diff)
                    if diff >= 0.90 or jaccard_diff >=0.95:
                        cnt += 1
                        orgin_data[k]["flag"] = True
                        orgin_data[k]["split_result_part2_formate"]["Solution_Explore"] = Solution_Explore_split[str(k)]
                    else:
                        orgin_data[k]["flag"] = False
                else:
                    orgin_data[k]["flag"] = False
            print(f"{cnt} records remain after validation against the original solution")
            data = []
            with open("R1_verify_explore.jsonl", "r") as f:
                for d in f.readlines():
                    js = json.loads(d)
                    js['task_l1'] = "math"
                    js['task_2'] = js['tag']
                    js['split_result'] = js['result']
                    js['result'] = js['prompt'].apply(
                        lambda x: str(x).split("### 2. Please split the following mathematical reflection text:\n")[1]
                                    .split("\n\n##Output: ")[0]
                        if "### 2. Please split the following mathematical reflection text:\n" in str(x) 
                        else ""
                    )
                    data.append(js)
            self.part = "verify"
            Verification_split = self.split_refine(data)
            keys = Verification_split.keys()
            print(f"{len(keys)} data samples passed Verification_split")
            cnt = 0
            for k in tqdm(orgin_data.keys()):
                d = orgin_data[k]
                d["split_result_part3_formate"] = d["split_result_part2_formate"].copy()
                if str(k) in keys:
                    # print("id: ", d["id"],"Reformate match: ", "".join(Verification_split[str(k)].values()) == d["split_result_part3_formate"]['Verify'])
                    origin = d["split_result_part1_formate"]['Verify']
                    change = "".join(Verification_split[str(k)].values())
                    diff = difflib.SequenceMatcher(None, change, origin).quick_ratio()
                    jaccard_diff = self.jaccard_similarity(change, origin)
                    # print("diff: ", diff, "jaccard_diff: ", jaccard_diff)
                    d["split_result_part3_formate"]["Verify"] = Verification_split[str(k)]
                    if diff >= 0.90 or jaccard_diff >=0.95:
                        cnt += 1
                        orgin_data[k]["flag"] = True and orgin_data[k]["flag"]
                        # d["split_result_part3_formate"]["Verify"] = Verification_split[str(k)]
                    else:
                        orgin_data[k]["flag"] = False
                else:
                    orgin_data[k]["flag"] = False
            print(f"{cnt} records remain after validation against the original solution")
            with open("R1_split_part2_filtered.jsonl", "w", encoding="utf-8") as fw_split_part2:
                i = 0
                for k, v in orgin_data.items():
                    if v["flag"]:
                        fw_split_part2.write(json.dumps(v, ensure_ascii=False) + "\n")
                        i += 1
                print("final number of data samples: ", i)


import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--part',
        type=str,
        choices=['basic_structure', 'solution_verification_explore'],
        required=True,
        help="steps include 'basic_structure' and 'solution_verification_explore'"
    )
    
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    partition = "20250209_deepseek_r1_math_26K" 
    if args.part == 'basic_structure':
    #  Split the result, reformat it, and upload the solution and verification sections for the content to be split.
        part = "basic_structure"
        stat = "r1"
        op = AnswerSplitOperator(partition, part, stat)
        op.run()
    elif args.part == 'solution_verification_explore':
    # further split the solution and verification part
        part = "solution_verification_explore"
        stat = "r1"
        op = AnswerSplitOperator(partition, part, stat)
        op.run()

