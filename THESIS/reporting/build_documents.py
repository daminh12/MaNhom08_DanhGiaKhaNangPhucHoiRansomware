"""Build editable Group08 Word/PPTX from reviewed Markdown and pinned evidence.

Requires python-docx, python-pptx, matplotlib. Never calls Docker or edits evidence.
Run from any cwd: python THESIS/reporting/build_documents.py
"""
import csv
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from docx import Document
from docx.shared import Cm, Pt as WPt, RGBColor as WColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parents[2]
THESIS = ROOT / 'THESIS'
ASSETS = THESIS / 'assets'
INK, TEAL, AMBER, MUTED, BG = '14263F', '007F82', 'B56D00', '526477', 'F3F6FA'
FONT = 'Arial'


def load_metrics():
    rows = list(csv.DictReader((ROOT/'docs/evidence/phase5/export-20261110/metrics.csv').open(encoding='utf-8-sig')))
    main = next(r for r in rows if r['scenario'] == 'drill')
    assert main['trial_status']=='PASS' and main['rto_target_result']=='NOT TESTED'
    assert main['exact_rpo_seconds']=='' and len(rows)==4
    return main


def figures():
    ASSETS.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    fig, ax = plt.subplots(figsize=(11.2, 4.4));fig.patch.set_facecolor('#F3F6FA')
    ax.set(xlim=(0,11.2),ylim=(0,4.4));ax.axis('off')
    boxes=[(.25,2.6,2.45,1.2,'NGUỒN • group08-lab\nFlask → MySQL orders',INK),
           (3.5,2.6,3.0,1.2,'DUMP + BASELINE\nSQL / metadata / SHA-256',TEAL),
           (7.45,2.6,3.25,1.2,'RESTIC SNAPSHOT\nfull ID + trusted digest',INK),
           (7.45,.35,3.25,1.2,'TARGET SẠCH\nproject / network / volume mới',TEAL)]
    for x,y,w,h,t,c in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08',facecolor='#'+c,edgecolor='none'))
        ax.text(x+w/2,y+h/2,t,color='white',ha='center',va='center',fontsize=14)
    for start,end in [((2.85,3.2),(3.35,3.2)),((6.65,3.2),(7.25,3.2)),((9.05,2.4),(9.05,1.75))]:
        ax.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'->','lw':2,'color':'#'+MUTED})
    ax.text(.2,1.2,'Sơ đồ thiết kế, không phải ảnh chụp lab.\nKho và secret vẫn cùng host.\nTarget không mount volume DB nguồn; không seed.',color='#'+MUTED,fontsize=13,va='center')
    fig.savefig(ASSETS/'architecture.png',dpi=160,bbox_inches='tight',facecolor=fig.get_facecolor());plt.close(fig)
    events=[json.loads(s) for s in (ROOT/'docs/evidence/phase4/main-events.jsonl').read_text().splitlines()]
    one=lambda name:next(e for e in events if e['event']==name)
    t0=one('FAULT_REQUESTED')['monotonic_ns']
    stages=[('FAULT_REQUESTED','ARTIFACT_VERIFIED','Dừng nguồn + xác minh artifact',INK),
            ('ARTIFACT_VERIFIED','TARGET_READY','Dựng DB target sạch',TEAL),
            ('TARGET_READY','DATA_VERIFIED','Import + quyền + toàn bảng','3A8EAE'),
            ('DATA_VERIFIED','SERVICE_VERIFIED','API + probe + restart + ổn định','A16B14')]
    fig,ax=plt.subplots(figsize=(11.2,4.1));fig.patch.set_facecolor('white')
    labels=[]
    for i,(start,end,label,color) in enumerate(stages):
        left=(one(start)['monotonic_ns']-t0)/1e9;right=(one(end)['monotonic_ns']-t0)/1e9
        ax.barh(3-i,right-left,left=left,height=.57,color='#'+color)
        ax.text(right+.3,3-i,format(right-left,'.2f')+' s',va='center',color='#'+INK,fontsize=9)
        labels.append(label)
    ax.set(yticks=[3,2,1,0],yticklabels=labels,xlabel='Giây từ FAULT_REQUESTED (monotonic observer)',xlim=(0,59),ylim=(-.6,3.7))
    for side in ['left','top','right']:ax.spines[side].set_visible(False)
    ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    elapsed=one('SERVICE_VERIFIED')['monotonic_ns']-t0
    rto_text=f'{elapsed//1_000_000_000}.{elapsed%1_000_000_000:09d}'
    assert rto_text==load_metrics()['observed_rto_seconds']
    ax.set_title('Một main trial Linux • Tready = '+rto_text+' s',loc='left',color='#'+INK,fontweight='bold',pad=14)
    fig.text(.08,.01,'Các khoảng liên tiếp gồm thời gian điều phối giữa mốc. Đối chiếu ACK hoàn tất sau Tready; return-source ngoài RTO.',fontsize=8,color='#'+MUTED)
    fig.tight_layout(rect=(0,.05,1,1));fig.savefig(ASSETS/'recovery_timeline.png',dpi=160,bbox_inches='tight');plt.close(fig)


def clean(text):
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 (\2)',text)
    return text.replace('**','').replace('`','')


def setup_doc():
    d=Document();sec=d.sections[0]
    sec.page_height=Cm(29.7);sec.page_width=Cm(21)
    sec.top_margin=Cm(1.8);sec.bottom_margin=Cm(1.8);sec.left_margin=Cm(2);sec.right_margin=Cm(2)
    normal=d.styles['Normal'];normal.font.name=FONT;normal.font.size=WPt(10.5)
    normal.paragraph_format.space_after=WPt(4);normal.paragraph_format.line_spacing=1.07
    for name,size in [('Title',25),('Heading 1',20),('Heading 2',14),('Heading 3',12)]:
        d.styles[name].font.name=FONT;d.styles[name].font.size=WPt(size);d.styles[name].font.color.rgb=WColor.from_string(INK)
    for s in ['List Bullet','List Number']:d.styles[s].font.name=FONT;d.styles[s].font.size=WPt(10.5)
    sec.header.paragraphs[0].text='NHÓM 08  |  AN TOÀN THÔNG TIN  |  HỒ SƠ REVIEW 15/11/2026'
    sec.header.paragraphs[0].style='Caption'
    footer=sec.footer.paragraphs[0];footer.text='Bằng chứng Linux; Windows chưa nghiệm thu  •  '
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    for r in footer.runs:r.font.size=WPt(8)
    d.core_properties.author='Nhóm 08 — Đa Minh, Minh Quân'
    d.core_properties.subject='Mô phỏng lành tính; kết quả có giới hạn; chờ nghiệm thu Windows'
    return d


def doc_from_md(md,output,title,subtitle,cover=True):
    d=setup_doc()
    if cover:
        d.add_paragraph('HỌC PHẦN AN TOÀN THÔNG TIN',style='Subtitle')
        d.add_paragraph(title,style='Title')
        d.add_paragraph(subtitle,style='Subtitle')
        d.add_paragraph('Nhóm 08 • Đa Minh và Minh Quân')
        d.add_paragraph('Thời gian dự án: 6 tuần • Tổng hợp ngày 15/11/2026')
        d.add_paragraph('Trạng thái: hồ sơ kỹ thuật để review; chưa nghiệm thu toàn bộ dự án.',style='Heading 2')
        d.add_paragraph('Kết quả Linux được giữ đúng nguồn. Windows 10, mục tiêu RTO/RPO và lượt thực thi độc lập của thành viên chỉ được PASS khi có bằng chứng riêng.')
        d.add_paragraph('Tài liệu này không có chữ ký nghiệm thu hoặc thông tin trường, lớp, MSSV, giảng viên chưa được nhóm cung cấp.')
    lines=md.splitlines();i=0;code=False;paragraph=[]
    if output.name=='BaoCao_Nhom08.docx':
        p=d.add_heading('Nội dung báo cáo',level=1);p.paragraph_format.page_break_before=True
        for line in lines:
            if line.startswith('## '):d.add_paragraph(clean(line[3:]),style='List Bullet')
        i=next(n for n,line in enumerate(lines) if line.startswith('## '))
    def flush():
        if paragraph:d.add_paragraph(clean(' '.join(paragraph)));paragraph.clear()
    while i<len(lines):
        line=lines[i];i+=1
        if line.startswith('```'):
            flush();code=not code;continue
        if code:
            p=d.add_paragraph();p.paragraph_format.space_after=WPt(0)
            r=p.add_run(line);r.font.name='Consolas';r.font.size=WPt(8)
            continue
        if not line.strip():flush();continue
        if line.startswith('# '):flush();continue
        if line.startswith('## '):
            flush();p=d.add_heading(clean(line[3:]),level=1);p.paragraph_format.page_break_before=True;continue
        if line.startswith('### '):flush();d.add_heading(clean(line[4:]),level=2);continue
        if line.startswith('#### '):flush();d.add_heading(clean(line[5:]),level=3);continue
        if line.startswith('|'):
            flush();tablelines=[line]
            while i<len(lines) and lines[i].startswith('|'):tablelines.append(lines[i]);i+=1
            data=[[clean(c.strip()) for c in row.strip().strip('|').split('|')] for row in tablelines]
            data=[row for row in data if not all(re.fullmatch(r':?-+:?',c.replace(' ','')) for c in row)]
            t=d.add_table(rows=1,cols=len(data[0]));t.style='Light Shading Accent 1'
            repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
            for j,c in enumerate(data[0]):t.rows[0].cells[j].text=c
            for row in data[1:]:
                cells=t.add_row().cells
                for j,c in enumerate(row[:len(cells)]):cells[j].text=c
            for idx,row in enumerate(t.rows):
                row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
                for c in row.cells:
                    for p in c.paragraphs:
                        p.paragraph_format.space_after=WPt(4)
                        for r in p.runs:r.font.size=WPt(8.5 if len(data[0])>=4 else 9)
                if idx==0:
                    for c in row.cells:
                        shade=OxmlElement('w:shd');shade.set(qn('w:fill'),INK);c._tc.get_or_add_tcPr().append(shade)
                        for r in c.paragraphs[0].runs:r.font.color.rgb=WColor(255,255,255);r.bold=True
            d.add_paragraph();continue
        image=re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)',line)
        if image:
            flush();d.add_picture(str(THESIS/image[2]),width=Cm(16.5));d.add_paragraph(image[1],style='Caption');continue
        if line.startswith('- '):flush();d.add_paragraph(clean(line[2:]),style='List Bullet');continue
        numbered=re.match(r'^\d+\.\s+(.*)',line)
        if numbered:flush();d.add_paragraph(clean(numbered[1]),style='List Number');continue
        if line.startswith('> '):flush();d.add_paragraph(clean(line[2:]),style='Subtitle');continue
        paragraph.append(line)
    flush();d.save(output)


def rgb(h):return RGBColor.from_string(h)


def textbox(s,x,y,w,h,text,size=21,color=INK,bold=False,space=12):
    box=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=box.text_frame;tf.word_wrap=True
    for i,line in enumerate(text.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line
        p.font.name=FONT;p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=rgb(color)
        p.space_after=Pt(space)
    return box


def card(s,x,y,w,h,title,body,color=TEAL):
    shape=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
    shape.fill.solid();shape.fill.fore_color.rgb=rgb('FFFFFF');shape.line.color.rgb=rgb('DCE4ED')
    textbox(s,x+.2,y+.18,w-.4,1,title,size=22,color=color,bold=True,space=0)
    textbox(s,x+.2,y+1.3,w-.4,h-1.45,body,size=18,space=4)


def build_slides(main):
    prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
    spec=json.loads((THESIS/'reporting/slides.json').read_text(encoding='utf-8'))
    values={'RTO':main['observed_rto_seconds'],'MTTD':main['observed_mttd_seconds'],
            'LOWER':main['recovered_commit_lag_lower_seconds'],'UPPER':main['recovered_commit_lag_upper_seconds']}
    md=['# Thuyết trình Nhóm 08','']
    for idx,item in enumerate(spec,1):
        item=json.loads(json.dumps(item,ensure_ascii=False))
        for k,v in values.items():item=json.loads(json.dumps(item,ensure_ascii=False).replace('{'+k+'}',v))
        s=prs.slides.add_slide(prs.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=rgb(BG)
        strip=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,prs.slide_width,Inches(.11));strip.fill.solid();strip.fill.fore_color.rgb=rgb(TEAL);strip.line.fill.background()
        textbox(s,.55,.34,12.2,.85,item['title'],size=30,bold=True)
        textbox(s,.58,1.22,12.1,.65,item.get('subtitle',''),size=16,color=MUTED)
        kind=item.get('kind','cards')
        if kind=='figure':
            from PIL import Image
            with Image.open(ASSETS/item['image']) as im:aspect=im.width/im.height
            h=min(3.85,12.1/aspect);w=h*aspect
            s.shapes.add_picture(str(ASSETS/item['image']),Inches((13.333-w)/2),Inches(2.05),width=Inches(w),height=Inches(h))
        elif kind=='cover':
            textbox(s,.65,2,11.9,2,item['body'],size=32,bold=True)
            textbox(s,.7,4.35,11.8,1.4,item['detail'],size=22,color=TEAL)
        elif kind=='architecture':
            cards=item['cards'];positions=[(.6,2.1,2.6,3.65),(3.7,2.1,2.6,3.65),(6.8,2.1,2.6,3.65),(9.9,2.1,2.8,3.65)]
            for c,pos in zip(cards,positions):card(s,*pos,c['title'],c['body'])
            for x in [3.2,6.3,9.4]:textbox(s,x,3.2,.5,.7,'→',size=26,color=TEAL)
        else:
            cards=item['cards'];n=len(cards)
            if n<=3:
                w=(12.1-(n-1)*.3)/n
                for j,c in enumerate(cards):card(s,.6+j*(w+.3),2.05,w,3.9,c['title'],c['body'],c.get('color',TEAL))
            else:
                for j,c in enumerate(cards):card(s,.6+(j%2)*6.2,1.98+(j//2)*2.05,5.9,1.9,c['title'],c['body'],c.get('color',TEAL))
        if item.get('callout'):textbox(s,.65,6.15,12.05,.65,item['callout'],size=15,color=item.get('callout_color',MUTED))
        textbox(s,.6,7.05,11.7,.3,'NHÓM 08 • AN TOÀN THÔNG TIN  |  Linux evidence • Windows NOT TESTED',size=10,color=MUTED)
        textbox(s,12.3,7.05,.5,.3,f'{idx:02}',size=11,color=TEAL,bold=True)
        s.notes_slide.notes_text_frame.text=item.get('notes','')+'\nNguồn: '+item.get('source','BAO_CAO_CAC_PHASE.md')
        md+=['## '+str(idx)+'. '+item['title'],item.get('subtitle',''),'']
        if 'body' in item:md += [item['body'],item.get('detail','')]
        for c in item.get('cards',[]):md+=['- '+c['title']+': '+c['body'].replace('\n','; ')]
        if item.get('image'):md+=['![Timeline thực nghiệm](assets/'+item['image']+')']
        md+=['',item.get('callout',''),'','Ghi chú thuyết trình: '+item.get('notes',''),'Nguồn: '+item.get('source','BAO_CAO_CAC_PHASE.md'),'']
    prs.core_properties.author='Nhóm 08 — Đa Minh, Minh Quân'
    prs.core_properties.title='Đánh giá khả năng phục hồi bằng mô phỏng an toàn'
    prs.save(THESIS/'ThuyetTrinh_Nhom08.pptx')
    (THESIS/'SLIDES_GROUP08.md').write_text('\n'.join(md),encoding='utf-8')


def main():
    main=load_metrics();figures()
    report=(THESIS/'REPORT_GROUP08.md').read_text(encoding='utf-8')
    if re.search(r'\{(?:FINAL_UNIT_TOTAL|RECOVERY_TESTS)\}',report):raise ValueError('Review counts must be resolved before build')
    doc_from_md(report,THESIS/'BaoCao_Nhom08.docx','ĐÁNH GIÁ KHẢ NĂNG PHỤC HỒI TRƯỚC SỰ CỐ MÃ HÓA TỐNG TIỀN','Báo cáo kỹ thuật • Mô phỏng an toàn trên lab Docker')
    build_slides(main)
    print(json.dumps({'status':'BUILT','docx':'THESIS/BaoCao_Nhom08.docx','pptx':'THESIS/ThuyetTrinh_Nhom08.pptx'},ensure_ascii=False))


if __name__=='__main__':main()
