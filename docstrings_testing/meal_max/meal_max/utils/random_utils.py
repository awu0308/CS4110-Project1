import logging
import requests

from music_collection.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


def get_random(num_songs: int) -> int:
    """
    Fetches a random 2 decimal float between 0 and 1 from random.org

    Returns:
        float: the random number from random.org.
    Raises:
        RuntimeError: if the request to random.org fails or returns an invalid response
        ValueError: if the response from random.org is not a valid float
    """
    url = f"https://www.random.org/integers/?num=1&min=1&max={num_songs}&col=1&base=10&format=plain&rnd=new"

    try:
        # Log the request to random.org
        logger.info("Fetching random number from %s", url)

        response = requests.get(url, timeout=5)

        # Check if the request was successful
        response.raise_for_status()

        random_number_str = response.text.strip()

        try:
            random_number = int(random_number_str)
        except ValueError:
            raise ValueError("Invalid response from random.org: %s" % random_number_str)

        logger.info("Received random number: %.3f", random_number)
        return random_number

    except requests.exceptions.Timeout:
        logger.error("Request to random.org timed out.")
        raise RuntimeError("Request to random.org timed out.")

    except requests.exceptions.RequestException as e:
        logger.error("Request to random.org failed: %s", e)
        raise RuntimeError("Request to random.org failed: %s" % e)