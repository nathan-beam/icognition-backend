import requests
import logging
import sys
import json
from dotenv import dotenv_values


logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s - %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

config = dotenv_values(".env")


class NerClient:
    """
    NerCaller is a class that wrap NER service. The class call the service with text and return list of identified

    Key responsibilities:
    - Initialize the API client with auth token and endpoint
    - Build the API request payload from the input text
    - Send request to API and get response
    - Extract and clean up the summary text from the API response
    """

    def __init__(self) -> None:
        self.url = config["NER_SERVICE_URL"]

    def __call__(self, text: str) -> list:
        payload = {"text": text}
        headers = {"content-type": "application/json", "accept": "application/json"}
        response = requests.post(self.url, headers=headers, json=payload)

        if response.status_code == 200:
            try:
                results = response.json()
                logging.info(
                    f"NER API Call successful. Status code {response.status_code}. Identify: {len(results)} entities"
                )
                if len(results) > 0:
                    return results
                else:
                    return None

            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON response: {response}")
                return None
        else:
            logging.error(f"Error calling NER service: {response.status_code}")


if __name__ == "__main__":
    caller = NerClient()
    entities = caller(
        "Roger bought an Apple computer on Amazon for $500. Jeff is driving Toyota 2020"
    )

    for ent in entities:
        print(ent)
