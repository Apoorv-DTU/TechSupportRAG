from bs4 import BeautifulSoup

def document_from_html(filename):
    content = ""
    with open(filename, 'r') as file:
        content = file.read()
    
    return trim_irrelevant(content)

def trim_irrelevant(content):
    soup = BeautifulSoup(content, "html.parser")
    results = soup.find_all(class_="content")
    
    trimmed = '\n'.join([str(r) for r in results])
    return trimmed, soup.find("h1").text