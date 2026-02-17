from app.supabase.supabase_service import SupabaseService
from app.deepseek_api.deepseek_api_service import DeepSeekApiService


class ExtractorService:
    def __init__(self):
        self.supabase_service = SupabaseService()
        self.deepseek_service = DeepSeekApiService()

    def populate_base_entities(self, file_bucket: str, file_path: str, header_filter: list = None, model: str = "deepseek-chat"):
        file = self.supabase_service.download_file_from_s3(
            file_bucket, file_path)

        file_content = file.decode('utf-8')

        if header_filter is not None:
            file_content = self.slice_content_by_headers(
                file_content, header_filter)

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
            system_prompt, user_prompt, model=model)

        return response.choices[0].message.content

    def populate_exam_subtopics(self, file_bucket: str, file_path: str, identified_exams: list, exam_id: str, header_filter: list = None, model: str = "deepseek-chat"):
        file = self.supabase_service.download_file_from_s3(
            file_bucket, file_path)

        file_content = file.decode('utf-8')

        if header_filter is not None:
            file_content = self.slice_content_by_headers(
                file_content, header_filter)

        exam = next(
            (d for d in identified_exams if d.get('id') == exam_id), None)

        system_prompt = """
        # Objective
        You are an expert at parsing "Conteúdo Programático" from Brazilian public exams.
        Your goal is to map specific subtopics to their parent macro-topics.

        # Extraction Rules
        1. SCOPE: Only process the exam with the specific ID/Name provided.
        2. SUBTOPIC GRANULARITY: 
        - Extract distinct subjects (e.g., "Crase", "Regência").
        - DO NOT extract long descriptions, law articles (e.g., "Art. 1º ao 5º"), or administrative observations.
        - Clean the text: Remove leading dashes, dots, or numbers (e.g., "1.1. Crase" -> "Crase").
        3. HIERARCHY: If the text says "Matemática: Álgebra, Geometria", then "Matemática" is the Name and the others are Subtopics.

        # Schema (exam_topics)
        - name: The macro area/subject (e.g., "Direito Administrativo")
        - subtopics: Array of strings representing the granular items to be studied.

        # Constraint
        OUTPUT ONLY THE RAW JSON ARRAY. NO MARKDOWN. NO PREAMBLE.
        """

        user_prompt = f"""
        # Context: Previously Identified Topics
        Use these as your primary "Name" keys if they appear in the text:
        {identified_exams}

        # Document Source Text
        ### START OF CONTENT ###
        {file_content}
        ### END OF CONTENT ###

        # Final Instructions
        1. Target Exam: "{exam["name"]}"
        2. Tasks: 
            - Identify the sections in the text belonging to this exam.
            - Map the granular subjects found to the parent topics.
            - If a topic from the "Identified Topics" list is found, populate its `subtopics` array.
        3. Output: Return the completed JSON array for this exam only.
        """

        response = self.deepseek_service.chat_completion(
            system_prompt, user_prompt, model=model)

        return response.choices[0].message.content

    def populate_job_roles(self, file_bucket: str, file_path: str, identified_exams: list, exam_id: str, header_filter: list = None, model: str = "deepseek-chat"):
        file = self.supabase_service.download_file_from_s3(
            file_bucket, file_path)

        file_content = file.decode('utf-8')

        if header_filter is not None:
            file_content = self.slice_content_by_headers(
                file_content, header_filter)

        exam = next(
            (d for d in identified_exams if d.get('id') == exam_id), None)

        system_prompt = """
       # Objective
        You are a specialized parser for Brazilian Public Sector Recruitment (Concursos Públicos). 
        Extract job roles for a specific exam from the provided text.

        # Extraction Rules
        1. LANGUAGE: Keep all text in original Brazilian Portuguese.
        2. NUMBERS: Convert salary and openings to pure numbers (e.g., "R$ 5.000,00" -> 5000.00). Use null if not found.
        3. CR: If a role is strictly "Cadastro Reserva", set openings to 0 and has_cr_openings to the true (event if "CR" is mentioned without a number).
        4. SCOPE: Only extract roles belonging to the specific exam name provided.

        # Schema (job_roles)
        - name (string)
        - salary (number)
        - openings (number): Total direct vacancies. Considers all direct openings like "ampla concorrência", "PCD (pessoa com deficiência)", "cota racial", etc. 
        - has_cr_openings (bool): Whether or not the job role has any cr openings.

        # Constraint
        OUTPUT ONLY THE JSON ARRAY. NO MARKDOWN, NO EXPLANATION.
        """
    
        user_prompt = f"""
        # Context: Identified Exams
        {identified_exams}

        # Document Source Text
        ### START ###
        {file_content}
        ### END ###

        # Final Task
        1. Target Exam: "{exam["name"]}"
        2. Find all job roles associated with this exam.
        3. Return the data as a JSON array matching the schema provided in your instructions.
        4. Reminder: Return ONLY the raw JSON.
        """

        response = self.deepseek_service.chat_completion(
            system_prompt, user_prompt, model=model)

        return response.choices[0].message.content

    def populate_offices(self, file_bucket: str, file_path: str, identified_exams: list, exam_id: str, header_filter: list = None, model: str = "deepseek-chat"):
        file = self.supabase_service.download_file_from_s3(
            file_bucket, file_path)

        file_content = file.decode('utf-8')

        if header_filter is not None:
            file_content = self.slice_content_by_headers(
                file_content, header_filter)
            
        exam = next(
            (d for d in identified_exams if d.get('id') == exam_id), None)

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
            system_prompt, user_prompt, model=model)

        return response.choices[0].message.content

    def slice_content_by_headers(self, content: str, headers: list) -> str:
        """
        Slices content from a 'selected: True' header up to the 
        start of the next 'selected: False' header.
        """
        sliced_parts = []
        included_headers = []
        for i, item in enumerate(headers):
            if item.get("selected") is True:
                header_text = item.get("header")
                
                if header_text in included_headers:
                    continue

                start_index = content.find(header_text)

                if start_index == -1:
                    continue

                end_index = len(content)

                for next_item in headers[i + 1:]:
                    if next_item.get("selected") is False:
                        next_header_text = next_item.get("header")
                        find_next = content.find(
                            next_header_text, start_index + len(header_text))
                        if find_next != -1:
                            end_index = find_next
                            break
                    else:
                        included_headers.append(next_item.get("header"))

                sliced_parts.append(content[start_index:end_index].strip())

        return "\n\n".join(sliced_parts)
