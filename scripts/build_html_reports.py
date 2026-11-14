"""Build self-contained offline HTML reading views from the Markdown reports."""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    'report/BAO_CAO_DEMO.md': ('Báo cáo demo', 'Từ dữ liệu đến câu trả lời có bằng chứng'),
    'report/KICH_BAN_THUYET_TRINH.md': ('Kịch bản thuyết trình', 'Lời dẫn 8–10 phút và câu hỏi phản biện'),
    'report/individual/2A202603547_PhanTrongHau.md': ('Báo cáo kỹ thuật', 'Số liệu đầy đủ và đối chiếu từng câu test'),
}


def inline(text):
    snippets = []
    def code(match):
        snippets.append('<code>' + html.escape(match[1]) + '</code>')
        return f'\x00{len(snippets)-1}\x00'
    text = re.sub(r'`([^`]+)`', code, text)
    text = html.escape(text)
    def link(match):
        label, target = match.groups()
        # Convert links only when a generated HTML counterpart exists.
        for source in PAGES:
            name = Path(source).name
            if target.endswith(name):
                target = target[:-3] + '.html'
                break
        return f'<a href="{target}">{label}</a>'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    for i, snippet in enumerate(snippets):
        text = text.replace(f'\x00{i}\x00', snippet)
    return text


def diagram():
    # Native HTML flow diagram: readable offline, no Mermaid CDN or network needed.
    return '''<figure class="pipeline"><figcaption>Luồng xử lý một câu hỏi</figcaption>
    <div class="flow-step"><b>01</b><div><strong>Câu hỏi và filter</strong><span>Chỉ nhận điều kiện người dùng nêu rõ</span></div></div>
    <div class="flow-step"><b>02</b><div><strong>Qwen gọi search_documents</strong><span>Model tạo query để tìm bằng chứng</span></div></div>
    <div class="branches"><div>Dense<span>Qdrant · vector Day 6</span></div><div>BM25<span>Tìm theo từ khóa</span></div><div>Hybrid RRF<span>Kết hợp thứ hạng</span></div></div>
    <p class="flow-note">Tool sử dụng một trong ba phương pháp theo cấu hình thí nghiệm.</p>
    <div class="flow-step"><b>03</b><div><strong>Chọn context</strong><span>Chunk nguyên vẹn · loại trùng · giữ ID, nguồn, trang · giới hạn ký tự</span></div></div>
    <div class="flow-step"><b>04</b><div><strong>Model trả lời hoặc từ chối</strong><span>Citation cho câu trả lời · ABSTAIN khi thiếu bằng chứng</span></div></div>
    <div class="flow-step"><b>05</b><div><strong>Kiểm tra và lưu trace</strong><span>Kiểm tra giao thức và citation ID, sau đó đọc đối chiếu nguồn</span></div></div></figure>'''


def render_markdown(source):
    lines, output, toc = source.splitlines(), [], []
    i, section, heading = 0, False, 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith('# '):
            i += 1
            continue
        if line.startswith('**Phan Trọng Hậu ·'):
            # Author identity is already rendered in the shared page header.
            i += 1
            continue
        if line.startswith('```'):
            language = line[3:]
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith('```'):
                code.append(lines[i]); i += 1
            if language == 'mermaid':
                output.append(diagram())
            else:
                output.append('<div class="code-block"><div class="code-label">' + html.escape(language or 'Lệnh') +
                              '<button type="button" class="copy">Sao chép</button></div><pre><code>' +
                              html.escape('\n'.join(code)) + '</code></pre></div>')
            i += 1
            continue
        match = re.match(r'^(#{2,3}) (.+)', line)
        if match:
            level, title = len(match[1]), match[2]
            heading += 1
            anchor = f'muc-{heading}'
            if level == 2:
                if section:
                    output.append('</section>')
                output.append('<section class="report-section">')
                section = True
            toc.append((level, anchor, title))
            output.append(f'<h{level} id="{anchor}">{inline(title)}</h{level}>')
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                row = lines[i].strip().strip('|')
                rows.append(re.split(r'(?<!\\)\|', row)); i += 1
            output.append('<div class="table-wrap" tabindex="0" role="region" aria-label="Bảng số liệu"><table>')
            for n, row in enumerate(rows):
                if n == 1 and all(re.fullmatch(r'\s*:?-+:?\s*', x) for x in row):
                    continue
                if n == 0:
                    output.append('<thead><tr>' + ''.join('<th scope="col">' + inline(x.strip()) + '</th>' for x in row) + '</tr></thead><tbody>')
                else:
                    output.append('<tr>' + ''.join('<td>' + inline(x.strip().replace('\\|', '|')) + '</td>' for x in row) + '</tr>')
            output.append('</tbody></table></div>')
            continue
        if line.startswith('>'):
            quote = []
            while i < len(lines) and lines[i].startswith('>'):
                quote.append(lines[i].lstrip('> ').strip()); i += 1
            output.append('<blockquote>' + ''.join('<p>' + inline(p) + '</p>' for p in '\n'.join(quote).split('\n\n') if p) + '</blockquote>')
            continue
        if re.match(r'^(- |\d+\. )', line):
            ordered = bool(re.match(r'^\d', line))
            tag = 'ol' if ordered else 'ul'
            output.append(f'<{tag}>')
            while i < len(lines) and re.match(r'^(\d+\. )' if ordered else r'^- ', lines[i]):
                output.append('<li>' + inline(re.sub(r'^(?:- |\d+\. )', '', lines[i])) + '</li>'); i += 1
            output.append(f'</{tag}>')
            continue
        paragraph = []
        while i < len(lines) and lines[i].strip() and not re.match(r'^(?:#|```|\||>|- |\d+\. )', lines[i]):
            paragraph.append(inline(lines[i].strip()) + ('<br>' if lines[i].endswith('  ') else ' ')); i += 1
        output.append('<p>' + ''.join(paragraph).strip() + '</p>')
    if section:
        output.append('</section>')
    return '\n'.join(output), toc


CSS = '''
:root{--ink:#182b3b;--muted:#617385;--accent:#087f78;--border:#dce5ea;--paper:#fff;--bg:#f3f6f8}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:95px}body{margin:0;color:var(--ink);background:var(--bg);font:16px/1.8 system-ui,-apple-system,"Segoe UI",sans-serif}a{color:var(--accent);text-underline-offset:4px}button{font:inherit;cursor:pointer}a:focus-visible,button:focus-visible,[tabindex]:focus-visible{outline:3px solid #da9d30;outline-offset:4px}.skip{position:absolute;left:16px;top:-80px;background:white;padding:10px;z-index:99}.skip:focus{top:10px}
.topbar{position:sticky;top:0;z-index:10;background:#ffffffed;backdrop-filter:blur(12px);border-bottom:1px solid var(--border)}.topbar-inner{max-width:1460px;margin:auto;min-height:70px;display:flex;align-items:center;justify-content:space-between;padding:10px 32px;gap:20px}.brand{font-weight:800;letter-spacing:-.4px;text-decoration:none;color:var(--ink);white-space:nowrap}.brand span{color:var(--accent)}.tabs{display:flex;gap:8px;flex-wrap:wrap}.tabs a{color:var(--muted);font-size:14px;text-decoration:none;padding:7px 12px;border-radius:8px}.tabs a[aria-current="page"]{background:#e6f3f0;color:#076e66;font-weight:700}.actions{display:flex;gap:8px}.actions button{border:1px solid var(--border);background:#fff;border-radius:8px;padding:6px 12px;font-size:13px;white-space:nowrap}
.layout{max-width:1460px;margin:0 auto;display:grid;grid-template-columns:250px minmax(0,1fr);gap:40px;padding:38px 32px 80px}aside{position:sticky;top:104px;align-self:start;max-height:calc(100vh - 125px);overflow:auto;padding-right:12px}.eyebrow{font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:800;color:var(--muted);margin-bottom:14px}.toc a{display:block;font-size:13px;line-height:1.6;text-decoration:none;color:var(--muted);padding:8px 12px;border-left:2px solid transparent}.toc a.sub{font-size:12px;padding:5px 12px 5px 24px}.toc a:hover,.toc a.active{color:var(--accent);background:#e7efef;border-left-color:var(--accent)}.aside-note{font-size:12px;color:var(--muted);margin:22px 12px}
main{min-width:0}.hero{padding:4px 0 28px}.hero .eyebrow{color:var(--accent)}h1{font-size:clamp(32px,3.8vw,48px);line-height:1.18;letter-spacing:-1.6px;margin:12px 0 14px}.subtitle{font-size:19px;color:var(--muted);margin:0 0 18px}.identity{font-size:14px;color:var(--muted)}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0 8px}.stat{padding:17px 19px;border:1px solid var(--border);border-radius:12px;background:white}.stat b{display:block;font-size:27px;line-height:1.4;letter-spacing:-.7px}.stat span{display:block;font-size:12px;line-height:1.5;color:var(--muted)}.stat.warning{background:#fff8eb;border-color:#ecd4a0}.stat.warning b{color:#94600c}.report-section{background:var(--paper);border:1px solid var(--border);border-radius:14px;padding:30px 36px;margin:0 0 24px}h2{font-size:24px;line-height:1.4;letter-spacing:-.5px;margin:0 0 22px}h3{font-size:18px;line-height:1.5;margin:32px 0 13px}p{margin:0 0 18px}li{margin-bottom:9px}strong{font-weight:700}main>p{color:var(--muted);font-size:14px}blockquote{border-left:3px solid var(--accent);margin:18px 0;padding:4px 0 4px 22px;color:#344e5f}blockquote p:last-child{margin:0}
.table-wrap{overflow:auto;margin:22px 0 25px;border:1px solid var(--border);border-radius:9px}table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.6}th{background:#edf3f6;color:#294558;font-weight:700;text-align:left;white-space:normal}th,td{padding:13px 15px;border-bottom:1px solid var(--border);vertical-align:top;min-width:80px}th:first-child,td:first-child{min-width:145px}tr:last-child td{border-bottom:0}tbody tr:nth-child(even){background:#fafcfd}tbody tr:hover{background:#edf7f4}td strong{color:#087167}code{font: .87em/1.7 ui-monospace,"DejaVu Sans Mono",monospace;background:#eef2f5;border-radius:4px;padding:2px 5px;overflow-wrap:anywhere}.code-block{margin:22px 0;border-radius:10px;background:#152c3a;color:#dfeff2;overflow:hidden}.code-label{display:flex;align-items:center;justify-content:space-between;padding:9px 16px;color:#a8c8ce;font:12px system-ui;border-bottom:1px solid #ffffff19;text-transform:uppercase}.copy{border:1px solid #ffffff38;background:transparent;color:#e7f6f7;border-radius:5px;padding:4px 9px;font-size:12px;text-transform:none}pre{padding:17px;margin:0;overflow:auto;white-space:pre-wrap;word-break:break-word}pre code{background:transparent;color:inherit;padding:0}
.pipeline{margin:25px 0;padding:24px;background:#f6faf9;border:1px solid #dceae5;border-radius:12px}.pipeline figcaption{font-size:12px;letter-spacing:1px;text-transform:uppercase;color:var(--accent);font-weight:800;margin-bottom:20px}.flow-step{display:flex;gap:16px;align-items:flex-start;margin:16px 0}.flow-step>b{color:var(--accent);font-size:12px;border:1px solid #badbd3;border-radius:50%;width:30px;height:30px;display:grid;place-items:center;flex-shrink:0}.flow-step strong{display:block;font-size:15px}.flow-step span,.branches span{display:block;font-size:12px;color:var(--muted)}.branches{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:8px 0 8px 46px}.branches>div{background:white;border:1px solid #cfe1dc;border-radius:8px;padding:12px;font-size:14px;font-weight:700}.flow-note{font-size:12px;color:var(--muted);margin:0 0 18px 46px}footer{font-size:12px;color:var(--muted);margin:28px 0;text-align:center}.reading-progress{position:fixed;top:0;left:0;width:0;height:3px;background:var(--accent);z-index:20}.focus .layout{grid-template-columns:minmax(0,980px);justify-content:center}.focus aside{display:none}.focus .report-section{font-size:18px}.focus .tabs{display:none}
@media(max-width:1100px){.layout{grid-template-columns:210px minmax(0,1fr);gap:22px;padding:25px 20px}.topbar-inner{padding:10px 20px}.brand{font-size:14px}.tabs a{font-size:12px;padding:6px 8px}.report-section{padding:25px}.actions button{font-size:12px}}@media(max-width:800px){.layout{display:block;padding:24px 16px}.topbar-inner{flex-wrap:wrap;gap:8px;padding:10px 16px}.tabs{order:3;width:100%}aside{position:static;max-height:210px;margin-bottom:25px;border-bottom:1px solid var(--border);padding-bottom:15px}.report-section{padding:22px 18px}h2{font-size:21px}.stats{grid-template-columns:repeat(2,1fr)}.branches{padding-left:0;grid-template-columns:1fr}.flow-note{margin-left:0}.subtitle{font-size:17px}h1{letter-spacing:-1px}html{scroll-padding-top:130px}}
@media print{@page{size:A4;margin:17mm}body{background:white;font-size:10pt;color:black}.topbar,aside,.actions,.copy,.reading-progress,.skip{display:none!important}.layout,.focus .layout{display:block;padding:0;max-width:none}.hero{padding:0 0 15px}h1{font-size:28pt}h2{font-size:17pt;break-after:avoid}h3{break-after:avoid;font-size:12pt}.report-section,.focus .report-section{border:0;border-radius:0;padding:0;margin:24px 0;font-size:10pt}.stats{gap:8px}.stat{padding:10px}table{font-size:8pt}.table-wrap{overflow:visible}tr,blockquote,.flow-step{break-inside:avoid}thead{display:table-header-group}th,td{padding:7px;min-width:0!important}pre{white-space:pre-wrap}.code-block{background:#f3f5f6;color:black;border:1px solid #ccc;break-inside:avoid}.code-label{color:black}.table-wrap{border:0}.pipeline{break-inside:avoid}a{color:inherit;text-decoration:none}.stats,.branches{break-inside:avoid}footer{margin-top:20px}}
'''

JS = '''
document.querySelector('#print').addEventListener('click',()=>window.print());
document.querySelector('#focus').addEventListener('click',e=>{const on=document.body.classList.toggle('focus');e.currentTarget.textContent=on?'Thoát tập trung':'Tập trung';e.currentTarget.setAttribute('aria-pressed',String(on))});
document.querySelectorAll('.copy').forEach(button=>button.addEventListener('click',async()=>{const text=button.closest('.code-block').querySelector('pre').textContent;try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(text)}else{const t=document.createElement('textarea');t.value=text;t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();if(!document.execCommand('copy'))throw Error();t.remove()}button.textContent='Đã sao chép'}catch(e){button.textContent='Chọn lệnh để sao chép'}setTimeout(()=>button.textContent='Sao chép',2000)}));
const links=[...document.querySelectorAll('.toc a')];const headings=links.map(a=>document.getElementById(a.hash.slice(1)));
function update(){const max=document.documentElement.scrollHeight-innerHeight;document.querySelector('.reading-progress').style.width=(max>0?scrollY/max*100:0)+'%';let index=0;headings.forEach((h,i)=>{if(h.getBoundingClientRect().top<160)index=i});links.forEach((a,i)=>{a.classList.toggle('active',i===index);if(i===index)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current')})}
window.addEventListener('scroll',update,{passive:true});window.addEventListener('resize',update);update();
'''


def main():
    for filename, (title, subtitle) in PAGES.items():
        path = ROOT / filename
        content, toc = render_markdown(path.read_text(encoding='utf-8'))
        nav = []
        for name, (label, _) in PAGES.items():
            target = ROOT / name
            import os
            href = os.path.relpath(target.with_suffix('.html'), path.parent)
            nav.append(f'<a href="{href}"' + (' aria-current="page"' if name == filename else '') + '>' + label + '</a>')
        toc_html = ''.join(f'<a href="#{anchor}" class="{"sub" if level == 3 else ""}">{html.escape(label)}</a>' for level, anchor, label in toc)
        page = f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>{title} · Agentic RAG Day 7</title><style>{CSS}</style></head><body>
<a class="skip" href="#content">Đến nội dung chính</a><div class="reading-progress" aria-hidden="true"></div>
<header class="topbar"><div class="topbar-inner"><a class="brand" href="{nav[0].split('href="')[1].split('"')[0]}">DAY 07 <span>/</span> AGENTIC RAG</a><nav class="tabs" aria-label="Tài liệu">{''.join(nav)}</nav><div class="actions"><button id="focus" aria-pressed="false" type="button">Tập trung</button><button id="print" type="button">In / Lưu PDF</button></div></div></header>
<div class="layout"><aside><div class="eyebrow">Trong tài liệu này</div><nav class="toc" aria-label="Mục lục">{toc_html}</nav><p class="aside-note">Bản HTML đọc offline.<br>Số liệu từ trace benchmark đã lưu.<br>Nhãn có AI hỗ trợ đối chiếu.</p></aside>
<main id="content"><div class="hero"><div class="eyebrow">Retrieval and context engineering</div><h1>{title}<br>Agentic RAG Day 7</h1><p class="subtitle">{subtitle}</p><div class="identity">Phan Trọng Hậu &nbsp;·&nbsp; 2A202603547 &nbsp;·&nbsp; L3A</div><div class="stats"><div class="stat"><b>192</b><span>chunk từ Day 6</span></div><div class="stat"><b>24</b><span>câu dev và test</span></div><div class="stat"><b>5/5</b><span>câu test có đáp án đạt grade 2<br>Cấu hình lexical</span></div><div class="stat warning"><b>2 lỗi</b><span>ở câu test thiếu bằng chứng<br>Chưa gọi retrieval</span></div></div></div>
{content}<footer>Phan Trọng Hậu · Day 7 · Báo cáo, trace và giới hạn của kết quả được giữ nguyên.</footer></main></div><script>{JS}</script></body></html>'''
        path.with_suffix('.html').write_text(page, encoding='utf-8')
        print(path.with_suffix('.html').relative_to(ROOT))


if __name__ == '__main__':
    main()
