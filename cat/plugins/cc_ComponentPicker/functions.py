import requests
import json

base_URL = "http://json-server:3000/components/"


def API_request(subfolder):
    """
    Args:
        subfolder list representing API path: [folder1,folder2] -> .../folder1/folder2
    Returns:
        (data, if list): returns the
    """

    # inefficient API request just for example

    try:
        response = requests.get(base_URL)
        response.raise_for_status()
        json_data = response.json()

        for folder in subfolder:
            json_data = json_data[folder]

        is_list = "components" in json_data
        if is_list:
            json_data.pop("components")

        return json_data if is_list else list(json_data.keys()), is_list

    except requests.exceptions.RequestException as e:
        print(e)
        return None


def look_into_categories(path: list, query_component, cat):
    categories = API_request(path)
    if not categories:
        return []

    if categories[1]:
        return [str(categories[0])]

    cat_query = f"""You are an electronics component picker, and you need to classify some component requests in the correct category.
From the component characteristics and type, and given the categories, choose the categories that include the component itself.

If the component can be inside more than one category, select also that categories.
If in the description of the component are specified more components, select all the relative categories, EXAMPLE: component= {{transistor:{{type:"NPN or PNP"}}}} -> in this case it should be classified as NPN AND PNP.
If the component is missing a detail to classify it, respond with ["#","@DETAIL@"], where @DETAIL@ is what's missing from the description, for example @MAX_CURRENT@.

Your response MUST be an UNFORMATTED PURE JSON list, containing strings representing exactly the category names.

REQUESTED COMPONENT:
{query_component}

CATEGORIES:
{categories[0]}"""

    cat_categories = json.loads(cat.llm(cat_query))

    return_result = []

    if "#" in cat_categories:
        return cat_categories

    for category in cat_categories:
        new_path = path + [category]

        new_categories = look_into_categories(new_path, query_component, cat)
        if "#" in new_categories:
            return new_categories

        return_result += new_categories

    return return_result


def pick_component(query_component, cat):

    components = look_into_categories([], query_component, cat)

    if "#" in components:
        return components[1], False
    else:
        return "\n-".join(components), True
