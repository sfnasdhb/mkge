"""
Chạy: python create_test_pdf.py
Tạo file test_medical.pdf trong thư mục hiện tại.
Yêu cầu: pip install reportlab
"""
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

TEXT = """
ĐIỀU TRỊ TĂNG HUYẾT ÁP VÀ CÁC BỆNH ĐỒNG MẮC THƯỜNG GẶP

1. ĐẠI CƯƠNG

Tăng huyết áp (THA) là bệnh tim mạch phổ biến nhất hiện nay, ảnh hưởng đến hơn 25% dân số trưởng thành tại Việt Nam. Bệnh được định nghĩa khi huyết áp tâm thu >= 140 mmHg và/hoặc huyết áp tâm trương >= 90 mmHg.

2. TRIỆU CHỨNG LÂM SÀNG

Bệnh nhân tăng huyết áp thường có các triệu chứng sau:
- Đau đầu, đặc biệt vùng chẩm, thường xuất hiện buổi sáng
- Chóng mặt, ù tai
- Khó thở khi gắng sức
- Đau tức ngực
- Mờ mắt thoáng qua
- Hồi hộp đánh trống ngực

3. CHẨN ĐOÁN

Chẩn đoán tăng huyết áp dựa trên đo huyết áp nhiều lần tại phòng khám hoặc theo dõi huyết áp 24 giờ (Holter huyết áp). Cần phân biệt với tăng huyết áp áo choàng trắng.

Các xét nghiệm cần thiết:
- Điện tâm đồ (ECG)
- Siêu âm tim
- Chụp X-quang ngực
- Xét nghiệm máu: creatinine, glucose, kali, natri

4. ĐIỀU TRỊ BẰNG THUỐC

4.1. Nhóm ức chế men chuyển (ACEI)
Enalapril là thuốc ức chế men chuyển được sử dụng rộng rãi trong điều trị tăng huyết áp và suy tim. Liều thông thường 5-20 mg/ngày. Thuốc có thể gây ho khan do tích lũy bradykinin.

Perindopril được chỉ định trong tăng huyết áp, bệnh động mạch vành ổn định và suy tim. Liều 4-8 mg/ngày.

Ramipril đặc biệt có lợi cho bệnh nhân sau nhồi máu cơ tim và đái tháo đường có protein niệu.

4.2. Nhóm chẹn thụ thể angiotensin II (ARB)
Losartan được chỉ định trong tăng huyết áp, đặc biệt ở bệnh nhân không dung nạp ACEI do ho khan. Liều 50-100 mg/ngày.

Valsartan có hiệu quả trong điều trị tăng huyết áp và suy tim. Liều 80-320 mg/ngày.

4.3. Nhóm chẹn kênh canxi
Amlodipine là thuốc chẹn kênh canxi dihydropyridine tác dụng kéo dài, được dùng trong tăng huyết áp và đau thắt ngực ổn định. Liều 5-10 mg/ngày.

Nifedipine dạng phóng thích chậm được dùng trong tăng huyết áp và đau thắt ngực. Thuốc gây phù mắt cá chân, đỏ bừng mặt.

4.4. Nhóm lợi tiểu thiazide
Hydrochlorothiazide (HCTZ) là lựa chọn đầu tay trong tăng huyết áp không biến chứng. Liều 12.5-25 mg/ngày. Có thể gây hạ kali máu.

Indapamide ít ảnh hưởng đến chuyển hóa glucose và lipid hơn HCTZ.

4.5. Nhóm chẹn beta
Metoprolol được chỉ định trong tăng huyết áp kèm bệnh mạch vành hoặc rối loạn nhịp tim. Liều 25-200 mg/ngày.

Bisoprolol có tính chọn lọc beta-1 cao, dùng trong tăng huyết áp và suy tim. Liều 2.5-10 mg/ngày.

5. CÁC BỆNH ĐỒNG MẮC VÀ XỬ TRÍ

5.1. Tăng huyết áp và đái tháo đường type 2
Đái tháo đường type 2 thường đi kèm với tăng huyết áp. Điều trị ưu tiên ACEI hoặc ARB để bảo vệ thận. Mục tiêu huyết áp < 130/80 mmHg.

Metformin là thuốc hạ đường huyết uống đầu tay trong đái tháo đường type 2. Insulin có thể cần thiết khi đường huyết không kiểm soát được bằng thuốc uống.

5.2. Tăng huyết áp và rối loạn lipid máu
Rối loạn lipid máu thường đồng hành với tăng huyết áp. Atorvastatin và Rosuvastatin là các statin thường dùng để điều trị tăng cholesterol LDL.

5.3. Biến chứng thận mạn tính
Tăng huyết áp là nguyên nhân hàng đầu gây bệnh thận mạn tính. Bệnh thận mạn biểu hiện bằng protein niệu, tăng creatinine máu, phù, thiếu máu.

6. PHÁC ĐỒ ĐIỀU TRỊ KHÔNG DÙNG THUỐC

- Giảm cân nếu thừa cân (BMI > 23)
- Chế độ ăn DASH: tăng rau quả, giảm muối natri < 6g/ngày
- Hạn chế rượu bia
- Tập thể dục aerobic 30 phút/ngày, 5 ngày/tuần
- Bỏ thuốc lá

7. CHỐNG CHỈ ĐỊNH

Enalapril và các ACEI chống chỉ định trong thai kỳ (có thể gây quái thai), hẹp động mạch thận hai bên, và tiền sử phù mạch.

Metoprolol chống chỉ định trong nhịp tim chậm nặng, block nhĩ thất độ cao, và hen phế quản nặng.

Hydrochlorothiazide chống chỉ định trong suy thận nặng và gout cấp.
"""


def create_pdf(output_path: str = "test_medical.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        "VietNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        spaceAfter=8,
    )
    story = []
    for line in TEXT.strip().split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(line, normal))
    doc.build(story)
    print(f"Created: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    create_pdf()
