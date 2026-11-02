#!/usr/bin/env python3
"""
Sync Verbatim Content from Live HTML Templates to PostgreSQL page_sections.
Ensures 100% exact match between salesleadmachine.co.uk templates and CMS database.
"""
import os, json, re
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import Json

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

HTML_MAP = {
    '': 'index.html',
    'terms-and-conditions': 'term_condition.html',
    'privacy-policy': 'privacy_policy.html',
    'technographics': 'technographics.html'
}

def clean_txt(t):
    if not t:
        return ''
    return re.sub(r'\s+', ' ', t).strip()

def extract_section_verbatim(sec_el, stype, current_data):
    d = dict(current_data) if current_data else {}
    
    # 1. ElementsKit Headings
    ekit_h = sec_el.find(class_='ekit-heading')
    if ekit_h:
        title_el = ekit_h.find(class_='ekit-heading--title') or ekit_h.find(class_='elementskit-section-title')
        sub_el = ekit_h.find(class_='ekit-heading--subtitle') or ekit_h.find(class_='elementskit-section-subtitle')
        desc_el = ekit_h.find(class_='ekit-heading__description')
        
        badge_span = title_el.find('span') if title_el else None
        
        if badge_span and sub_el:
            # Case A: badge span is red pill badge, sub_el is main headline
            d['eyebrow'] = clean_txt(badge_span.get_text())
            d['title'] = clean_txt(sub_el.get_text())
        elif sub_el and title_el:
            sub_t = clean_txt(sub_el.get_text())
            title_t = clean_txt(title_el.get_text())
            if len(sub_t) < 45 and not sub_t.endswith('.'):
                d['eyebrow'] = sub_t
                d['title'] = title_t
            else:
                d['title'] = title_t
                d['subtitle'] = sub_t
                d['description'] = sub_t
                d['body'] = sub_t
                d['body_html'] = sub_t
        elif title_el:
            d['title'] = clean_txt(title_el.get_text())
        elif sub_el:
            d['title'] = clean_txt(sub_el.get_text())
            
        if desc_el:
            p_tags = [clean_txt(p.get_text()) for p in desc_el.find_all('p') if clean_txt(p.get_text())]
            if p_tags:
                desc_text = ' '.join(p_tags)
                d['description'] = desc_text
                d['body'] = desc_text
                d['body_html'] = desc_text
                if 'subtitle' not in d:
                    d['subtitle'] = desc_text
    else:
        # Standard headings
        all_h = sec_el.find_all(['h1', 'h2', 'h3'])
        is_col_grid = stype == 'card_grid' and len(sec_el.find_all(class_='elementor-top-column')) >= 2 and not sec_el.find(class_='elementor-widget-heading', recursive=False)
        if all_h and not is_col_grid:
            d['title'] = clean_txt(all_h[0].get_text())
            
        # Text editor fallback
        txt_ed = sec_el.find(class_='elementor-widget-text-editor')
        if txt_ed:
            p_tags = [clean_txt(p.get_text()) for p in txt_ed.find_all('p') if clean_txt(p.get_text())]
            if p_tags:
                desc_text = ' '.join(p_tags)
                d['description'] = desc_text
                d['body'] = desc_text
                d['body_html'] = desc_text
                if 'subtitle' not in d:
                    d['subtitle'] = desc_text

    # 2. Buttons
    btns = sec_el.find_all('a', class_=lambda c: c and any(k in c for k in ['elementskit-btn', 'elementor-button', 'btn']))
    valid_btns = []
    for b in btns:
        bt = clean_txt(b.get_text())
        href = b.get('href', '')
        if bt and href and not href.startswith('#'):
            valid_btns.append({'label': bt, 'url': href})
    if valid_btns:
        d['buttons'] = [{'label': b['label'], 'url': b['url'], 'style': 'primary' if i==0 else 'outline'} for i, b in enumerate(valid_btns)]
        d['btn1_text'] = valid_btns[0]['label']
        d['btn1_url'] = valid_btns[0]['url']
        d['button_text'] = valid_btns[0]['label']
        d['button_url'] = valid_btns[0]['url']
        if len(valid_btns) > 1:
            d['cta_primary_text'] = valid_btns[1]['label']
            d['cta_primary_url'] = valid_btns[1]['url']
            d['cta_text'] = valid_btns[1]['label']
            d['cta_url'] = valid_btns[1]['url']
            d['cta_label'] = valid_btns[1]['label']
        else:
            d['cta_primary_text'] = valid_btns[0]['label']
            d['cta_primary_url'] = valid_btns[0]['url']
            d['cta_text'] = valid_btns[0]['label']
            d['cta_url'] = valid_btns[0]['url']
            d['cta_label'] = valid_btns[0]['label']

    # 3. Cards
    if stype == 'card_grid':
        iboxes = sec_el.find_all(class_='elementskit-infobox') or sec_el.find_all(class_='service-card')
        if iboxes:
            cards = []
            for ib in iboxes:
                ctitle = ib.find(class_='elementskit-info-box-title') or ib.find(class_='service-title') or ib.find(['h4', 'h5'])
                cdesc = ib.find(class_='box-body') or ib.find(class_='elementskit-box-description') or ib.find(class_='service-desc') or ib.find('p')
                cimg = ib.find('img')
                ca = ib.find('a')
                cards.append({
                    'title': clean_txt(ctitle.get_text()) if ctitle else '',
                    'description': clean_txt(cdesc.get_text()) if cdesc else '',
                    'image': cimg.get('src', '') if cimg else '',
                    'url': ca.get('href', '') if ca else ''
                })
            if cards:
                d['cards'] = cards
        else:
            cols = sec_el.find_all(class_='elementor-top-column')
            if len(cols) >= 2:
                cards = []
                for col in cols:
                    ctitle = col.find(class_='elementor-heading-title') or col.find(['h2', 'h3', 'h4'])
                    cdesc = col.find('.elementor-widget-text-editor p, p')
                    cimg = col.find('img')
                    ca = col.find('a')
                    cards.append({
                        'title': clean_txt(ctitle.get_text()) if ctitle else '',
                        'description': clean_txt(cdesc.get_text()) if cdesc else '',
                        'image': cimg.get('src', '') if cimg else '',
                        'url': ca.get('href', '') if ca else ''
                    })
                if cards:
                    d['cards'] = cards

    # 4. Bullets
    bullets = sec_el.find_all(class_='elementor-icon-list-item')
    if bullets:
        d['bullets'] = [{'text': clean_txt(b.get_text())} for b in bullets if clean_txt(b.get_text())]

    # 5. Counters
    ffs = sec_el.find_all(class_='elementskit-funfact')
    if ffs:
        counters = []
        for ff in ffs:
            num = ff.find(class_='number-percentage')
            unit = ff.find(class_='super')
            lbl = ff.find(class_='elementskit-funfact-title')
            counters.append({
                'value': clean_txt(num.get_text()) if num else '',
                'unit': clean_txt(unit.get_text()) if unit else '',
                'label': clean_txt(lbl.get_text()) if lbl else ''
            })
        if counters:
            d['counters'] = counters

    # 6. Logos
    if stype == 'logo_wall':
        logos = sec_el.find_all(class_='elementskit-client-slider-item') or sec_el.find_all(class_='single-client')
        if not logos:
            logos = sec_el.find_all(class_='simple_logo_image')
        if logos:
            logo_list = []
            for l in logos:
                img = l.find('img')
                a = l.find('a')
                if img:
                    logo_list.append({
                        'image_url': img.get('src', ''),
                        'name': img.get('alt', '') or 'Partner',
                        'url': a.get('href', '') if a else ''
                    })
            if logo_list:
                d['logos'] = logo_list

    # 7. Team
    if stype == 'team':
        members = sec_el.find_all(class_='sassico-team-style-2') or sec_el.find_all(class_='profile-card') or sec_el.find_all(class_='elementskit-team')
        if members:
            mem_list = []
            for m in members:
                name_el = m.find(class_='profile-title') or m.find(class_='ekit-team-modal-title')
                role_el = m.find(class_='profile-designation') or m.find(class_='ekit-team-modal-position')
                m_img = m.find('img')
                m_link = m.find('a', href=lambda h: h and 'linkedin.com' in h) or m.find('a', attrs={'aria-label': lambda a: a and 'link' in a.lower()})
                if name_el:
                    mem_list.append({
                        'name': clean_txt(name_el.get_text()),
                        'role': clean_txt(role_el.get_text()) if role_el else '',
                        'photo': m_img.get('src', '') if m_img else '',
                        'linkedin': m_link.get('href', '') if m_link else ''
                    })
            if mem_list:
                d['members'] = mem_list

    # Main image
    img = sec_el.find('img')
    if img and stype in ['hero', 'split']:
        d['image_url'] = img.get('src', '')
        d['dashboard_image'] = img.get('src', '')

    return d

def run_sync():
    conn = psycopg2.connect(dbname='salesleadmachine', user='liluzi')
    cur = conn.cursor()
    cur.execute('SELECT id, slug, full_path, title FROM pages ORDER BY slug')
    pages = cur.fetchall()

    updated_count = 0
    for p in pages:
        page_id, slug, full_path, title = p
        hf = HTML_MAP.get(slug, slug + '.html')
        hpath = os.path.join(DIR_PATH, hf)
        if not os.path.isfile(hpath):
            print(f'[SKIP] Missing HTML file for {slug}: {hf}')
            continue
            
        with open(hpath, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        cur.execute('SELECT id, section_type, sort_order, anchor_id, data FROM page_sections WHERE page_id = %s ORDER BY sort_order', (page_id,))
        secs = cur.fetchall()
        for s in secs:
            sid, stype, sorder, aid, sdata = s
            sec_el = soup.find(attrs={'data-id': aid}) or soup.find(id=aid) or soup.find(class_=f'elementor-element-{aid}')
            if not sec_el:
                print(f'[WARN] DOM element not found for {slug} sec {sorder} aid={aid}')
                continue
                
            new_data = extract_section_verbatim(sec_el, stype, sdata)
            
            cur.execute(
                'UPDATE page_sections SET data = %s, draft_data = %s WHERE id = %s',
                (Json(new_data), Json(new_data), sid)
            )
            updated_count += 1
            
    conn.commit()
    conn.close()
    print(f'Sync complete! Successfully updated {updated_count} sections in PostgreSQL database.')

if __name__ == '__main__':
    run_sync()

