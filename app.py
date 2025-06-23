
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

openai.api_key = "YOUR_OPENAI_API_KEY"

def scrape_amazon(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')

    title = soup.select_one('#productTitle')
    title = title.get_text(strip=True) if title else 'No title found'

    feature_bullets = soup.select('#feature-bullets ul li')
    features = '\n'.join([b.get_text(strip=True) for b in feature_bullets])

    rating = soup.select_one('span[data-asin-average-rating]')
    if not rating:
        rating = soup.select_one('span.a-icon-alt')
    rating = rating.get_text(strip=True) if rating else 'No rating found'

    return {
        'title': title,
        'features': features,
        'rating': rating,
        'url': url
    }

def generate_review(product):
    prompt = f"""
Product Name: {product['title']}
Rating: {product['rating']}
Features:\n{product['features']}

Write a detailed, Google-friendly Amazon product review in clean HTML format. Follow these instructions:
- Write in a human-like personal tone as if you personally used the product.
- Add SEO-optimized headings (H1, H2, H3).
- Include a Quick Summary box.
- Provide Pros and Cons in bullet points.
- Add detailed product features in user-friendly language.
- Use EEAT principles: add personal experience, honest opinion, and practical tips.
- Add a Why I Recommend section.
- Include Google FAQ Schema at the end with 3 common questions and answers.
- Write in a way that can easily rank on Google in 2025.

Output format: Clean HTML.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional product review writer."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message['content']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate-review', methods=['POST'])
def generate():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    product = scrape_amazon(url)
    review_html = generate_review(product)

    return jsonify({
        'review_html': review_html
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
