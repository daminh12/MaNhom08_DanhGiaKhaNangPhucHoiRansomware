"""Build practical guide artifacts, without replacing historical results/reports."""
import json
from docx import Document
from pptx import Presentation
from pptx.util import Inches
from build_documents import ROOT, THESIS, doc_from_md, textbox, card, INK, TEAL, MUTED


def main():
    source=ROOT/'HUONGDAN.md'
    target=THESIS/'runbook/HuongDan_ThucNghiem.docx'
    doc_from_md(source.read_text(encoding='utf-8'),target,'HƯỚNG DẪN THỰC NGHIỆM',
                'Đa Minh kích hoạt • Minh Quân phục hồi • Chờ thực hành Windows 10')
    doc=Document(target)
    for section in doc.sections:
        section.header.paragraphs[0].text='NHÓM 08 | HƯỚNG DẪN THỰC HÀNH WINDOWS | 16/11/2026'
        section.footer.paragraphs[0].text='Windows/hai người thực hành: NOT TESTED | Tài liệu không thay bằng chứng'
    doc.core_properties.subject='Kế hoạch thực hành Windows; chưa có kết quả Windows được nghiệm thu'
    doc.save(target)
    slides=[
        ('Thực hành đúng yêu cầu của nhóm 08',
         [('Phạm vi','Dừng DB nguồn → phục hồi snapshot vào stack sạch → URL phục vụ trở lại.'),
          ('Vai trò','Đa Minh: chuẩn bị, INJECT, quan sát.\nMinh Quân: đọc runbook, RECOVER, WEB_OK.'),
          ('Trạng thái','Có mã và kiểm thử mock.\nWindows, hai người thực hành và video: NOT TESTED.')]),
        ('1. Chuẩn bị và mở hồ sơ',
         [('Công cụ','Windows 10, Docker Linux containers, Compose v2, Git, Python 3.10+, PowerShell, OBS.'),
          ('Ghi nhận','Đúng branch/commit. Mở session transcript. Ghi OS/tool versions, người thao tác và runbook version.'),
          ('Điều kiện','Nguồn healthy; đủ host/Docker disk; không writer hoặc backup khác; giữ secret gốc.')]),
        ('2. Nghiệm thu phục hồi sạch trước diễn tập',
         [('Backup','Baseline nhất quán; full snapshot ID; manifest SHA-256; Restic check/readback.'),
          ('Restore','Project/network/volume mới; không seed/mount nguồn; import exit 0; cấp quyền app.'),
          ('Xác minh','Schema + toàn bảng; API đọc trước probe; restart; cleanup và return-source PASS.')]),
        ('3. Bàn giao theo runbook',
         [('INJECT','Đa Minh xác nhận. Observer ghi T0 rồi dừng DB, xác nhận 503.'),
          ('RECOVER','Minh Quân làm theo tài liệu. Thời gian đọc/thao tác nằm trong RTO.'),
          ('WEB_OK','Mở URL và lưu ảnh trước xác nhận. Chốt sau đối chiếu ACK, kiểm lại dữ liệu và stable health.')]),
        ('4. Xuất số liệu của đúng lượt',
         [('Lượt mới','export_metrics.py --trial-dir\nGiữ raw events/result/ACK và evidence-manifest. Không --trial-dir là corpus cũ.'),
          ('Phân biệt','RTO, backup age, bounds send/ACK, số đơn chưa phục hồi, duplicate và uncertain.'),
          ('Giới hạn','Chưa có exact RPO hoặc target. FAIL/ABORTED không gán 0; không trộn guided-v2 với automated-v1.')]),
        ('5. Ghi lỗi, cải tiến và chạy lại',
         [('Windows v1.0','Đóng băng trước lượt đầu; Đa Minh ghi khó khăn, trợ giúp và lỗi thật.'),
          ('Windows v1.1','Cập nhật HUONGDAN theo bằng chứng; ghi changelog và retest bằng run/target mới. Chưa có retest thật.'),
          ('Video','Giữ bản đầy đủ; bản demo 3–5 phút chú thích tua/cắt. Không dùng độ dài video biên tập làm RTO.')]),
        ('6. Hoàn thiện bộ nộp',
         [('Số liệu','CSV đo lường, biên bản, danh sách minh chứng. Sheets ghi đúng kịch bản, trạng thái và link.'),
          ('Hồ sơ','Word, PPTX, runbook, video và log đã che. Kiểm native Office và quyền truy cập link.'),
          ('Chưa kết luận','Bốn kịch bản mở rộng chờ xác nhận. Kho cùng host chưa chứng minh mất host hoặc bản sao độc lập.')]),
    ]
    prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
    for index,(title,cards) in enumerate(slides,1):
        slide=prs.slides.add_slide(prs.slide_layouts[6])
        textbox(slide,.6,.45,12.1,.9,title,size=30,color=INK,bold=True)
        for n,(heading,body) in enumerate(cards):card(slide,.6+n*4.1,1.8,3.85,4.1,heading,body)
        textbox(slide,.6,6.7,11.8,.45,'HƯỚNG DẪN • Không phải kết quả diễn tập • Windows NOT TESTED',size=14,color=MUTED)
        textbox(slide,12.3,6.7,.6,.45,str(index),size=14,color=TEAL)
        slide.notes_slide.notes_text_frame.text=(
            'Đây là hướng dẫn thực hành, không phải số liệu hoặc bằng chứng đã chạy. '
            'Nguồn: HUONGDAN.md; BAO_CAO_CAC_PHASE.md; LUU_Y_THUC_NGHIEM.md. '
            'Google Sheets PROJECT NHÓM 8 ATTT, tab planning. '
            'Trình bày giới hạn trước khi diễn giải kết quả; không suy ra Windows PASS từ Linux/mock.')
    presentation=THESIS/'KeHoach_ThucHanh_Windows.pptx'
    prs.core_properties.author='Nhóm 08 — Đa Minh, Minh Quân'
    prs.core_properties.title='Kế hoạch thực hành Windows — chưa nghiệm thu'
    prs.save(presentation)
    print(json.dumps({'docx':str(target.relative_to(ROOT)),'pptx':str(presentation.relative_to(ROOT)),
                      'slides':len(slides),'windows_execution':'NOT TESTED'},ensure_ascii=False))


if __name__=='__main__':main()
