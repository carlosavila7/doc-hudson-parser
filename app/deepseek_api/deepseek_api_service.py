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

        Represents the topics contained in an exam. A student that wants to prepare for it, would look the topics to study them. It represents the macro area of knowledge, subtopics will be handled in other entity.

        An exam_topic has the following properties:

        - name: The name of the exam topic

        ```json
        name: string,
        ```

        ## `exams`

        Represents every written test (or exam) that must be taken during this process. Is exepected that a recruiment offer has at least one exam, however it might have many exams that evaluate different candidates for different job roles.

        An exam has the following properties:

        - name: Based on the context, give it a name so it can be identified.
        - education_level: BASIC for when the requirement is only `Ensino Fundamental`, MEDIUM for when the requirement is the `Ensino Médio`and SUPERIOR when some graduation IS required.
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