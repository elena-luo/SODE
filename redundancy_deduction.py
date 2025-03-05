import json
from prompts import answer_simplification_instruction


class simplize_answer:
    def __init__(self, output_file, input_file, status, is_upload_odps=False):

        # Delete all duplicates, keeping only the distinct ones
        # Delete all duplicates, keeping only the distinct ones, and remove content with calculation errors or no conclusions
        # Keep only the first solution that provides a calculation conclusion
        # ["delete_multi", "delete_multi_incorrect_incomplete", "keep_first"]
        self.status = status
        self.input_file = input_file
        self.output_file = output_file
        self.is_upload_odps = is_upload_odps

    def run(self):
        data = []
        with open(self.input_file, "r") as f:
            for line in f.readlines():
                line = json.loads(line)
                data.append(line)
        fw = open(self.output_file+f"_{status}_need_simplize.json", "w", encoding="utf-8")
        for d in data:
            problem = d["prompt"]
            result = d["result"]
            Drop_Multipilation = d["Drop_Multipilation"]
            incorrect_solution = "\n".join(d["incorrect_solution"])
            incomplete_solution = "\n".join(d["incomplete_solution"])
            """- **Mathematical Problem:** [Mathematical problem here]  
- **Answer:** [Original answer here]  
- **Part to Remove:** [Removed Part]  """
            if status == "delete_multi_all":
                if Drop_Multipilation:
                    prompt = answer_simplification_instruction.replace("[Mathematical problem here]", problem).replace("[Original answer here]", result).replace("[Removed Part]", "\n".join(Drop_Multipilation))
                else:
                    continue
            elif status != "delete_multi" and status != "delete_multi_incorrect_incomplete" and "delete_multi" in status:
                if Drop_Multipilation[max(0, len(Drop_Multipilation)-int(status.replace("delete_multi_", ""))):]:
                    prompt = answer_simplification_instruction.replace("[Mathematical problem here]", problem).replace("[Original answer here]", result).replace("[Removed Part]", "\n".join(Drop_Multipilation[max(0, len(Drop_Multipilation)-int(status.replace("delete_multi_", ""))):]) )
                else:
                    continue
            elif status == "keep_first":
                prompt = answer_simplification_instruction.replace("[Mathematical problem here]", problem).replace("[Original answer here]", result).replace("[Removed Part]", Drop_Multipilation)
            prompt = f"<|im_start|>user\n{prompt}\n<|im_end|>\n<|im_start|>assistant\n"
            line = {"id": d["id"], "prompt": prompt, "answer": "", "tag": d["task_l2"]}
            fw.write(json.dumps(line, ensure_ascii=False) +"\n")
        fw.close()


if __name__ == "__main__":
    
    file_name = "R1_split_part2_filtered"
    input = "R1_split_part2_filtered_need_filter.json"
    status = "delete_multi_all"
    status = "delete_multi_1"
    status = "delete_multi_2"
    is_upload_odps = False
    op = simplize_answer(file_name, input, status, is_upload_odps)
    op.run()
    

