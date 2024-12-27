import requests

base_URL = "http://json-server:3000/components/"


def API_request(subfolder):
    """
    Args:
        subfolder list representing API path: [folder1,folder2] -> .../folder1/folder2
    Returns:
        (data, if list): returns the
    """

    try:
        print(base_URL + "/".join(subfolder))
        response = requests.get(base_URL + "/".join(subfolder))
        response.raise_for_status()
        json_data = response.json()

        is_list = "components" in json_data

        return json_data if is_list else list(json_data.keys()), is_list

    except requests.exceptions.RequestException as e:
        print(e)
        return None


def pick_component(query, cat):
    print("##################")
    response = API_request(["Active", "Diodes", "Rectifier_Diodes"])
    if not response:
        return "API ERROR"

    print(response)
    print("##################")

    return "component"
