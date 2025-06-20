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

def render_article_cell(article):
    return f'''
    <div style="flex:1 0 200px;max-width:250px;min-width:180px;background:#fafafa;border-radius:8px;padding:10px;margin:8px;box-shadow:0 1px 4px rgba(0,0,0,0.06);display:flex;flex-direction:column;align-items:center;">
        <a href="{article['link']}" target="_blank" style="text-decoration:none;">
            <img src="{article['img']}" alt="{article['title']}" style="width:100px;height:100px;object-fit:cover;border-radius:6px;margin-bottom:10px;">
            <div style="font-weight:bold;text-align:center;margin-bottom:6px;">{article['title']}</div>
        </a>
        <div style="font-size:12px;color:#888;text-align:center;">{article['date']}</div>
    </div>
    '''

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
    new_grid = render_article_cell(article) + '\n' + old_grid

    new_html = f'''
{GRID_START}
<div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-start;">
{new_grid}
</div>
{GRID_END}
'''.strip()

    if grid_match:
        updated_content = re.sub(f'{GRID_START}.*?{GRID_END}', new_html, content, flags=re.DOTALL)
    else:
        updated_content = content + '\n\n' + new_html

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print('README updated successfully.')

if __name__ == '__main__':
    try:
        update_readme()
    except Exception as e:
        print(f'Error occurred: {str(e)}')
        exit(1)
