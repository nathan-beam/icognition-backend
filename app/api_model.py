import requests
import os
import logging
import sys
import re
from time import sleep
from transformers import AutoTokenizer
from dotenv import dotenv_values
from app.icog_util import truncate_text


logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

config = dotenv_values(".env")


class LlamaTemplates():
    def __init__(self) -> None:
        pass

    # Replace long space bigger then 2 with single space
    def clean_text(self, text: str) -> str:
        return re.sub(r'\s{2,}', ' ', text)

    def summarize(self, body_text: str) -> str:
        return self.clean_text(self.templates['summarize'].format(BODY=body_text))

    def buletPoints(self, body_text: str) -> str:
        return self.clean_text(self.templates['bullet-points'].format(BODY=body_text))

    def peopleOrgPlaces(self, body_text: str) -> str:
        return self.clean_text(self.templates['people-org-places'].format(BODY=body_text))

    @property
    def templates(self) -> dict:
        return {
            "summarize": """
                Write a summary of the following text delimited by triple backquotes.
                {BODY}
                SUMMARY:""",
            "bullet-points": """
                Write a very concise summary of the following text delimited by triple backquotes. Write the summary in bullet points which covers the key points of the text.
                {BODY}
                BULLET POINTS SUMMARY:""",
            "people-org-places": """
                Extract people, organizations and places from the following text and output them by entity type
                {BODY}
                EXTRACTED NAMES, ORGANIZATIONS AND PLACES:""",
            "empty": """{INSTRUCTIONS}
                         {BODY}
                         {RESULTS}""",
        }


class APIModel():
    """
    APIModel class is used to generate summaries by calling the HuggingFace API.

    It handles constructing the API request, sending it, and processing the response.

    Key responsibilities:
    - Initialize the API client with auth token and endpoint
    - Build the API request payload from the input text 
    - Send request to API and get response
    - Extract and clean up the summary text from the API response
    """

    def __init__(self) -> None:
        self._api_token = config['HF_API_TOKEN']
        self._options = {'use_cache': True}
        self._base_url = "https://api-inference.huggingface.co/models/"
        self._model_name = "meta-llama/Llama-2-70b-chat-hf"
        self._api_url = self._base_url + self._model_name
        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        # self._api_token = os.environ['HF_API_TOKEN']
        self._max_length = 4096
        self._retry_sleep = 30
        self._retry_attempts = 0
        self._retry_max_attempts = 2
        self._templates = LlamaTemplates()
        self._parameters = {'max_length': 4000,
                            'max_new_tokens': 1000,
                            'top_k': 10,
                            'return_full_text': False,
                            'do_sample': True,
                            'num_return_sequences': 1,
                            'temperature': 0.7,
                            'repetition_penalty': 1.0,
                            'length_penalty': 1.0}

    def build_query(self, templete: str, body_text: str) -> str:
        results = templete.format(BODY=body_text)
        tokens = self._tokenizer.encode(results, return_tensor='np')
        if (len(tokens[0]) > self._max_length):
            logging.warn(f"Query is too big, let shorten the body text")

        return results

    def api_call(self, payload: dict) -> dict:
        API_URL = self._api_url
        headers = {"Authorization": f"Bearer {self._api_token}"}

        response = requests.post(API_URL, headers=headers, json=payload)

        # If error true, sleep for 30 seconds and
        # try again.
        # If error still true, return error message.
        if (response.status_code == 503 and (self._retry_attempts < self._retry_max_attempts)):
            logging.info(
                f"API Call Error: {results['error']}. Retrying in {self._retry_sleep} seconds")
            self._retry_attempts += 1
            sleep(self._retry_sleep)
            logging.info(f"Retrying now")
            self.api_call(payload)
        elif (response.status_code == 503 and self._retry_attempts >= self._retry_max_attempts):
            self._retry_attempts = 0
            logging.warn(f"Retry limit reached. Returning error")
            raise ResourceWarning("Retry limit reached. Returning an error")
        elif (response.status_code == 200):
            try:
                results = response.json()
                answer = results[0]['generated_text']
                logging.info(
                    f"API Call successful. Status code {response.status_code}. Generated text length: {len(answer)}")
                self._retry_attempts = 0
                return answer
            except JSONDecodeError(e):
                logging.error(f"Error decoding JSON response: {response}")
                raise JSONDecodeError(e)

    def generate(self, query) -> str:

        parameters = {'max_length': 4000, 'max_new_tokens': 1000, 'top_k': 10, 'return_full_text': False, 'do_sample': True,
                      'num_return_sequences': 1, 'temperature': 0.7, 'repetition_penalty': 1.0,
                      'length_penalty': 1.0}
        options = {'use_cache': False}

        logging.info(f"Sending query to API: {query[:20]}...")

        payload = {"inputs": query,
                   "parameters": parameters, "options": options}

        try:
            results = self.api_call(payload)
            logging.info(
                f"API Call successful. Returning results. len(results): {len(results)}")
            return results
        except ResourceWarning as e:
            logging.error(e)
            raise ResourceWarning(e)
        except Exception as e:
            logging.error(e)
            raise Exception(e)


if __name__ == "__main__":
    model = APIModel()
    logging.info("Generating summary")
    query = model._templates.summarize("""The US has passed the peak on new coronavirus cases, \
        President <NAME> said and predicted that some states would reopen this month. The US has over 637,000 confirmed \
        Covid-19 cases and over 30,826 deaths, the highest for any country in the world. At the daily White House coronavirus briefing on Wednesday,\
        Trump said new guidelines to reopen the country would""")

    print(model.generate(query))

    query = model._templates.buletPoints("""Evidence that dozens of women were groomed into online sex work by members of influencer Andrew Tate's "War Room" group has been uncovered by the BBC.
Leaked internal chat logs identify 45 potential victims between March 2019 and April 2020 but the total number is likely to be higher.
The texts also appear to show the techniques used by War Room members to exploit possible victims.
Mr Tate denies any wrongdoing and says he is prepared to defend his innocence.
Warning: Some readers may find details of this report disturbing
A statement issued by his press officer said the BBC's findings represent "another brazen attempt to present one-sided, unverified" allegations against him.
The 36-year-old former kickboxer has been charged in Romania with rape and human trafficking.
On 4 August he was released from house arrest pending his trial. Last week details of graphic evidence compiled by Romanian prosecutors were revealed by the BBC.
His brother Tristan and two associates also face charges. All have denied the allegations.
The BBC's latest investigation - outlined in the documentary Andrew Tate: The Man Who Groomed the World? - centres on 12,000 pages of encrypted Telegram messages sent by hundreds of War Room members.
However the BBC's access to the logs was limited to those sent over a period of 13 months - so the total number of women possibly targeted and exploited by the group, which was formed in 2019, could be much higher""")

    print(model.generate(query))

    query = model._templates.peopleOrgPlaces("""Evidence that dozens of women were groomed into online sex work by members of influencer Andrew Tate's "War Room" group has been uncovered by the BBC.
Leaked internal chat logs identify 45 potential victims between March 2019 and April 2020 but the total number is likely to be higher.
The texts also appear to show the techniques used by War Room members to exploit possible victims.
Mr Tate denies any wrongdoing and says he is prepared to defend his innocence.
Warning: Some readers may find details of this report disturbing
A statement issued by his press officer said the BBC's findings represent "another brazen attempt to present one-sided, unverified" allegations against him.
The 36-year-old former kickboxer has been charged in Romania with rape and human trafficking.
On 4 August he was released from house arrest pending his trial. Last week details of graphic evidence compiled by Romanian prosecutors were revealed by the BBC.
His brother Tristan and two associates also face charges. All have denied the allegations.
The BBC's latest investigation - outlined in the documentary Andrew Tate: The Man Who Groomed the World? - centres on 12,000 pages of encrypted Telegram messages sent by hundreds of War Room members.
However the BBC's access to the logs was limited to those sent over a period of 13 months - so the total number of women possibly targeted and exploited by the group, which was formed in 2019, could be much higher""")

    print(model.generate(query))
