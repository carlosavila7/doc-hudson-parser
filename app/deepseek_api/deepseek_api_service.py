import os
from openai import OpenAI


class DeepSeekApiService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'), 
            base_url="https://api.deepseek.com"
        )

    def populate_first_step(self, file_content):
        system_prompt = """"
        # Objective

        You are tasked with analyzing the provided text content of a PDF document, which details information about public sector recruitment. The document is in brazilian portuguese. Your goal is to **extract and structure** the data into JSON objects (arrays), corresponding to the following database entities:
        - `exam_topics` 
        - `exams`
        - `recruitment_offers`

        # Database entities

        ## `exam_topics`

        Represents the topics contained in an exam. A student that wants to prepare for it, would look the topics to study them. Extract only the main subject headings or macro areas. Do not include detailed subtopics, specific articles of law, or paragraphs.

        An exam_topic has the following properties:

        - name: The name of the exam topic

        ```json
        name: string,
        ```

        ## `exams`

        Represents every written test (or exam) that must be taken during this process. Any test other than written must not be mapped - as physical or psicological evaluations. Is exepected that a recruiment offer has at least one exam, however it might have many exams that evaluate different candidates for different job roles.

        An exam has the following properties:

        - name: Based on the context, give it a name so it can be identified.
        - education_level: BASIC for when the requirement is only `Ensino Fundamental`, MEaDIUM for when the requirement is the `Ensino Médio`and SUPERIOR when some graduation IS required.
        - exam_topics: an array of the entity [`exam_topics`](#exam_topics)

        JSON specification:

        ```json
        name: string
        education_level: "BASIC" | "MEDIUM" | "SUPERIOR",
        exam_topics: exam_topics[],
        ```

        ## `recruitment_offers`

        Represents the public sector recruitment process itself. It has the following properties:

        - name: Name of the process
        - examining_board: The name of the instituition responsable for conducting the exams
        - year: The year when the process was published
        - scope: Process scope in the public administration (LOCAL, STATE, FEDERAL)
        - city: The city related to the process (only if the `scope` is LOCAL, else `undefined`)
        - state: The state of Brazil related to the process (only if the `scope` is LOCAL or STATE, else `undefined`)

        JSON specification: 

        ```json
        name: string, 
        examining_board: string, 
        year: string,
        scope: "LOCAL" | "STATE" | "FEDERAL"
        city?: string,
        state?: string,

        exams: exams[],
        ```

        # Output 

        The JSON output must be a single object with the previous entities starting from the `recruitment_offers` and their relations.

        ```json
        {
            name: string, 
            examining_board: string, 
            year: string,
            scope: "LOCAL" | "STATE" | "FEDERAL"
            city?: string,
            state?: string,
            exams: [
                {
                    name: string,
                    education_level: "BASIC" | "MEDIUM" | "SUPERIOR",
                    exam_topics: [
                        {
                            name: string,
                        },
                    ],
                },
            ],
        }
        ```

        """

        user_prompt = f""""
        # File Content

        ```txt
        {file_content}
        ```
        """
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                'type': 'json_object'
            }
        )
        
        return response.choices[0].message.content
    
    def populate_second_step(self, file_content, identified_exams, exam_index):
        system_prompt = """
        # Objective

        You are tasked with analyzing the provided text content of a PDF document, which details information about public sector recruitment. The document is in Brazilian Portuguese. Your goal is to **extract the detailed subtopic names** for the exam provided in the context, and structure them under their corresponding parent topics.

        **CRITICAL CONSTRAINT:** The ONLY output must be the raw JSON array, starting with `[` and ending with `]`. DO NOT include any markdown formatting (e.g., ```json), commentary, or explanation. All extracted text values must be in the original Brazilian Portuguese.

        # Database entity

        ## `exam_topics`

        Represents the topics contained in an exam. A student that wants to prepare for it, would look the topics to study them. Extract only the main subject headings or macro areas. Do not include detailed subtopics, specific articles of law, or paragraphs.

        `subtopics` must be an array of string property inside each topic. Represents the sub topics contained in an exam topic.

        - name: The name of the exam topic
        - subtopics: An array of strings where each is a subtopic inside that topic

        ```json
        name: string,
        subtopics: string[]
        ```

        # Output 

        The JSON output must be a single object with the previous entities starting from the `recruitment_offers` and their relations.

        ```json
        [
            {
                name: string,
                subtopics: string[]
            },
        ],

        ```

        """

        user_prompt = f"""
        # Identified exams

        Here are the exams that have been identified from that same pdf file content. The topics from each exam have also been identified.  

        ```json
        {identified_exams}
        ```

        # Instructions

        Extract the subtopics for the exam at the index {exam_index} from the identified exams array. The output json object should reflect only this exam.

        # File Content

        ```txt
        {file_content}
        ```
        """

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                'type': 'json_object'
            }
        )
        
        return response.choices[0].message.content