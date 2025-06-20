import requests
import feedparser
import random
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
import re

TOPICS = ['.NET', 'C#', 'Azure', 'Blazor', 'Entity Framework', 'ASP.NET Core', 'Microservices']
GRID_START = '<!-- ARTICLES-GRID-START -->'
GRID_END = '<!-- ARTICLES-GRID-END -->'

def get_random_topic():
    return random.choice(TOPICS)

def fetch_microsoft_devblogs():
    url = 'https://devblogs.microsoft.com/dotnet/feed/'
    feed = feedparser.parse(url)
    if not feed.entries:
        return None
    article = feed.entries[0]
    img_url = 'https://devblogs.microsoft.com/dotnet/wp-content/uploads/sites/10/2019/07/dotNET_bot.png'
    return {
        'title': article.title,
        'link': article.link,
        'img': img_url,
        'date': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M UTC')
    }

def fetch_medium_search(topic):
    search_query = topic.replace(' ', '+')
    url = f'https://medium.com/search?q={search_query}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    article_block = soup.select_one('div.postArticle')
    if not article_block:
        return None
    title_tag = article_block.select_one('h3')
    link_tag = article_block.select_one('a')
    img_tag = article_block.select_one('img')
    title = title_tag.text.strip() if title_tag else 'Medium Article'
    link = link_tag['href'].split('?')[0] if link_tag else url
    img = img_tag['src'] if img_tag else 'https://cdn-icons-png.flaticon.com/512/5968/5968885.png'
    return {
        'title': title,
        'link': link,
        'img': img,
        'date': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M UTC')
    }

def get_latest_article():
    return fetch_microsoft_devblogs() or fetch_medium_search(get_random_topic())

def render_article_cell_md(article):
    return f"""| [![{article['title']}]({article['img']})]({article['link']}) | **[{article['title']}]({article['link']})**<br/>🕒 {article['date']} |"""

def update_readme():
    article = get_latest_article()
    if not article:
        print('No article found.')
        return

    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = ''

    grid_match = re.search(f'{GRID_START}(.*?){GRID_END}', content, re.DOTALL)
    old_grid = grid_match.group(1).strip() if grid_match else ''
    old_rows = old_grid.split('\n')[2:] if old_grid.startswith("| Article") else []  # skip header lines

    new_row = render_article_cell_md(article)
    if new_row in old_rows:
        print("Article already exists, not adding duplicate.")
        return

    trimmed_rows = [new_row] + old_rows[:4]  # keep max 5 articles

    new_table = (
        "| Article | |\n"
        "|--------|--|\n"
        + "\n".join(trimmed_rows)
    )

    new_content = f"{GRID_START}\n{new_table}\n{GRID_END}"

    if grid_match:
        updated_content = re.sub(f'{GRID_START}.*?{GRID_END}', new_content, content, flags=re.DOTALL)
    else:
        updated_content = content + '\n\n' + new_content

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print('README updated successfully.')

if __name__ == '__main__':
    try:
        update_readme()
    except Exception as e:
        print(f'Error occurred: {str(e)}')
        exit(1)
