pattern_split_instruction_1 = """You are a mathematical solution structure decomposition agent. Your task is to analyze a mathematical problem's solution, then restructure it into a specific format following these rules:\n\n1. Split the solution into exactly 5 sequential components:\n   - Question_Repeat: The initial statement of the problem, including the "let's break this down step by step" part\n   - Problem_Understand: Only the initial high-level analysis before diving into calculations (if present, otherwise skip)\n   - Solution_Explore: The main solution process, including all calculations and intermediate steps up to finding the first answer\n   - Verify: Include ALL verification steps, alternative approaches, and checking calculations after the initial solution (if present, otherwise skip)\n   - Conclusion: Include both the final concluding statement AND the boxed answer\n\n2. Natural Transition Points:\n   - Question_Repeat → Problem_Understand: Break after the problem is stated and before analysis begins\n   - Problem_Understand → Solution_Explore: Break after conceptual analysis and before first calculations\n   - Solution_Explore → Verify: Break after obtaining first answer and before starting verification\n   - Verify → Conclusion: Break after all checking is complete and before final statement\n\n3. Format Requirements:\n   - Present the output in two main sections: "# Answer Split" and "# Structure"\n   - Under "Answer Split", use "##" headings for each component (Question_Repeat, Problem_Understand, etc.)\n   - Include the exact original text under each heading, preserving all line breaks and formatting\n   - After all components, add the "# Structure" section with the array of component names\n   - Ensure no text is truncated or modified from the original\n\n3. Content Distribution Guidelines:\n   - Question_Repeat must include both the problem statement AND any initial "let's break this down" statement\n   - Problem_Understand should be limited to only the initial analysis before any calculations\n   - Solution_Explore should contain all mathematical steps, intermediate checking and calculations\n   - Place ALL verification steps, alternative solutions, and checking calculations in the Verify section\n   - Conclusion should contain only the final answer with proper \\boxed{} notation\n\n4. Critical Requirements:\n   - Preserve all original mathematical notation exactly, especially \\boxed{} notation\n   - Maintain all line breaks as they appear in the original text\n   - Include all text exactly as written without any modifications\n   - Ensure each section break occurs at natural transition points in the solution\n   - Ensure all verification steps are in the Verify section\n\n5. Quality Control:\n   - Double-check that no text is missing between sections\n   - Do not add any additional structure beyond the 5 main components\n   - Do not modify or rewrite any of the original text\n   - Preserve all LaTeX notation exactly as given\n   - Follow the exact formatting of the expected output example\n\n# Input\n## 1. The mathematics question's solution\n{solution}\n\n## Output"""

Solution_Explore_split_instruction = """As an AI assistant, your task is to restructure mathematical solution text into a hierarchical format. Follow these steps:

1. Parse the input text and organize it into the following structure:
   - Top level: "Solution Explore Split" (main heading)
   - Second level: Solutions (## Solution1, ## Solution2, etc.)
   - Third level: Analysis components

2. Format Rules:
   - Use # for main heading
   - Use ## for Solution level
   - Use ### for component headers
   - DO NOT use original text content as component headers
   - Preserve all mathematical notations and equations
   - Maintain original text content within appropriate sections

3. After the main content, add a "structure" section that summarizes the hierarchy using:
   # structure
   Solution[n]: [list of components]

4. Solution Separation Rules:
    - Start a new Solution section when a different approach to the same problem is attempted
    - The strategy fundamentally changes
    - Keywords: "alternatively", "Maybe there's a better way."

5. Content Preservation:
    - Keep all mathematical notations (\( \) and LaTeX)
    - Use exact text as it appears
    - Maintain all numerical values and equations
    - Keep logical flow intact
    - Include all text exactly as written without any modifications

Please format the following mathematical solution accordingly :
# Mathematical Solution:
{solution}

Remember double check original mathematical solution hasn't been rewritten."""

Verification_split_instruction = """Given a mathematical solution and its reflection text, identify and categorize the verification steps into specific categories. The output should contain two parts:

1. A formatted section titled "# Verify Split" containing:
   - Each verification step as a second-level heading (##)
   - The relevant text under each category keeping the mathematical notation intact
   - Separate the content of the self-talk affirmation and negation programs into the self-affirmation/self-negation
   - "self-affirmation" example: I think this is solid/ Yes, that checks out
   - "self-negation" example: We already did that / but that might be too complicated

2. A section titled "# structure" containing:
   - A simple list of the verification categories in the exact order they appear in the text
   - Format: ["category1", "category2", ...]

Key Guidelines:
- Include complete verification sequences even when they span multiple paragraphs
- Keep all mathematical notation and calculations exactly as they appear
- Maintain the logical flow of verification steps
- Focus on numerical verification and constraint checking
- Include all text exactly as written without any modifications
- Include complete verification sequences even when they span multiple paragraphs

Format the output exactly as shown:
# Verify Split

## [Category_Name]
[Complete verification text with all calculations]

## [Next_Category_Name]
[Complete verification text with all calculations]

# structure
["category1", "category2", ...]

Important: Only INCLUDE the mathematical REFLECTION TEXT, NOT the SOLUTION TEXT itself.

## Input
### 1. Solution Text:
{solution}

### 2. Please split the following mathematical reflection text:
{reflection}

##Output: """


complete_answer = """**Instruction:**  
Given a **mathematical problem**, the **correct answer**, and a **response divided into two consecutive parts**, your task is to evaluate the following:  

1. **Does the first part of the response provide an answer to the mathematical problem?**  
	- For multiple-choice questions, it is important to note whether the conclusion of the solution matches the content of the options. If they match, it can also be considered as providing an answer.
    - For proof-based questions, it is important to note whether the problem explicitly provides the text of the conclusion to be proven.
2. **If the first part provides an answer, does it match the correct answer?**  
3. **If the first part does not provide an answer, does it seamlessly connect with the subset of second part to form a complete and correct answer while maintaining linguistic fluency and logical coherence?** 
4. **If the answer of third question is Yes, Give the SMALLEST consecutive subset of second part keys that can seamlessly connect with the first part to completely answer the quesiton.** 

**Input Format:**  
- **Mathematical Problem:** [Insert the mathematical problem here]  
- **Correct Answer:** [Insert the correct answer here]  
- **Response Part 1:** [Insert the first part of the response here]  
- **Response Part 2:** [Insert the second part of the response here]  

**Output Format:**  
1. **Answer to Question 1:** [Yes/No]  
2. **Answer to Question 2:** [Yes/No] (if applicable)  
3. **Answer to Question 3:** [Yes/No] (if applicable)  
4. **Answer to Question 4:** [a list of part2's keys]
4. **Explanation:** [Provide a brief explanation supporting your answers]  

**Example:**  
**Example1: **
- **Mathematical Problem:** Solve for \( x \) in the equation \( 2x + 3 = 7 \).  
- **Correct Answer:** \( x = 2 \)  
- **Response Part 1:** "First, subtract 3 from both sides of the equation."  
- **Response Part 2:** {"Sub Calculate": "Which gives \( 2x = 4 \).", "Calculation": "Then, divide both sides by 2 to find \( x = 2 \).", "Check": "Wait let me check.", "Put answer back": "Put the \( x = 2 \) back to the function", "Calculate \( x = 2 \)": "\( 2x + 3 = 2 * 2 + 3 = 7 \) This satisfy the question."}

**Output:**  
1. **Answer to Question 1:** No  
2. **Answer to Question 2:** N/A  
3. **Answer to Question 3:** Yes  
4. **Answer to Question 4:** ["Sub Calculate", "Calculation"]
5. **Explanation:** The first part of the response correctly identifies the first step in solving the equation but stops short of providing the final answer. The "Calculation" key in the second part logically follows the first part by completing the necessary division to solve for \( x \), thus forming a complete and correct answer when combined with the first part. The other keys in the second part are either redundant or unnecessary for providing the final answer.

**Example2: **
- **Mathematical Problem:** Prove that for any real numbers \( a \) and \( b \), if \( a > 0 \) and \( b > 0 \), then \( ab > 0 \).
- **Correct Answer:** The product of two positive real numbers is always positive.
- **Response Part 1:** "To prove that \( ab > 0 \) when \( a > 0 \) and \( b > 0 \), we start by noting that both \( a \) and \( b \) are positive, which is a necessary condition for the product to be positive."
- **Response Part 2:** {"Verification": "Given \( a > 0 \) and \( b > 0 \), the product \( ab \) is positive because the product of two positive numbers is always positive, thus verifying the statement \( ab > 0 \)."}

**Output:**
1. **Answer to Question 1:** Yes
2. **Answer to Question 2:** Yes
3. **Answer to Question 3:** No
4. **Answer to Question 4:** []  
5. **Explanation:** The first part of the response correctly sets up the proof by stating the conditions under which the proof will proceed. The second part, now labeled as "Verification," confirms that these conditions indeed lead to the conclusion that \( ab > 0 \). Since the first part already provides a clear and correct setup, no subset of the verification part is necessary to form a complete and correct answer, making the answer to the third question "No" and the fourth question an empty list."""


clustering_instruction="""Criteria for clustering the mathematical solutions:
1. If the solutions used to arrive at the solutions are fundamentally different from each other, such
as algebraic manipulation versus geometric reasoning, they can be considered novel;
2. Even if the results are the same, if the intermediate steps or processes involved in reaching
those solutions vary significantly, the solutions can be considered different;
3. If the solutions relies on different assumptions or conditions, they should be considered
different from each other;
4. A solution might generalize to a broader class of problems, while another solution might be
specific to certain conditions. In such cases, they are considered distinct;
5. If one solution is significantly simpler or more complex than the others, it can be regarded as
essentially novel, even if they lead to the same result.
Given the following mathematical problem:
***problem***
Solutions:
Solution 1: ...
Solution 2: ...
Please output the clusters strictly following the following format, each row containing a cluster,
names, and reasons. Do not include any additional text or explanations outside of this format:
cluster1 [solution names] reason for cluster
cluster2 [solution names] reason for cluster
cluster3 [solution names] reason for cluster
...
For example:
cluster1 [Solution 1, Solution 3, Solution 5] similar algebraic approach using the volume formula
and canceling terms or directly solving for the height.
cluster2 [Solution 2, Solution 4] verifying the correctness and consistency of the formula and
solution and considering unit checks or logical reasoning on how volume relates to base area and
height.

#Input
1. Math Queestion to Answer
[question text here]

2. Solution:
[solution text here]"""

answer_simplification_instruction = """**Instruction:**  
Given a **mathematical problem**, its **answer**, and a **specific part of the answer that needs to be removed**, your task is to:  
1. Remove the specified part from the answer **without altering the rest of the text**.  
2. Ensure the modified answer remains **linguistically fluent** and **logically coherent**.  
3. Make minimal changes to the original text and make sure to preserve its meaning and structure. 
4. Output text directly without any extra explanation.

**Input Format:**  
- **Mathematical Problem:** [Insert the mathematical problem here]  
- **Answer:** [Insert the original answer here]  
- **Part to Remove:** [Specify the exact part of the answer to be removed]  

**Output Format:**  
- **Modified Answer:** [Provide the modified answer after removing the specified part]  

**Example:**  
**Input:**  
- **Mathematical Problem:** Solve for \( x \) in the equation \( 2x + 3 = 7 \).  
- **Answer:** To solve for \( x \), first subtract 3 from both sides of the equation, which gives \( 2x = 4 \). Then, divide both sides by 2 to find \( x = 2 \).  
- **Part to Remove:** "which gives \( 2x = 4 \)"  
**Output:**  
- **Modified Answer:** To solve for \( x \), first subtract 3 from both sides of the equation. Then, divide both sides by 2 to find \( x = 2 \). 

**Input:**  
- **Mathematical Problem:** [Mathematical problem here]  
- **Answer:** [Original answer here]  
- **Part to Remove:** [Removed Part]

**Output:**  
- **Modified Answer:** """

SOLUTION_CLASSIFICATION_PROMPT = '''
You are a professional mathematics teacher tasked with evaluating student solutions to mathematical problems. I will provide you with:

1. A mathematical problem
2. The standard solution for this problem
3. Multiple solutions that need evaluation

For each solution, you need to carefully analyze and provide two labels:

# Label 1: Evaluate Completeness and Correctness
Analyze whether each solution fully derives the final answer to the question and whether the final answer matches the final answer marked with \boxed in the standard solution. 
Note that in label 1, we only care about whether the final answer in solution matches the final answer marked with \boxed in the standard solution. There could be errors in the solution, but as long as the final answer matches, it is considered correct.
- If the solution fully derives the final answer to the question, and matches the final answer marked with \boxed in the standard solution, output: <label1>Correct</label1>
- If the solution fully derives a final answer to the question, but differs from the final answer marked with \boxed in the standard solution, output: <label1>Incorrect</label1>
- If the solution is not complete and does not fully derive the final answer to the question, output: <label1>Incomplete</label1>
- Note that the format of the final answer in the solution may have slightly different representations compared to the final answer in the standard solution. For numerical or formula solutions, if they are mathematically equivalent, they are considered correct. For example, 109.2 and \frac{{546}}{{5}} are equivalent and thus correct.

# Label 2: Evaluate Calculation and Derivation Errors
Even though the solution may be correct, incorrect, or incomplete as defined above, there might still be Calculation and Derivation Errors in its derivation process。
- If there are calculation and derivation errors, output: <label2>Calculation and Derivation Error</label2>, 
- Then in the next line, talk about the explanation for the Calculation and Derivation Error.
- Then in the next line, quote the erroneous parts from the solution completely and exactly without omitting any words. An erroneous part could be a step or several steps. You should fully include where the error starts and ends.
- Note that the part you quote must exactly match a portion of the solution. Do not add any extra characters, including newline characters, spaces, etc.
- if the the solution does not contain any calculation and derivation errors, output: <label2>No Calculation and Derivation Error</label2>

# Output Format
For each solution, provide output in the following format:

## Solution X (where X is the solution number)
[Label 1]
Explanation for label1: [Detailed explanation of the reason for Label 1]
[Label 2]
Explanation for label2: [Detailed explanation of the reason for Label 2]
Quoted erroneous parts: [Quoted erroneous parts from the solution]

# Evaluation Principles
1. Examine each step of every solution carefully
2. Provide specific and clear explanations, avoiding vague statements
3. Note when evaluating solutions, treat each solution as a complete independent answer. Do not make connections between multiple solutions.
4. You must strictly follow the format of the output

Remember to maintain consistency in your evaluation across all solutions while being thorough in your analysis of each specific case.

Question:
{}

Standard solution:
{}

Solutions to be evaluated:
{}
'''

