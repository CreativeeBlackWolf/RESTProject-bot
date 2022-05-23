import re
from typing import List


def find_urls(text: str, template: str = None) -> List[str]:
    """
    Find URLs in given string.

    Returns list of URLs.

    Paremeters
    ----------
    `text`
        Text in which to find links.
    
    `template`
        A link template. If given, 
        function will return links that satisfy the specified template.
    """
    regex = \
r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, text)
    if not template:
        return [i[0] for i in url]
    return [i[0] for i in url if template in i[0]]
