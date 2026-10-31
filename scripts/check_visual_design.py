"""Check category membership, native links, and responsive media budgets."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.goals, self.images, self.projects = [], [], []
        self.card = False
        self.row = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'data-goal' in a:
            assert tag == 'a' and 'onclick' not in a
            assert a['href'] == f'/visual-design/sdgs/{a["data-goal"]}/'
            self.goals.append(a)
        if tag == 'article':
            self.card = 'project' in a.get('class', '').split()
            self.row = a.get('class', '')
        if tag == 'a' and self.card:
            
            if a['href'] not in self.projects:
                self.projects.append(a['href'])
        if tag == 'img':
            self.images.append((a, self.row))
    def handle_endtag(self, tag):
        if tag == 'article':
            self.card = False
            self.row = None


def parse(file):
    html = file.read_text(encoding='utf-8')
    assert 'sdg-detail' not in html and 'sdg-header.js' not in html
    parser = Page()
    parser.feed(html)
    assert [int(goal['data-goal']) for goal in parser.goals] == list(range(1, 18))
    for image, _ in parser.images:
        assert image.get('width') and image.get('height')
        assert image.get('src', '').endswith('.webp'), image.get('src')
        assert image.get('srcset') and image.get('sizes')
    return parser


def check(root=None):
    root = Path(root or ROOT)
    site = root / '.site'
    registry = json.loads((root / 'data/visual-design-projects.json').read_text(encoding='utf-8'))
    delivery = json.loads((root / 'docs/portfolio-image-delivery.json').read_text(encoding='utf-8'))['images']
    for project in registry:
        p = parse(site / project['url'].lstrip('/') / 'index.html')
        assert [int(goal['data-goal']) for goal in p.goals if goal['data-related'] == 'true'] == project['goals']
    overview = parse(site / 'visual-design/index.html')
    for number in range(1, 18):
        p = parse(site / f'visual-design/sdgs/{number}/index.html')
        expected = [row['url'] for row in registry if number in row['goals']]
        assert p.projects == expected, (number, p.projects, expected)
        related = [number]
        assert [int(goal['data-goal']) for goal in p.goals if goal['data-related'] == 'true'] == related
        html = (site / f'visual-design/sdgs/{number}/index.html').read_text(encoding='utf-8')
        assert '目前尚無對應作品' not in html and 'sdg-page-nav' not in html
        assert 'class="sdg-lead-icon"' in html
        assert 'grid-template-columns:var(--row-columns)' in (site/'brands/assets/visual-design.css').read_text(encoding='utf-8')
    first_screen = next(image for image, _ in overview.images if not image['data-original-src'].startswith('/brands/assets/sdg/'))
    assert first_screen['fetchpriority'] == 'high' and first_screen['loading'] == 'eager'
    assert all(image.get('loading') == 'eager' for image, _ in overview.images)
    # Estimate request bytes with native srcset selection. This is a file-size
    # budget, not a network timing or browser paint measurement.
    original = sum(delivery[src]['originalBytes'] for src in {image['data-original-src'] for image, _ in overview.images})
    estimates = []
    for viewport, dpr in [(390, 2), (1440, 1), (1440, 2)]:
        gutter, gap = (20, 8) if viewport <= 600 else (32, 12) if viewport <= 900 else (48, 12)
        available = min(1680, viewport - gutter*2)
        ratios = {'lifeline-project':(5.396158809300389,3),'scouts-project':(6.297436358904954,3),'election-project':(4.232518568179475,5)}
        requests = {}
        for image, row in overview.images:
            source = image['data-original-src']
            if source.startswith('/brands/assets/sdg/'):
                width = 64 if viewport <= 900 else viewport/17
            else:
                group = next(key for key in ratios if key in row)
                total, gaps = ratios[group]
                width = (available-gap*gaps) / total * float(image['width']) / float(image['height'])
                if source.endswith('/lifeline-project-views.png'):
                    width *= 2
            variants = delivery[source]['variants']
            choice = next((variant for variant in variants if variant['width'] >= width*dpr), variants[-1])
            requests[choice['url']] = choice['bytes']
        total = sum(requests.values())
        assert total < 2_000_000, (viewport, dpr, total)
        estimates.append({'viewport':viewport,'dpr':dpr,'imageBytes':total,'originalImageBytes':original,'reductionPercent':round((1-total/original)*100,1)})
    css = (site/'brands/assets/sdg-header.css').read_text(encoding='utf-8')
    assert '[data-sdg-scope="collection"] .sdg-button img{filter:none}' in css
    assert 'brightness(1.12)' in css and 'translateX(120%)' in css
    report = {'categories':17,'projectGoals':{row['id']:row['goals'] for row in registry},'overviewImageEstimates':estimates,'note':'Static file-size estimates; no browser loading-time measurement.'}
    (root/'docs/portfolio-performance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':
    check()
