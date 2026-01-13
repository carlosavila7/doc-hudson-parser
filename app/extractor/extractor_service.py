import json

from app.supabase.supabase_service import SupabaseService
from app.deepseek_api.deepseek_api_service import DeepSeekApiService


class ExtractorService:
    def __init__(self):
        self.supabase_service = SupabaseService()
        self.deepseek_service = DeepSeekApiService()

    def populate_base_entities(self, file_bucket, file_path):
        file = self.supabase_service.download_file_from_s3(
            file_bucket, file_path)
        file_content = file.decode('utf-8')

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

        Represents every written test (or exam) that must be taken during this process. Any test other than written with multiple alternatives choices and true or false questions must not be mapped - as physical or psychological evaluations. DO NOT include writing tests, essays or physical proficiency tests. Is expected that a recruitment offer has at least one exam, however it might have many exams that evaluate different candidates for different job roles.

        An exam has the following properties:

        - name: Based on the context, give it a name so it can be identified. MUST be unique for each exam. May reference a job role, educational level or other related information.
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
        - examining_board: The name of the institution responsible for conducting the exams
        - year: The year when the process was published
        - scope: Process scope in the public administration (LOCAL, STATE, FEDERAL)
        - city: The city related to the process (only if the `scope` is LOCAL, else `undefined`)
        - state: The Brazil state acronym (only two letters) related to the process (only if the `scope` is LOCAL or STATE, else `undefined`).

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

        response = self.deepseek_service.chat_completion(
            system_prompt, user_prompt)

        return response.choices[0].message.content

    def populate_exam_subtopics(self, file_content, identified_exams, exam_id):
        exam = next((d for d in identified_exams if d.get('id') == exam_id), None)

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

        The JSON output must be a single object array `exam_topics` with the `subtopics` property populated.

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

        Extract the subtopics for the exam with the following id: `{exam["name"]}`. The output json object should reflect only this exam.

        # File Content

        ```txt
        {file_content}
        ```
        """

        response = self.deepseek_service.chat_completion(
            system_prompt, user_prompt)

        return response.choices[0].message.content

    def populate_job_roles(self, file_content, identified_exams, exam_id):
        exam = next((d for d in identified_exams if d.get('id') == exam_id), None)

        system_prompt = """
        # Objective

        You are tasked with analyzing the provided text content of a PDF document, which details information about public sector recruitment. The document is in Brazilian Portuguese. Your goal is to **extract the job roles** for the exam provided in the context, and structure them under their corresponding properties.

        **CRITICAL CONSTRAINT:** The ONLY output must be the raw JSON array, starting with `[` and ending with `]`. DO NOT include any markdown formatting (e.g., ```json), commentary, or explanation. All extracted text values must be in the original Brazilian Portuguese.

        # Database entity

        ## `job_roles`

        Represents the job roles given an exam. Those candidates who took an exam have the chance of being nominated for that job. Job roles are related to exams. An exam may have one or many job roles.

        `job_roles` have the following properties.

        - name: The name of the job role
        - salary: The salary value for the job role
        - openings: The number of openings for the job role
        - verification_exam_name: Why does this role belong to the requested ID?

        ```json
        name: string,
        salary: number,
        openings: number,
        verification_exam_name: string
        ```

        # Output 

        The JSON output must be a single object array of the `job_roles` entity given a certain exam previously identified. ONLY return job roles related to the exam which id have been passed. Job roles related to other identified exams must not be in the output result.

        ```json
        [
            {
                name: string,
                salary: number,
                openings: number
            },
        ],
        ```
        """

        user_prompt = f"""
        # Identified exams

        Here are the exams that have been identified from that same PDF file content (the topics from each exam have also been identified):

        ```json
        {identified_exams}
        ```

        # Instructions

        Extract the job roles for the exam with the following name: `{exam["name"]}`. The output json object should reflect only this exam. All job roles related to other exams must be ignored

        # File Content

        ```txt
        {file_content}
        ```
        """

        response = self.deepseek_service.chat_completion(
            system_prompt, user_prompt)

        return response.choices[0].message.content

    def populate_offices(self, file_content, identified_exams, exam_id):
        exam = next((d for d in identified_exams if d.get('id') == exam_id), None)

        system_prompt = """
        # Objective

        You are tasked with analyzing the provided text content of a PDF document, which details information about public sector recruitment. The document is in Brazilian Portuguese. Your goal is to **extract the office entity** for the exam provided in the context, and structure them under their corresponding properties.

        **CRITICAL CONSTRAINT:** The ONLY output must be the raw JSON array, starting with `[` and ending with `]`. DO NOT include any markdown formatting (e.g., ```json), commentary, or explanation. All extracted text values must be in the original Brazilian Portuguese.

        # Database entity

        ## `offices`

        Represents the public sector entity that will employ the candidate that took and was approved at the exam. This entities has a relationship with a certain exam, meaning that an exam has one or more offices.

        `offices` have the following properties.

        - name: The name of the public section office (or institution)

        ```json
        name: string,
        ```

        # Output 

        The JSON output must be a single object array of the `offices` entity given a certain exam previously identified.

        ```json
        [
            {
                name: string,
            },
        ],
        ```
        """

        user_prompt = f"""
        # Identified exams

        Here are the exams that have been identified from that same PDF file content:  

        ```json
        {identified_exams}
        ```

        # Instructions

        Extract the offices for the exam with the following id: `{exam["name"]}`. The output json object should reflect only this exam.

        # File Content

        ```txt
        {file_content}
        ```
        """

        response = self.deepseek_service.chat_completion(
            system_prompt, user_prompt)

        return response.choices[0].message.content