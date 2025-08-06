# Prompt Principles

1. **Be Concise:** No need for polite phrases; get straight to the point.
   - *Example:* ~~Could you kindly describe the structure of a human cell, please?~~ Describe the structure of a human cell.

2. **Specify Audience:** Integrate the intended audience in the prompt.
   - *Example:* Construct an overview of how smartphones work, intended for seniors who have never used one before.

3. **Break Down Tasks:** Break complex tasks into simpler, sequential prompts in an interactive conversation.
   - *Example:* P1: Distribute the negative sign to each term inside the parentheses of the following equation: 2x + 3y - (4x - 5y) P2: Combine like terms for 'x' and 'y' separately. P3: Provide the simplified expression after combining the terms.

4. **Use Affirmative Directives:** Employ affirmative directives such as "do," while steering clear of negative language like "don't".
   - *Example:* How do buildings remain stable during earthquakes?

5. **Request Clarity at the Right Level:** Use prompts like:
   - Explain [topic] in simple terms.
   - Explain to me like I'm 11 years old.
   - Explain to me as if I'm a beginner in [field].
   - Explain to me as if I'm an expert in [field].
   - Write the [essay/text/paragraph] using simple English like you're explaining something to a 5-year-old.
   - *Example:* Explain to me like I'm 11 years old: how does encryption work?

6. **Use Incentives for Better Solutions:** Add "I'm going to tip $xxx for a better solution".
   - *Example:* I'm going to tip $300K for a better solution! Explain the concept of dynamic programming and provide an example use case.

7. **Example-Driven Prompting:** Use few-shot prompting.
   - *Example:* Example 1: Translate the following English sentence to French: "The sky is blue." (Response: "Le ciel est bleu.") Example 2: Translate the following English sentence to Spanish: "I love books." (Response: "Amo los libros.")

8. **Use Delimiters and Structure:** Start with '###Instruction###', followed by '###Example###' or '###Question###' if relevant. Separate instructions, examples, questions, context, and input data with line breaks.
   - *Example:* ###Instruction### Translate a given word from English to French. ###Question### What is the French word for "book"?

9. **Use Explicit Directives:** Incorporate phrases like "Your task is" and "You MUST".
   - *Example:* Your task is to explain the water cycle to your friend. You MUST use simple language.

10. **State Penalties for Non-Compliance:** Incorporate phrases like "You will be penalized".
    - *Example:* Your task is to explain the water cycle to your friend. You will be penalized if you fail to use simple language.

11. **Request Human-Like Answers:** Use the phrase "Answer a question given in a natural, human-like manner".
    - *Example:* Write a paragraph about healthy food. Answer a question given in a natural, human-like manner.

12. **Encourage Step-by-Step Reasoning:** Use leading words like "think step by step".
    - *Example:* Write a Python code to loop through 10 numbers and sum all of them. let's think step by step.

13. **Request Unbiased Answers:** Add "Ensure that your answer is unbiased and avoids relying on stereotypes."
    - *Example:* How do cultural backgrounds influence the perception of mental health? Ensure that your answer is unbiased and avoids relying on stereotypes.

14. **Elicit Details by Asking Questions:** Allow the model to ask you questions until it has enough information.
    - *Example:* From now on, ask me questions until you have enough information to create a personalized fitness routine.

15. **Teach and Test Understanding:** Use prompts like "Teach me the [topic] and include a test at the end, but don't give me the answers and then tell me if I got the answer right when I respond".
    - *Example:* Teach me about the KVL law and include a test at the end, and let me know if my answers are correct after I respond, without providing the answers beforehand.

16. **Assign a Role to the Model:** Assign a role to the LLM.
    - *Example:* If you were an expert economist, how would you answer this: What are the key differences between a capitalist and a socialist economic system?

17. **Use Delimiters for Clarity:** Use delimiters to separate sections or content.
    - *Example:* Compose a persuasive essay discussing the importance of 'renewable energy sources' in reducing greenhouse gas emissions.

18. **Repeat Key Words or Phrases:** Repeat a specific word or phrase multiple times within a prompt.
    - *Example:* Evolution, as a concept, has shaped the development of species. What are the main drivers of evolution, and how has evolution affected modern humans?

19. **Combine Chain-of-Thought with Few-Shot:** Use both chain-of-thought and few-shot examples.
    - *Example:* Example 1: "Divide 10 by 2. First, take 10 and divide it by 2. The result is 5." Example 2: "Divide 20 by 4. First, take 20 and divide it by 4. The result is 5." Main Question: "Divide 30 by 6. First, take 30 and divide it by 6. The result is...?"

20. **Use Output Primers:** Conclude your prompt with the beginning of the desired output.
    - *Example:* Describe the principle behind Newton's First Law of Motion. Explanation:

21. **Request Detailed Content:** Use phrases like "Write a detailed [essay/text/paragraph/article] for me on [topic] in detail by adding all the information necessary".
    - *Example:* Write a detailed paragraph for me on the evolution of smartphones in detail by adding all the information necessary.

22. **Request Style-Preserving Corrections:** To correct or change text without changing its style, use prompts like "Try to revise every paragraph sent by users. You should only improve the user’s grammar and vocabulary and make sure it sounds natural. You should maintain the original writing style, ensuring that a formal paragraph remains formal".
    - *Example:* Try to revise every text sent by users. You should only improve the user's grammar and vocabulary and make sure it sounds natural. You should maintain the original writing style, ensuring that a formal paragraph remains formal. Paragraph: Renewable energy is really important for our planet's future. It comes from natural ...

23. **Automate Multi-File Code Generation:** For code spanning multiple files, instruct the model to generate a script that creates or modifies the necessary files.
    - *Example:* Generate code that spans more than one file, and generate a Python script that can be run to automatically create the specified files for a Django project with two basic apps for different functionalities.

24. **Continue Text with Specific Starters:** To initiate or continue text using specific words, phrases, or sentences, use prompts like "I'm providing you with the beginning [song lyrics/story/paragraph/essay...]: [Insert text]. Finish it based on the words provided. Keep the flow consistent."
    - *Example:* I'm providing you with the beginning of a fantasy tale: "The misty mountains held secrets no man knew." Finish it based on the words provided. Keep the flow consistent.

25. **State Explicit Requirements:** Clearly state the requirements that the model must follow in order to produce content, in the form of keywords, regulations, hints, or instructions.
    - *Example:* Create a packing list for a beach vacation, including the following keywords "sunscreen," "swimsuit," and "beach towel" as essential items.

26. **Mimic Provided Language Style:** To write text similar to a provided sample, include instructions like "Use the same language based on the provided paragraph/title/text/essay/answer".
    - *Example:* "The gentle waves whispered tales of old to the silvery sands, each story a fleeting memory of epochs gone by." Use the same language based on the provided text to portray a mountain's interaction with the wind.
