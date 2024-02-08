from typing import Any
import requests
import os
import logging
import sys
import re
import json
from time import sleep
from transformers import AutoTokenizer
from dotenv import dotenv_values
from app.icog_util import truncate_text


logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s - %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

config = dotenv_values(".env")


class PromptTemplates:
    def __init__(self) -> None:
        self.template = ""
        pass

    def getTemplate(self) -> str:
        return self.template

    def __name__(self) -> str:
        return self.__class__.__name__

    def __call__(self, text):
        pass


class OneLinerTemplate(PromptTemplates):
    def __init__(self):
        super(OneLinerTemplate, self).__init__()
        self.template = """
            <s>[INST] <<SYS>>
            You are a researcher task in summarizing and writing concise brief of articles.  
            Please ensure that your responses are socially unbiased and positive in nature.
            If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. 
            If you don't know the answer, please don't share false information.
            <</SYS>>
            In one sentence, tell me what is the main idea of the following article. Limit the answer to tweenty words. 
            Article: {BODY}
            [/INST]"""

    def __call__(self, text) -> str:
        return self.template.format(BODY=text)


class BulletPointTemplate(PromptTemplates):
    def __init__(self):
        super(BulletPointTemplate, self).__init__()
        self.template = """<s>[INST]<<SYS>>
            You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe.  
            Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. 
            Please ensure that your responses are socially unbiased and positive in nature.
            If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. 
            If you don't know the answer to a question, please don't share false information.
            <</SYS>>
            Write a concise TL;DR summary in numeric bullet-points for the following article. Only include bullet-points. 
            Limit the number of bullet-point to five. Output the answer in JSON format [{{"1", bullet-point}}, {{"2", bullet-point}}, ...]
            Article: {BODY}[/INST]"""

    def __call__(self, text) -> str:
        return self.template.format(BODY=text)


class InclusiveTemplate(PromptTemplates):
    def __init__(self):
        super(InclusiveTemplate, self).__init__()
        self.template = """<s>[INST] <<SYS>>
        You are a researcher task with answering questions about an article.  
        Please ensure that your responses are socially unbiased and positive in nature.
        If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. 
        If you don't know the answer, please don't share false information.

        <</SYS>>

        Answers output must confirm to the this JSON format [/INST] 

        JSON Output: {{
        "oneSentenceSummary" : "Mobile game soft launch is a process of releasing a game to a limited audience for testing.",
        "summaryInNumericBulletPoints" : [
        "1. Mobile game soft launch is a process of releasing a game to a limited audience for testing.",
        "2. Mobile game soft launch is a process of releasing a game to a limited audience for testing.",
        ],
        "entities" : [
        {{"name": "semiconductor", "type": "industry", "explanation": "Companies engaged in the design and fabrication of semiconductors and semiconductor devices"}},
        {{"name": "NBA", "type": "sport league", "explanation": "NBA is the national basketball league"}},
        {{"name": "Ford F150", "type": "vehicle", "explanation": "Article talks about the Ford F150 truck"}},
        ],
        "concepts_ideas": [
            {{"concept": "mobile game soft launch", "explanation": "Mobile game soft launch is a process of releasing a game to a limited audience for testing."}},
            {{"concept": "US Civil War", "explanation": "The American Civil War was a civil war in the United States between the Union and the Confederacy, which had been formed by states that had seceded from the Union. The central cause of the war was the dispute over whether slavery would be permitted to expand into the western territories, leading to more slave states, or be prevented from doing so, which many believed would place slavery on a course of ultimate extinction."}},
            {{"concet": "Capitalism", "explanation": Capitalism is an economic system based on the private ownership of the means of production and their operation for profit. Central characteristics of capitalism include capital accumulation, competitive markets, price system, private property, property rights recognition, voluntary exchange, and wage labor."}}    
        ] 
        }} </s>

        <s>[INST]
        Use the examples above to answer the following questions.
        1. Summarize the article in one sentence. Limit the answer to twenty words.
        2. Summarize the article in multiple bullet-points. Each bullet-point need to have betweeen ten to tweenty words. Limit the number of bullet points must below six.
        3. Identify ten entities (companies, people, location, products....) mentioned in the article. Include short explanation for each entity.
        4. Identify three concepts or ideas mentioned in the article. Include short explanation for each concept or idea.

        Use the JSON format above to output your answer. Only output valid JSON format.
        Article: {BODY}
        [/INST]"""

    def __call__(self, text) -> str:
        return self.template.format(BODY=text)

    def handleResponse(self, response: dict) -> dict:
        try:
            answer = response["output"]["choices"][0]["text"]
            json_start = answer.find("{")
            json_end = answer.rfind("}")
            answer = answer[json_start : json_end + 1]
            answer = json.loads(answer)
            oneSentence = answer["oneSentenceSummary"]
            bulletPoints = answer["summaryInNumericBulletPoints"]
            entities = answer["entities"]
            concepts = answer["concepts_ideas"]

            if (
                (len(oneSentence) > 1)
                and (len(bulletPoints) > 1)
                and (len(entities) > 0)
                and (len(concepts) > 0)
            ):
                return answer
            else:
                raise ValueError("One of the answers is empty")
                return None

        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON: {e}")
            return None


class ConceptsTemplate(PromptTemplates):
    def __init__(self):
        super(ConceptsTemplate, self).__init__()
        self.template = """<s>[INST] <<SYS>>
            You are a researcher task with answering questions about an article.  
            Please ensure that your responses are socially unbiased and positive in nature.
            If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. 
            If you don't know the answer, please don't share false information.

            Output answer in JSON using the following format: {{"name": name, "type": type, "explanation": explanation}}
            <</SYS>>

            What entities mentioned in the article that can generalize the topic? [/INST] 
            [
            {{"name": "semiconductor", "type": "industry", "explanation": "Companies engaged in the design and fabrication of semiconductors and semiconductor devices"}},
            {{"name": "NBA", "type": "sport league", "explanation": "NBA is the national basketball league"}},
            {{"name": "Ford F150", "type": "vehicle", "explanation": "Article talks about the Ford F150 truck"}},
            ] </s>

            <s>[INST]   
            What entities mentioned are important to the article subject? Limit the answert to ten most important entities. 
            Output answer in JSON using the following format: {{"name": name, "type": type, "explanation": explanation}}
            Article: {BODY}
            [/INST]"""

    def __call__(self, text) -> str:
        return self.template.format(BODY=text)


class TogetherMixtralClient:
    """
    APIModel class is used to generate summaries by calling the Together Mistral 7x8 Service.

    It handles constructing the API request, sending it, and processing the response.

    Key responsibilities:
    - Initialize the API client with auth token and endpoint
    - Build the API request payload from the input text
    - Send request to API and get response
    - Extract and clean up the summary text from the API response
    """

    def __init__(self) -> None:
        self._api_token = config["TOGETHER_TOKEN"]
        self._options = {"use_cache": True}
        self._api_url = "https://api.together.xyz/inference"
        self._model_name = "mistralai/Mixtral-8x7B-Instruct-v0.1"
        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._max_length = 32000
        self._retry_sleep = 30
        self._retry_attempts = 0
        self._retry_max_attempts = 2
        self._templates = PromptTemplates()

    def build_query(self, templete: str, body_text: str) -> str:
        results = templete.format(BODY=body_text)
        tokens = self._tokenizer.encode(results, return_tensor="np")
        if len(tokens[0]) > self._max_length:
            logging.warn(f"Query is too big, let shorten the body text")

        return results

    def api_call(self, payload) -> dict:
        API_URL = self._api_url
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "content-type": "application/json",
            "accept": "application/json",
            "User-Agent": "Icognition App",
        }

        response = requests.post(API_URL, headers=headers, json=payload)
        # Check if the response is valid
        status = response.status_code
        # In case the service isn't ready or overloaded
        if status != 200:
            logging.info(
                f"API Call Error: {response.content}. Status code: {response.status_code}"
            )

        elif response.status_code == 200:
            try:
                results = response.json()
                logging.info(
                    f"API Call successful. Status code {response.status_code}. Generated text length: {len(results)}"
                )
                return results
            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON response: {response}")
                return None
        else:
            logging.error(
                f"Response from HF API isn't right. Status code: {response.status_code} Contenct {response.content}"
            )
            return None

    def generate(
        self,
        body_text: str,
        template: PromptTemplates = InclusiveTemplate(),
        temperature=0.2,
        top_p=0.8,
        top_k=70,
    ) -> dict:
        ## Use template to generate prompt
        prompt = template(body_text)
        ## Build payload
        payload = {
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": 1,
        }

        logging.info(f"Sending query to API with template: {template.__name__}...")
        continue_loop = True
        self._retry_attempts = 0

        while continue_loop:
            try:
                self._retry_attempts += 1
                logging.debug(f"Attempt {self._retry_attempts} to generate summary")
                res = self.api_call(payload)
                logging.debug(f"Response status: {res['status']}")
                answer = template.handleResponse(res)
            except Exception as e:
                logging.error(f"Error calling API and/or handleResponse: {e}")
                raise Exception(e)

            if answer is not None:
                logging.debug(
                    f"Answer is not None. Stop retrying. Number of attempts {self._retry_attempts}"
                )
                continue_loop = False
            elif self._retry_attempts <= self._retry_max_attempts:
                logging.debug(
                    f"Answer is None. Retry. Number of attempts {self._retry_attempts}"
                )
                continue_loop = True
                sleep(self._retry_sleep)
            else:
                continue_loop = False
                logging.error(
                    f"Exitting retry loop. Number of attempts {self._retry_attempts}"
                )

        return res
