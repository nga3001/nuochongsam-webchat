"""Sinh brain/kb.json cho Sâm Thái Minh — theo schema Bình Vị v1.0 (docs/05 mục 4.2), mở rộng đa sản phẩm.
Nguồn: 'Sâm Thái Minh 1.xlsx' + thông tin chị Nga bổ sung/chốt qua chat 23–25/09/2026
+ file 'RV-Sâm Thái Minh BRIEF_ THÔNG TIN TRAINING BUSINESS AI chuẩn.docx' (25/09/2026: bảng quà Hồng sâm lát, quy trình 7 bước, bám khách 4 bước)
+ chốt 13/10/2026 (chị Nga): huyết áp cao/thấp/chưa ổn định đều dùng được Hồng sâm Thái Minh; bỏ câu "không phải thuốc" mặc định
  (chỉ khi khách nói đang dùng thuốc tây → khuyên duy trì thuốc + dùng kèm sâm bồi bổ); FAQ chai 175ml là chai nhựa.
+ chốt 15/10/2026 (anh Huy góp ý qua chị Nga, v0.1.17): bỏ "tự trồng", bỏ "gấp 3 lần sâm Hàn", câu MR2/ung thư mới, huyết áp mềm hơn,
  thuốc tây/kháng sinh dùng cách 2 giờ, cho con bú KHÔNG dùng sản phẩm nào, thăm vườn xin SĐT, FAQ mùi sâm + hóa đơn VAT.
Chạy lại script này mỗi khi đổi dữ liệu; KHÔNG sửa tay kb.json."""
import json, os
OUT = os.environ.get("KB_OUT") or os.path.join(os.path.dirname(__file__), "..", "brain", "kb.json")
HL = "1800 1120"
SHIP_HN_INNER, SHIP_OTHER = 15000, 20000

def pk(sku, label, units, price, in_stock=True, unit_name="hộp", note=None):
    d = {"sku": sku, "label": label, "units": units, "price_retail": price, "in_stock": in_stock, "unit_name": unit_name}
    if note: d["note"] = note
    return d

# Chốt 13/10 (chị Nga): huyết áp — dùng chung cho mọi dạng Hồng sâm Thái Minh (lát, chai, túi)
BP_NOTE = ("Người huyết áp cao, huyết áp thấp dùng được Hồng sâm Thái Minh. Hồng sâm một phần hỗ trợ điều hòa tuần hoàn và chức năng mạch máu, "
           "từ đó hỗ trợ ổn định huyết áp (chốt 15/10: nói mềm, không khẳng định). Người đang dùng thuốc huyết áp vẫn nên duy trì thuốc theo chỉ định của bác sĩ "
           "và dùng Hồng sâm cách thuốc khoảng 2 tiếng.")

P = {}
P["hsvn_lat"] = {
 "name": "Hồng Sâm Việt Nam Thái Minh (dạng lát)", "role": "core",
 "aka": ["hồng sâm lát", "sâm lát", "hồng sâm lai châu", "HSVN", "sâm ngậm"],
 "type": "Thực phẩm (tự công bố số 08/CNCTHAIMINH/2025) — KHÔNG phải thực phẩm bảo vệ sức khỏe, KHÔNG phải thuốc",
 "summary": "Hồng sâm lát từ Sâm Lai Châu (Sâm Việt Nam) 99% + mật ong 1%, sâm 5–6 năm tuổi, nguyên liệu có nguồn gốc rõ ràng, được kiểm soát chặt chẽ chất lượng đầu vào (chốt 23/10: KHÔNG nói toàn bộ sâm trồng ở Sìn Hồ); bồi bổ, tăng sức đề kháng cho người trung và cao tuổi, người mới ốm dậy, người có bệnh nền.",
 "key_ingredients": [{"name": "Sâm Lai Châu (Panax vietnamensis var. fuscidiscus)", "amount": "99% (gói 2g)"}, {"name": "Phụ liệu", "amount": "mật ong (1%), catazyme-pect, acid citric (theo bản tự công bố 08/CNCTHAIMINH/2025)"}],
 "benefits": ["Hỗ trợ bồi bổ, tăng cường sức khỏe toàn diện", "Hỗ trợ tăng sức đề kháng, nâng cao miễn dịch", "Hỗ trợ cải thiện trí nhớ, minh mẫn, làm chậm lão hóa", "Hỗ trợ giảm căng thẳng, an thần, ngủ ngon hơn", "Hỗ trợ bảo vệ sức khỏe tim mạch, giảm mỡ máu, giảm xơ vữa động mạch", "Hỗ trợ điều hòa tuần hoàn và chức năng mạch máu, từ đó hỗ trợ ổn định huyết áp (dùng được cho cả người huyết áp cao và huyết áp thấp); hỗ trợ phòng ngừa nguy cơ đột quỵ ở người cao tuổi", "Hỗ trợ kiểm soát đường huyết", "Hỗ trợ ức chế quá trình phân bào của tế bào một số loại ung thư (hoạt chất MR2 — nghiên cứu của Đại học Dược Kyoto, Nhật Bản)"],
 "usp": ["Hồng sâm đầu tiên chế biến từ Sâm Việt Nam — công trình chuyển giao từ VIGH (Viện Nghiên cứu Sâm và Dược liệu Việt Nam)", "Công nghệ lên men vi sinh giúp dễ hấp thu, giảm 70% vị đắng", "Có hoạt chất quý MR2 (Majonoside-R2) — một saponin chiếm hàm lượng cao trong Sâm Lai Châu, sâm Hàn Quốc không có (chốt 15/10: KHÔNG nói 'gấp 3 lần sâm Hàn Quốc', KHÔNG nêu % MR2); nghiên cứu của Đại học Dược Kyoto (Nhật Bản) cho thấy MR2 có tác dụng hỗ trợ ức chế quá trình phân bào của tế bào một số loại ung thư", "Sâm Việt Nam tính bình: dùng không bị lạnh bụng, không bị đi ngoài (điểm này không liên quan huyết áp)", "Huyết áp: Hồng sâm một phần hỗ trợ điều hòa tuần hoàn và chức năng mạch máu, từ đó hỗ trợ ổn định huyết áp (người bệnh huyết áp vẫn duy trì thuốc theo chỉ định bác sĩ, dùng sâm cách thuốc khoảng 2 tiếng)", "Nguyên liệu sâm có nguồn gốc rõ ràng, hóa đơn, chứng từ đầy đủ; toàn bộ sâm đưa vào sản xuất được kiểm soát chặt chẽ chất lượng đầu vào (chốt 15/10: không tự nhắc vườn; khách hỏi thẳng có vườn không → scripts_approved.origin)", "Hồng sâm so với sâm tươi: dễ hấp thu hơn, bảo quản dễ dàng hơn"],
 "evidence_rule": "Chốt 23/09 + 13/10: được nói các tác dụng liên quan bệnh lý NHƯNG luôn mở đầu bằng 'hỗ trợ'. Mẫu được phép: 'Trong Sâm Lai Châu có hoạt chất MR2, một saponin chiếm hàm lượng cao trong Sâm Lai Châu; nghiên cứu của Đại học Dược Kyoto, Nhật Bản cho thấy MR2 có tác dụng hỗ trợ ức chế quá trình phân bào của tế bào một số loại ung thư' (chốt 15/10 — KHÔNG nói '50%', KHÔNG nói 'chống khối u'), 'hỗ trợ ngăn ngừa sự phát triển của tế bào ung thư', 'hỗ trợ kiểm soát đường huyết', 'hỗ trợ ổn định huyết áp', 'hỗ trợ giảm mỡ máu, giảm xơ vữa động mạch', 'hỗ trợ phòng ngừa nguy cơ đột quỵ ở người cao tuổi'. Chốt 13/10: KHÔNG tự nói câu 'không phải thuốc, không thay thế thuốc'; chỉ khi khách nói đang dùng thuốc tây chữa bệnh nền mới khuyên duy trì thuốc + dùng kèm sâm bồi bổ. CẤM: chữa, điều trị, trị liệu, kháng ung thư (thiếu chữ hỗ trợ), khỏi, diệt, đẩy lùi, thay thế thuốc, cam kết/chắc chắn, 'đã chứng minh chữa', và các con số lâm sàng không có nguồn.",
 "dosage": {"standard": "Ngày 1 gói (2g), ngậm dưới lưỡi 3–5 phút rồi nhai ăn như bình thường; dùng buổi sáng hoặc trưa, trước ăn 30 phút hoặc sau ăn 1 giờ. KHÔNG dùng buổi tối (sâm làm tỉnh táo, dễ khó ngủ).",
   "diabetes": "Người tiểu đường: 1 gói/ngày CHIA 2 LẦN — sáng 1/2 gói trước ăn sáng 30 phút, trưa 1/2 gói trước ăn trưa 30 phút (sản phẩm có 1% mật ong nên dùng lúc đói, đường huyết không cao). KHÔNG nói 'cất tủ lạnh / để dành hôm sau' (đó là cách dùng của người dùng thuốc chống đông).",
   "blood_pressure": BP_NOTE + " Dùng liều thường 1 gói/ngày.",
   "children": "Trẻ 6–11 tuổi: 1/2 gói/ngày; từ 12 tuổi: 1 gói/ngày. Dưới 6 tuổi: không dùng.",
   "anticoagulant": "Đang dùng thuốc chống đông ≥ 6 tháng: 1/2 gói/ngày trước ăn 30 phút, nửa còn lại buộc kín để tủ lạnh. Dưới 6 tháng: chuyển chuyên viên tư vấn (không tự tư vấn). Khuyên khách duy trì thuốc chống đông theo bác sĩ.",
   "antibiotic": "Đang dùng kháng sinh hoặc thuốc tây: dùng cách thuốc khoảng 2 giờ (chốt 15/10).",
   "course": "Liệu trình cơ bản 3–6 tháng, có thể dùng hằng ngày lâu dài. Khách lăn tăn chi phí: dùng liệu trình 3 tháng, mỗi năm nhắc lại 1–2 đợt.",
   "expect": "Theo brief 25/09: thông thường sau khi dùng hết 2 hộp đầu tiên, cơ thể bắt đầu hấp thụ dưỡng chất từ sâm — anh/chị sẽ thấy ăn ngon, ngủ sâu hơn, khỏe khoắn hơn, giảm mệt mỏi, tinh thần tỉnh táo ban ngày. Tùy cơ địa, không hứa nhanh hơn."},
 "packages": [pk("hsvn-lat-14", "Hộp thiếc 14 gói x 2g (mỗi gói 1–2 lát sâm)", 14, 1420000), pk("hsvn-lat-50", "Hộp 50 gói x 2g", 50, 5000000, note="chốt 16/10 (chị Nga): ĐÃ CÓ HÀNG — chỉ nói khi khách hỏi; mua hộp 50 gói hiện KHÔNG có CTKM (không quà)")],
 "recommended_package": "hsvn-lat-14", "days_per_unit": {"hsvn-lat-14": 14},
 "hotline": "1800 1120 (chính), 1800 8396",
 "registration": "Số tự công bố 08/CNCTHAIMINH/2025 — Công ty Cổ phần Công nghệ Cao Thái Minh sản xuất",
 "authenticity": "Nguyên hộp, nguyên tem/niêm phong, đủ ngày sản xuất – hạn sử dụng – số lô; quét mã vạch/QR bằng app iCheck Scan; hoặc chụp hộp gửi page để bên em xác minh.",
}
# Chốt 24/09/2026 (chị Nga): Hồng sâm mật ong dạng nước — chai và túi dùng CHUNG một bản tự công bố 11/CNCTHAIMINH/2025.
REG_HSMO = "Bản tự công bố số 11/CNCTHAIMINH/2025 (Nước Hồng Sâm Thái Minh mật ong +) — dùng CHUNG cho cả dạng chai và dạng túi (chị Nga xác nhận 24/09/2026); Công ty Cổ phần Công nghệ Cao Thái Minh sản xuất"
P["hsmo_chai"] = {
 "name": "Nước Hồng sâm Thái Minh mật ong (chai 175ml)", "role": "core",
 "aka": ["hồng sâm nước", "hồng sâm mật ong", "nước sâm", "dạng chai", "HSMO"],
 "type": "Thực phẩm (công bố tại Chi cục Quản lý chất lượng Nông lâm sản và Thủy sản Hà Nội) — không phải thuốc",
 "summary": "Tinh chất Hồng sâm Lai Châu trong mật ong, pha nước ấm uống; vị ngọt nhẹ, dễ uống, lựa chọn tiết kiệm cho cả gia đình.",
 "key_ingredients": [{"name": "Tinh chất Hồng sâm Lai Châu trong mật ong", "amount": "11.000mg/10ml (tương đương 1.200mg Hồng sâm Lai Châu)"}, {"name": "Phụ liệu", "amount": "natri benzoat, kali sorbat, nước tinh khiết"}],
 "benefits": ["Hỗ trợ bồi bổ, tăng sức đề kháng", "Hỗ trợ giảm mệt mỏi, căng thẳng, ngủ ngon hơn", "Hỗ trợ cải thiện trí nhớ, minh mẫn", "Hỗ trợ làm chậm lão hóa, chăm sóc làn da", "Hỗ trợ bảo vệ sức khỏe tim mạch, hỗ trợ ổn định huyết áp", "Hỗ trợ ngăn ngừa sự phát triển của tế bào ung thư"],
 "packaging": "Chốt 15/10: chai nhựa chuyên dùng trong ngành thực phẩm & dược phẩm, đảm bảo an toàn cho sức khỏe (KHÔNG nói 'cao cấp'); ưu điểm: rất nhẹ, bền, dễ rót, không bị đập vỡ khi vận chuyển, tiện mang theo dùng hằng ngày. (Không phải chai thủy tinh.)",
 "dosage": {"standard": "Khoảng 10ml pha với 100ml nước ấm 60°C, khuấy đều; uống 1–2 lần/ngày.", "diabetes": "Người tiểu đường DÙNG ĐƯỢC (chốt 16/10, chị Nga): 5ml/ngày + 100ml nước ấm 60°C, sáng sớm khi ngủ dậy, trước ăn 30 phút, lúc đường huyết đang ổn định.", "blood_pressure": BP_NOTE, "breastfeeding": "Chốt 15/10: phụ nữ ĐANG CHO CON BÚ không dùng (không dùng bất kỳ sản phẩm nào). Mẹ sau sinh KHÔNG cho con bú: dùng được ngay để bồi bổ (chốt 15/10)."},
 "packages": [pk("hsmo-chai", "Chai nhựa 175ml", 1, 550000, unit_name="chai")],
 "recommended_package": "hsmo-chai", "hotline": "1800 1120 (chính), 1800 8396",
 "registration": REG_HSMO,
}
P["hsmo_tui"] = {
 "name": "Nước Hồng sâm Thái Minh mật ong + (dạng túi)", "role": "core",
 "aka": ["hồng sâm túi", "HSMO+", "hồng sâm mật ong plus", "dạng túi"],
 "type": "Thực phẩm (công bố tại Chi cục Quản lý chất lượng Nông lâm sản và Thủy sản Hà Nội) — không phải thuốc",
 "summary": "Hồng sâm mật ong đóng túi 8ml tiện mang theo, ăn trực tiếp hoặc pha nước ấm; phù hợp người bận rộn, người sợ vị đắng.",
 "key_ingredients": [{"name": "Tinh chất Hồng sâm Lai Châu trong mật ong", "amount": "11.000mg/10ml (tương đương 1.200mg Hồng sâm Lai Châu)"}, {"name": "Phụ liệu", "amount": "natri benzoat, kali sorbat, nước tinh khiết"}],
 "benefits": ["Hỗ trợ bồi bổ, tăng sức đề kháng", "Hỗ trợ giảm mệt mỏi, căng thẳng, ngủ ngon hơn", "Hỗ trợ cải thiện trí nhớ, minh mẫn", "Hỗ trợ làm chậm lão hóa, chăm sóc làn da", "Hỗ trợ bảo vệ sức khỏe tim mạch, hỗ trợ ổn định huyết áp", "Hỗ trợ ngăn ngừa sự phát triển của tế bào ung thư"],
 "dosage": {"standard": "1 túi ăn trực tiếp hoặc pha 100ml nước ấm 60°C; ngày 1–2 túi.", "diabetes": "Người tiểu đường DÙNG ĐƯỢC (chốt 16/10, chị Nga): 1 túi pha 100ml nước ấm 60°C, sáng sớm trước ăn 30 phút, lúc đường huyết đang ổn định.", "blood_pressure": BP_NOTE, "breastfeeding": "Chốt 15/10: phụ nữ ĐANG CHO CON BÚ không dùng (không dùng bất kỳ sản phẩm nào). Mẹ sau sinh KHÔNG cho con bú: dùng được ngay để bồi bổ (chốt 15/10).", "sport": "Muốn cung cấp năng lượng trước khi vận động, chơi thể thao thì dùng buổi tối được."},
 "packages": [pk("hsmo-tui", "Hộp 2 hộp mềm x 10 túi x 8ml (20 túi)", 20, 620000), pk("hsmo-tui-10", "Hộp 10 túi x 8ml", 10, 330000, note="chỉ báo khi khách hỏi gói nhỏ / muốn dùng thử")],
 "recommended_package": "hsmo-tui", "days_per_unit": {"hsmo-tui": 20, "hsmo-tui-10": 10}, "hotline": "1800 1120 (chính), 1800 8396",
 "registration": REG_HSMO,
}
P["duong_sam"] = {
 "name": "Dương Sâm Linh Đan", "role": "core", "aka": ["dương sâm", "sâm nam", "sinh lý nam"],
 "type": "Thực phẩm bảo vệ sức khỏe (Cục An toàn thực phẩm cấp)",
 "summary": "Viên hoàn mềm dành cho nam giới từ đủ 18 tuổi sinh lý yếu (xuất tinh sớm, ham muốn giảm, kém cương), đau lưng mỏi gối do thận kém: Đông trùng hạ thảo, Dâm dương hoắc, cao xương dê, Trâu cổ, Tích dương, Kẽm, Sâm Lai Châu.",
 "key_ingredients": [{"name": "Nấm đông trùng hạ thảo (Cordyceps militaris)", "amount": "1000mg"}, {"name": "Cao tổng hợp (cao Trâu cổ 105mg + cao Tích dương 105mg)", "amount": "210mg"}, {"name": "Cao Dâm dương hoắc", "amount": "200mg"}, {"name": "Cao xương dê", "amount": "200mg"}, {"name": "Kẽm gluconat (tương đương kẽm 25mg)", "amount": "175mg"}, {"name": "Sâm Lai Châu", "amount": "150mg"}, {"name": "Phụ liệu", "amount": "mật ong"}],
 "benefits": ["Hỗ trợ bổ thận, tráng dương", "Hỗ trợ cải thiện sinh lý nam giới", "Hỗ trợ cải thiện tình trạng xuất tinh sớm, ham muốn giảm, kém cương", "Hỗ trợ giảm các biểu hiện sinh lý yếu, đau lưng, mỏi gối do thận kém"],
 "dosage": {"standard": "Ngày 1 viên (viên hoàn mềm 4g, to như viên bi ve), buổi tối 8–9 giờ, sau ăn tối 1 giờ."},
 "packages": [pk("duongsam-10", "Hộp 10 viên hoàn mềm x 4g", 10, 990000)],
 "recommended_package": "duongsam-10", "days_per_unit": {"duongsam-10": 10}, "hotline": "1800 8308",
 "disclaimer_required": False, "registration": "Giấy tiếp nhận đăng ký bản công bố số 3496/2024/ĐKSP — Cục An toàn thực phẩm, 14/04/2024. Sản xuất: Công ty TNHH Đông Dược Phúc Hưng; công ty công bố: Công ty Cổ phần Công nghệ Cao Thái Minh",
}
P["tra_nguyen_la"] = {
 "name": "Trà sâm Lai Châu nguyên lá", "role": "on_request_only", "aka": ["trà sâm nguyên lá", "trà lá sâm"],
 "type": "Thực phẩm (công bố tại Chi cục Quản lý chất lượng Nông lâm sản và Thủy sản Hà Nội)",
 "summary": "100% lá Sâm Lai Châu từ trang trại Thái Minh, dạng nguyên lá chế biến truyền thống giữ saponin; vị thanh ngọt, dễ uống hằng ngày.",
 "key_ingredients": [{"name": "Lá Sâm Lai Châu (Folium Panax vietnamensis var. fuscidiscus)", "amount": "100%"}],
 "benefits": ["Hỗ trợ bồi bổ sức khỏe", "Hỗ trợ điều hòa huyết áp", "Hỗ trợ sức khỏe trí não và tim mạch", "Giúp an thần, ăn ngon"],
 "dosage": {"standard": "Tráng ấm bằng nước sôi; cho 1–1,5g trà vào ấm khoảng 200ml; rót nước 90–100°C; hãm 3–5 phút. Uống hằng ngày."},
 "packages": [pk("tra-nguyenla-100", "Hộp túi 100g ±5%", 1, 1250000), pk("tra-nguyenla-40", "Hộp túi 40g ±5%", 1, 750000, in_stock=False, note="hết hàng — chỉ tư vấn hộp 100g")],
 "recommended_package": "tra-nguyenla-100", "hotline": HL,
 "sales_rule": "Chốt 25/09 (chị Nga): CHỈ tư vấn khi khách TỰ hỏi đích danh trà sâm (hoặc khách đến từ bài viết/quảng cáo về trà sâm — chốt 13/10); KHÔNG chủ động giới thiệu/gợi ý/upsell.",
}
P["tra_1700"] = {
 "name": "Trà sâm 1700", "role": "on_request_only", "aka": ["trà sâm túi lọc", "trà 1700", "trà sâm"],
 "type": "Thực phẩm (công bố tại Chi cục Quản lý chất lượng Nông lâm sản và Thủy sản Hà Nội)",
 "summary": "Trà túi lọc thảo mộc: táo đỏ, lá đinh lăng, nhân sâm, đảng sâm, cam thảo, lá Sâm Lai Châu — uống hằng ngày, giá mềm.",
 "key_ingredients": [{"name": "Táo đỏ", "amount": "550mg"}, {"name": "Lá đinh lăng", "amount": "300mg"}, {"name": "Nhân sâm (Panax ginseng)", "amount": "200mg"}, {"name": "Đảng sâm", "amount": "200mg"}, {"name": "Cam thảo", "amount": "150mg"}, {"name": "Lá Sâm Lai Châu", "amount": "100mg"}],
 "benefits": ["Hỗ trợ tăng cường sức khỏe, sức đề kháng", "Hỗ trợ giảm căng thẳng, cải thiện trí nhớ", "Hỗ trợ sức khỏe tim mạch, làn da"],
 "dosage": {"standard": "Ngày 1–2 gói. Pha 1 gói với 250ml nước sôi 95–100°C, ủ 10–15 phút (có thể ủ bình giữ nhiệt).", "children": "Trẻ em dùng được theo hướng dẫn pha trên vỏ hộp."},
 "packages": [pk("tra1700-20", "Hộp 20 túi lọc", 20, 190000), pk("tra1700-10", "Hộp 10 túi lọc", 10, 120000)],
 "recommended_package": "tra1700-20", "hotline": HL,
 "sales_rule": "Chốt 25/09 (chị Nga): CHỈ tư vấn khi khách TỰ hỏi đích danh trà sâm để MUA (hoặc khách đến từ bài viết/quảng cáo về trà sâm — chốt 13/10); KHÔNG chủ động giới thiệu/gợi ý/upsell. Được nhắc Trà sâm khi báo QUÀ TẶNG kèm combo.",
}
P["ruou_sam"] = {
 "name": "Rượu Sâm Thái Minh", "role": "on_request_only", "aka": ["rượu sâm", "rượu sâm nguyên cây", "hũ rượu sâm"],
 "type": "Thực phẩm — đồ uống có cồn",
 "summary": "Rượu ngâm Sâm Lai Châu vườn Thái Minh. Chai 650ml: 30 độ, ngâm khoảng 150g sâm/lít. Hũ 3,5 lít và bình 4 lít: 32 độ, cây Sâm Lai Châu 5 tuổi nguyên lá ngâm rượu nếp cái hoa vàng.",
 "key_ingredients": [{"name": "Sâm Lai Châu vườn Thái Minh", "amount": "khoảng 150g/lít (chai 650ml, 30 độ theo nhãn)"}, {"name": "Rượu nếp cái hoa vàng", "amount": "hũ 3,5 lít và bình 4 lít 32 độ; chai 650ml 30 độ"}],
 "benefits": ["Dùng để bồi bổ sức khỏe"],
 "dosage": {"standard": "Dùng ban ngày, hạn chế buổi tối; mỗi lần 10–20ml (1–2 chén nhỏ). Không lái xe sau khi uống."},
 "packages": [pk("ruou-650", "Chai 650ml (30 độ)", 1, 1200000, unit_name="chai"), pk("ruou-hu-35", "Hũ sâm nguyên cây 3,5 lít (32 độ)", 1, 8800000, unit_name="hũ"), pk("ruou-hu-4", "Rượu sâm Lai Châu bình 4 lít (sâm nguyên cây, 32 độ)", 1, 9900000, unit_name="bình")],
 "recommended_package": "ruou-650", "hotline": HL,
 "sales_rule": "CHỈ tư vấn khi khách HỎI (hoặc khách đến từ bài viết/quảng cáo về rượu sâm — chốt 13/10); KHÔNG chủ động giới thiệu/gợi ý/upsell; không bán cho người dưới 18 tuổi.",
}
P["long_sam"] = {
 "name": "Long Sâm Linh Đan", "role": "core", "aka": ["long sâm", "viên hoàn sâm cao cấp", "quà biếu cao cấp"],
 "type": "Thực phẩm bảo vệ sức khỏe (Cục An toàn thực phẩm cấp)",
 "summary": "Viên hoàn cao cấp: Đông trùng hạ thảo, Cao ban long, Sâm Việt Nam, Hoàng kỳ, Kẽm — bồi bổ người suy nhược, sức đề kháng giảm, mới ốm dậy; hợp làm quà biếu.",
 "key_ingredients": [{"name": "Nấm đông trùng hạ thảo (Cordyceps militaris)", "amount": "1200mg"}, {"name": "Cao ban long", "amount": "400mg"}, {"name": "Thân rễ và rễ Sâm Việt Nam", "amount": "300mg"}, {"name": "Cao khô rễ Hoàng kỳ (tương đương 520mg rễ thô)", "amount": "104mg"}, {"name": "Kẽm gluconat (tương đương kẽm 11,43mg)", "amount": "80mg"}, {"name": "Phụ liệu", "amount": "mật ong"}],
 "benefits": ["Hỗ trợ nâng cao sức đề kháng", "Hỗ trợ bồi bổ sức khỏe"],
 "dosage": {"standard": "Ngày 1 viên buổi sáng, sau ăn 30 phút; có thể chia nhỏ để nhai."},
 "packages": [pk("longsam-6", "Hộp 6 viên", 6, 1050000), pk("longsam-30", "Hộp 30 viên", 30, 4750000)],
 "recommended_package": "longsam-6", "days_per_unit": {"longsam-6": 6, "longsam-30": 30}, "hotline": HL,
 "disclaimer_required": False, "registration": "Giấy tiếp nhận đăng ký bản công bố số 6193/2024/ĐKSP — Cục An toàn thực phẩm, 30/08/2024. Sản xuất: Công ty TNHH Đông Dược Phúc Hưng; công ty công bố: Công ty Cổ phần Công nghệ Cao Thái Minh",
}
P["tam_sam_dan"] = {
 "name": "Tam Sâm Đan Thái Minh", "role": "on_request_only", "aka": ["tam sâm đan", "tam sâm"],
 "type": "Thực phẩm bảo vệ sức khỏe — Số đăng ký 7514/2024/ĐKSP",
 "summary": "Viên nang kết hợp 3 dược liệu Đảng sâm – Đan sâm – Cát sâm; hỗ trợ tăng cường sức khỏe, sức đề kháng cho người suy nhược, mệt mỏi, kém ăn, người cao tuổi.",
 "key_ingredients": [{"name": "Cao khô rễ Đảng sâm (Codonopsis pilosula)", "amount": "100mg"}, {"name": "Cao khô rễ Đan sâm (Salvia miltiorrhiza)", "amount": "90mg"}, {"name": "Cao khô rễ Cát sâm (Millettia speciosa)", "amount": "50mg"}],
 "benefits": ["Hỗ trợ tăng cường sức khỏe", "Hỗ trợ tăng cường sức đề kháng"],
 "dosage": {"standard": "Người lớn: 4 viên/ngày, chia 2 lần, trước ăn 30 phút hoặc sau ăn 1 giờ.", "course": "Nên duy trì 3–6 tháng. 1 hộp 30 viên dùng được khoảng 7–8 ngày ở liều 4 viên/ngày."},
 "packages": [pk("tamsamdan-30", "Hộp 30 viên nang", 30, 560000)],
 "recommended_package": "tamsamdan-30", "days_per_unit": {"tamsamdan-30": 7}, "hotline": HL,
 "manufacturer": "Nhà máy Công nghệ cao Thái Minh Hitech (đạt GMP Bộ Y tế; phòng kiểm nghiệm ISO/IEC 17025) — Lô CN5, Khu công nghiệp Thạch Thất – Quốc Oai, Hà Nội",
 "disclaimer_required": False, "registration": "7514/2024/ĐKSP",
 "sales_rule": "Chốt 25/09 (chị Nga): CHỈ tư vấn khi khách TỰ hỏi đích danh Tam Sâm Đan (hoặc khách đến từ bài viết/quảng cáo về Tam Sâm Đan — chốt 13/10); KHÔNG chủ động giới thiệu, không gợi ý thay thế, không upsell.",
}
P["dong_trung"] = {
 "name": "Đông trùng hạ thảo Thái Minh", "role": "on_request_only", "aka": ["đông trùng", "đông trùng hạ thảo", "ĐTHT"],
 "type": "Thực phẩm bảo vệ sức khỏe — Số XNCB 10016/2021/ĐKSP; GPQC 88/2022/XNQC-ATTP",
 "summary": "Viên nang Nấm Đông trùng hạ thảo kết hợp HERISIN (Nấm hầu thủ + chiết xuất Đảng sâm Việt Nam); hỗ trợ tăng cường sức khỏe, giảm mệt mỏi cho người gầy yếu, suy nhược.",
 "key_ingredients": [{"name": "Nấm Đông trùng hạ thảo (Cordyceps militaris)", "amount": "250mg"}, {"name": "HERISIN (Nấm hầu thủ + chiết xuất Đảng sâm Việt Nam)", "amount": "150mg"}, {"name": "Phụ liệu", "amount": "tinh bột, talc, magie stearat, calci carbonat, aerosil, vỏ nang gelatin"}],
 "benefits": ["Hỗ trợ tăng cường sức khỏe", "Hỗ trợ giảm mệt mỏi"],
 "dosage": {"weak": "Người sức khỏe kém, gầy yếu, suy nhược: 4 viên/ngày chia 2 lần (sáng, trưa).", "normal": "Người bình thường: 2 viên/ngày, sáng hoặc trưa.", "timing": "Uống trước ăn 30 phút hoặc sau ăn 1 giờ.", "course": "Dùng liên tục 1 đợt 2–3 tháng, mỗi năm 2–3 đợt; có thể dùng lâu dài."},
 "packages": [pk("dongtrung-30", "Hộp 30 viên nang", 30, 750000)],
 "recommended_package": "dongtrung-30", "hotline": HL, "disclaimer_required": False,
 "registration": "XNCB 10016/2021/ĐKSP; GPQC 88/2022/XNQC-ATTP",
 "sales_rule": "Chốt 25/09 (chị Nga): CHỈ tư vấn khi khách TỰ hỏi đích danh Đông trùng hạ thảo (hoặc khách đến từ bài viết/quảng cáo về Đông trùng hạ thảo — chốt 13/10); KHÔNG chủ động giới thiệu, không gợi ý thay thế, không upsell.",
}
P["sam_tuoi"] = {
 "name": "Sâm tươi Lai Châu nguyên cây (5 tuổi)", "role": "on_request_only", "aka": ["sâm tươi", "sâm củ tươi", "sâm nguyên cây"],
 "type": "Nông sản — sâm tươi",
 "summary": "Sâm Lai Châu tươi 5 tuổi từ vườn Thái Minh Panax (Sìn Hồ, Lai Châu), bán nguyên cây gồm củ, thân, lá; khoảng 8–12 cây/kg.",
 "benefits": [], "dosage": {},
 "packages": [pk("samtuoi-kg", "1kg sâm tươi nguyên cây (khoảng 8–12 cây)", 1, 30000000, unit_name="kg")],
 "recommended_package": "samtuoi-kg", "hotline": HL,
 "sales_rule": "Đang mùa phát triển nên chỉ bán nguyên cây; muốn mua riêng củ thì chờ khoảng tháng 12 (sâm rụng lá). Đơn sâm tươi → bot báo giá, thu thông tin rồi CHUYỂN nhân viên chốt (cân thực tế).",
}
# Chốt 13/10: tên ngắn dùng khi xác nhận đơn
SHORT = {"hsvn_lat": "Hồng sâm dạng lát", "hsmo_chai": "Hồng sâm dạng nước (chai 175ml)", "hsmo_tui": "Hồng sâm dạng nước (hộp 20 túi)",
         "duong_sam": "Dương Sâm Linh Đan", "long_sam": "Long Sâm Linh Đan", "tam_sam_dan": "Tam Sâm Đan", "dong_trung": "Đông trùng hạ thảo",
         "tra_1700": "Trà sâm 1700", "tra_nguyen_la": "Trà sâm nguyên lá", "ruou_sam": "Rượu sâm", "sam_tuoi": "Sâm tươi"}
for pid, p in P.items():
    p["id"] = pid
    p["short_name"] = SHORT[pid]

# ---------------- compliance theo sản phẩm ----------------
def A(key, label, action): return {"key": key, "label": label, "action": action}
G_ABS = [A("ingredient_allergy", "Mẫn cảm/dị ứng với thành phần sản phẩm", "Không bán sản phẩm đó. Xin lỗi khách, khuyên hỏi bác sĩ."),
         A("adr_severe", "Phản ứng nặng sau khi dùng: khó thở, sưng môi/mặt/lưỡi/họng, mề đay lan rộng, choáng, tim đập nhanh bất thường", "NGỪNG NGAY, khuyên đi khám/cấp cứu. Không bán thêm. [HANDOFF: nghi ADR nặng | SĐT | 4].")]
G_CAU = [A("adr_mild", "Nghi phản ứng nhẹ–vừa sau khi dùng (mẩn ngứa, khó ngủ, nóng trong, đầy bụng, tiêu chảy, hồi hộp...)", "Khuyên TẠM NGỪNG, không phủ nhận, không phán nguyên nhân; khai thác 7 trường; [HANDOFF: nghi ADR | SĐT | 4]."),
         A("prescription_meds_unlisted", "Đang dùng thuốc kê đơn KHÔNG có hướng dẫn trong tài liệu (tim mạch, chẹn beta, chống động kinh, ức chế miễn dịch...)", "KHÔNG tự khẳng định dùng chung được. Chuyển chuyên viên chuyên môn: xin SĐT + [HANDOFF: hỏi tương tác thuốc | SĐT | 3]."),
         A("serious_condition", "Bệnh nặng chưa có trong tài liệu: suy thận giai đoạn cuối/chạy thận, tim mạch phức tạp (ung thư đang điều trị dùng flag cancer_treatment)", "KHÔNG tự chốt đơn. Khuyên hỏi bác sĩ điều trị; chuyển chuyên viên chuyên môn: xin SĐT + [HANDOFF: bệnh nặng đang điều trị | SĐT | 3].")]
UNKNOWN_ACTION = "Tài liệu nhãn hàng CHƯA có hướng dẫn cho đối tượng này với sản phẩm này → KHÔNG suy luận, KHÔNG khẳng định dùng được hay không; trả lời đúng câu chuẩn scripts_approved.disease_no_guidance + [HANDOFF: đối tượng đặc biệt chưa có hướng dẫn | SĐT | 3]."
# Chốt 13/10 (chị Nga): huyết áp cao / thấp / chưa ổn định đều DÙNG ĐƯỢC mọi dạng Hồng sâm Thái Minh.
MEDS_NOTE = " Chỉ khi khách NÓI đang dùng thuốc huyết áp (thuốc tây) → khuyên duy trì thuốc bác sĩ kê, dùng kèm sản phẩm để bồi bổ, dùng cách thuốc khoảng 2 tiếng (1 lần)."
# Chốt 13/10 (chị Nga): viêm khớp dạng thấp, tuyến giáp, tiền sử tai biến/đột quỵ dùng được bình thường Hồng sâm Thái Minh.
EXTRA_CAU = [A("rheumatoid_arthritis", "Viêm khớp dạng thấp", "Dùng được bình thường (chốt 13/10). Liều thường."),
             A("thyroid", "Bệnh tuyến giáp", "Dùng được bình thường (chốt 13/10). Liều thường."),
             A("stroke_history", "Tiền sử tai biến/đột quỵ do nhồi máu/tắc mạch, đã ổn định (KHÔNG phải xuất huyết)", "Dùng được (chốt 13/10). Tai biến do xuất huyết → flag stroke_hemorrhagic (chuyển chuyên viên). Nếu đang dùng thuốc chống đông: theo flag anticoagulant_ge6m / anticoagulant_lt6m (dưới 6 tháng → không tự tư vấn).")]
BP_CAU = [A("hypertension", "Huyết áp cao", "Dùng được — nói theo câu chuẩn scripts_approved.bp_question (Hồng sâm một phần hỗ trợ điều hòa tuần hoàn và chức năng mạch máu, từ đó hỗ trợ ổn định huyết áp); Được nói thêm (chốt 16/10, chị Nga): \"Hồng sâm Việt Nam không gây tăng huyết áp như sâm Hàn Quốc\"; KHÔNG tự giải thích về tinh dầu / hoạt chất gây kích thích tim mạch, KHÔNG chê sâm tươi. Liều thường." + MEDS_NOTE),
          A("hypotension", "Huyết áp thấp", "Dùng được — nói theo câu chuẩn scripts_approved.bp_question (Hồng sâm một phần hỗ trợ điều hòa tuần hoàn và chức năng mạch máu, từ đó hỗ trợ ổn định huyết áp); Được nói thêm (chốt 16/10, chị Nga): \"Hồng sâm Việt Nam không gây tăng huyết áp như sâm Hàn Quốc\"; KHÔNG tự giải thích về tinh dầu / hoạt chất gây kích thích tim mạch, KHÔNG chê sâm tươi. Liều thường." + MEDS_NOTE),
          A("bp_uncontrolled", "Huyết áp chưa ổn định / đang dao động", "Dùng được — nói theo câu chuẩn scripts_approved.bp_question (Hồng sâm một phần hỗ trợ điều hòa tuần hoàn và chức năng mạch máu, từ đó hỗ trợ ổn định huyết áp); Được nói thêm (chốt 16/10, chị Nga): \"Hồng sâm Việt Nam không gây tăng huyết áp như sâm Hàn Quốc\"; KHÔNG tự giải thích về tinh dầu / hoạt chất gây kích thích tim mạch, KHÔNG chê sâm tươi. Liều thường." + MEDS_NOTE)]
ULCER = A("stomach_ulcer", "Viêm loét dạ dày", "Chốt 16/10 (chị Nga): người viêm loét dạ dày CÓ THỂ dùng Hồng sâm Việt Nam Thái Minh — Hồng sâm không gây viêm hay làm đau tăng nặng. NHƯNG khi bệnh đang tiến triển nặng hoặc CÒN triệu chứng đau dạ dày thì CHƯA NÊN dùng lúc này, nên tập trung điều trị dạ dày ổn định trước. Khi dạ dày đã ổn định, không còn triệu chứng đau → hoàn toàn dùng được bình thường để hỗ trợ tăng cường sức khỏe. Hỏi khách hiện còn đau không trước khi kết luận; KHÔNG tự đặt cách dùng riêng (sau ăn/không dùng lúc đói...).")

BF_ACTION = "Chốt 15/10 (chị Nga): phụ nữ ĐANG CHO CON BÚ KHÔNG dùng bất kỳ sản phẩm nào của Sâm Thái Minh → câu chuẩn scripts_approved.breastfeeding; KHÔNG gợi ý sản phẩm khác cho mẹ; có thể mời mua làm quà cho người thân."
ANTIBIO = "Dùng cách thuốc khoảng 2 giờ (chốt 15/10: kháng sinh và thuốc tây nói chung đều cách khoảng 2 giờ)."
AORTIC = "Chốt 15/10: khuyên hỏi ý kiến bác sĩ điều trị trước; bác sĩ cho phép thì mua dùng được (không cần chuyển chuyên viên)."
INSOMNIA = "Dùng buổi sáng/trưa, tránh buổi tối (chốt 15/10, như Hồng sâm lát)."
DL_BP = "Chốt 15/10 (anh Huy): dùng được khi đang dùng thuốc và huyết áp đã ổn định; khuyên hỏi thêm ý kiến bác sĩ điều trị. Liều thường." + MEDS_NOTE
PP_HSMO = A("postpartum_lt6m", "Mẹ sau sinh KHÔNG cho con bú", "Chốt 15/10 (chị Nga): DÙNG ĐƯỢC NGAY để bồi bổ, không cần đợi 6 tháng; liều thường. Mẹ đang cho con bú → không dùng (flag breastfeeding).")
C = {}
C["hsvn_lat"] = {"absolute": [A("pregnant", "Phụ nữ có thai", "Không dùng Hồng sâm lát."),
  A("breastfeeding", "Phụ nữ đang cho con bú", BF_ACTION),
  A("postpartum_lt6m", "Mẹ sau sinh KHÔNG cho con bú (flag giữ tên cũ)", "Chốt 15/10: không dùng Hồng sâm lát → gợi ý Nước Hồng sâm mật ong (chai/túi), dùng được ngay không cần đợi 6 tháng. Mẹ đang cho con bú → flag breastfeeding (không dùng sản phẩm nào)."),
  A("child_under6", "Trẻ dưới 6 tuổi", "Không dùng."),
 ],
 "caution": [A("child_6_11", "Trẻ 6–11 tuổi", "Dùng 1/2 gói/ngày."),
  A("diabetes", "Tiểu đường", "Dùng được: 1 gói/ngày chia 2 lần — sáng 1/2 gói trước ăn sáng 30 phút, trưa 1/2 gói trước ăn trưa 30 phút. KHÔNG nói cất tủ lạnh/để dành hôm sau."),
  A("anticoagulant_ge6m", "Đang dùng thuốc chống đông từ 6 tháng trở lên", "Dùng 1/2 gói/ngày trước ăn 30 phút (chốt 14/10: sức khỏe ổn định, dùng thuốc chống đông từ 6 tháng → dùng được, không cần chuyển chuyên viên; khuyên duy trì thuốc chống đông theo bác sĩ)."),
  A("stent_lt6m", "Mới đặt stent tim mạch + dùng thuốc chống đông DƯỚI 6 tháng", "Chốt 16/10 (chị Nga): khuyên tham khảo ý kiến bác sĩ điều trị trước khi dùng (không tự khẳng định dùng được)."),
  A("stent_6_12m", "Đặt stent tim mạch + dùng thuốc chống đông thường xuyên từ 6 tháng đến dưới 1 năm", "Chốt 16/10 (chị Nga): dùng được — 1/2 gói/ngày; khuyên duy trì thuốc chống đông theo bác sĩ."),
  A("stent_ge12m", "Đặt stent tim mạch + dùng thuốc chống đông thường xuyên từ 1 năm trở lên", "Chốt 16/10 (chị Nga): dùng được — 1/2 gói/ngày; khuyên duy trì thuốc chống đông theo bác sĩ."),
  A("anticoagulant_lt6m", "Đang dùng thuốc chống đông dưới 6 tháng (vd mới tai biến)", "Chốt 13/10: KHÔNG tự tư vấn → câu chuẩn disease_no_guidance + [HANDOFF: thuốc chống đông dưới 6 tháng | SĐT | 3]."),
  A("antibiotic", "Đang dùng kháng sinh", ANTIBIO), ULCER,
  A("kidney_transplant_recent", "Mới ghép thận/ghép tạng", "Chốt 16/10 (chị Nga sửa bảng an toàn): KHÔNG tự tư vấn → câu chuẩn disease_no_guidance, xin SĐT + [HANDOFF: mới ghép thận | SĐT | 3].")] + BP_CAU + EXTRA_CAU + [
  A("kidney_failure_1_2", "Suy thận độ 1–2", "Dùng được bình thường (chốt 13/10), nên tham khảo ý kiến bác sĩ trước."),
  A("kidney_failure_3_4", "Suy thận độ 3–4", "Chốt 16/10 (chị Nga): CÓ THỂ DÙNG nhưng PHẢI hỏi ý kiến bác sĩ điều trị trước, bác sĩ đồng ý thì dùng. KHÔNG nói 'không dùng được'."),
  A("thalassemia", "Thalassemia (tan máu bẩm sinh)", "Thể nhẹ: 1/2 gói/ngày và theo dõi. Thể nặng phải truyền máu: hỏi bác sĩ trước."),
  A("aortic_aneurysm", "Phình động mạch chủ chưa đặt stent", AORTIC + " Nếu bác sĩ cho phép: bệnh nhẹ chưa dùng thuốc 1 gói/ngày buổi sáng; bệnh nặng đang dùng thuốc 1/2 gói/ngày buổi sáng."),
  A("insomnia", "Khó ngủ", "Dùng buổi sáng/trưa, tránh buổi tối.")]}
C["hsmo_chai"] = {"absolute": [A("pregnant", "Phụ nữ có thai", "Không dùng."), A("child_under3", "Trẻ dưới 3 tuổi", "Không dùng.")],
 "caution": [PP_HSMO, A("diabetes", "Tiểu đường", "Dùng được: 5ml/ngày + 100ml nước ấm 60°C, sáng sớm trước ăn 30 phút, lúc đường huyết đang ổn định. Khách nói kiêng mật ong vẫn tư vấn đúng liều này, KHÔNG tự chuyển sang Long Sâm/Dương Sâm.")] + BP_CAU + EXTRA_CAU + [ULCER]}
C["hsmo_tui"] = {"absolute": [A("pregnant", "Phụ nữ có thai", "Không dùng."), A("child_under3", "Trẻ dưới 3 tuổi", "Không dùng.")],
 "caution": [PP_HSMO, A("diabetes", "Tiểu đường", "Dùng được: 1 túi pha 100ml nước ấm 60°C, sáng sớm trước ăn sáng 30 phút, lúc đường huyết đang ổn định. Khách nói kiêng mật ong vẫn tư vấn đúng liều này, KHÔNG tự chuyển sang Long Sâm/Dương Sâm.")] + BP_CAU + EXTRA_CAU + [ULCER]}
# Chốt 14/10 (chị Nga, bản duyệt não): Dương Sâm, Long Sâm — bảng an toàn mới.
OK_DL = [A("diabetes", "Tiểu đường", "Dùng được, liều thường."),
  A("hypertension", "Huyết áp cao", DL_BP),
  A("hypotension", "Huyết áp thấp", DL_BP),
  A("bp_uncontrolled", "Huyết áp chưa ổn định", "Dùng được (chốt 14/10), liều thường." + MEDS_NOTE),
  A("cancer_treatment", "Người bệnh ung thư đang điều trị", "Dùng được (chốt 14/10). Khuyên duy trì phác đồ bác sĩ (maintain_meds, 1 lần)."),
  A("stroke_history", "Tiền sử tai biến không do xuất huyết", "Dùng được (chốt 14/10)."),
  A("anticoagulant_ge6m", "Đang dùng thuốc chống đông từ 6 tháng", "Dùng được (chốt 14/10); khuyên duy trì thuốc chống đông theo bác sĩ."),
  A("rheumatoid_arthritis", "Viêm khớp dạng thấp", "Dùng được."),
  A("thyroid", "Bệnh tuyến giáp", "Dùng được."),
  A("antibiotic", "Đang dùng kháng sinh", ANTIBIO),
  A("thalassemia", "Thalassemia", "Dùng được."),
  A("stent_lt6m", "Mới đặt stent tim mạch + dùng thuốc chống đông dưới 6 tháng", "Chốt 16/10 (chị Nga, Dương Sâm/Long Sâm: mốc 1 NĂM): khuyên tham khảo ý kiến bác sĩ điều trị trước khi dùng."),
  A("stent_6_12m", "Đặt stent + thuốc chống đông từ 6 tháng đến DƯỚI 1 năm", "Chốt 16/10 (chị Nga, Dương Sâm/Long Sâm: mốc 1 NĂM): chưa đủ 1 năm → khuyên tham khảo ý kiến bác sĩ điều trị trước khi dùng."),
  A("stent_ge12m", "Đặt stent + dùng thuốc chống đông thường xuyên TỪ 1 NĂM trở lên", "Chốt 16/10 (chị Nga): dùng được — 1 ngày 1 viên; khuyên duy trì thuốc chống đông theo bác sĩ."),
  A("aortic_aneurysm", "Phình động mạch chủ", AORTIC),
  A("insomnia", "Khó ngủ / mất ngủ", INSOMNIA),
  A("kidney_failure_1_2", "Suy thận độ 1–2", "Dùng được.")]
NO_PREG = [A("pregnant", "Phụ nữ có thai", "Không dùng."), A("breastfeeding", "Phụ nữ đang cho con bú", BF_ACTION),
  A("postpartum_lt6m", "Mẹ sau sinh KHÔNG cho con bú", "Không dùng sản phẩm này; gợi ý Nước Hồng sâm mật ong (dùng được ngay).")]
C["duong_sam"] = {"absolute": [A("under18", "Dưới 18 tuổi", "Không dùng (dành cho nam giới từ đủ 18 tuổi)."),
  A("kidney_failure_acute", "Suy thận CẤP", "Duyệt 21/10 (chị Nga): suy thận cấp KHÔNG dùng Dương Sâm Linh Đan. (Suy thận mạn độ 1–2 dùng được; mạn độ 3–4 hỏi bác sĩ đang điều trị trực tiếp.)")] + NO_PREG,
 "caution": [A("female", "Người dùng là nữ", "Sản phẩm dành cho nam giới trưởng thành — tư vấn sản phẩm khác phù hợp.")]
   + [(A("hypertension", "Huyết áp cao", "Chốt 16/10 (chị Nga sửa bảng an toàn): hỏi chỉ số huyết áp gần nhất. Từ 150 trở xuống → dùng được, liều thường." + MEDS_NOTE + " Trên 150 → KHÔNG tự tư vấn: câu chuẩn disease_no_guidance, xin SĐT + [HANDOFF: Dương Sâm - huyết áp trên 150 | SĐT | 3].") if a["key"] == "hypertension" else (A("hypotension", "Huyết áp thấp", "Dùng được (chốt 16/10, chị Nga), liều thường." + MEDS_NOTE) if a["key"] == "hypotension" else a)) if a["key"] != "bp_uncontrolled" else A("bp_uncontrolled", "Huyết áp chưa ổn định", "Chốt 14/10: hỏi chỉ số huyết áp gần nhất. Từ 150 trở xuống → dùng được, liều thường." + MEDS_NOTE + " Trên 150 → KHÔNG tự tư vấn: câu chuẩn disease_no_guidance, xin SĐT + [HANDOFF: Dương Sâm - huyết áp trên 150 | SĐT | 3].") for a in OK_DL]}
C["tra_nguyen_la"] = {"absolute": [A("child_under12", "Trẻ dưới 12 tuổi", "Không dùng (sản phẩm dành cho người từ 12 tuổi).")], "caution": []}
C["tra_1700"] = {"absolute": [A("pregnant", "Phụ nữ có thai", "Không dùng (có nhân sâm, đinh lăng)."),
  A("breastfeeding", "Phụ nữ đang cho con bú", BF_ACTION)],
 "caution": [A("child_any", "Trẻ em", "Dùng được theo hướng dẫn pha trên vỏ hộp.")]}
C["ruou_sam"] = {"absolute": [A("under18", "Dưới 18 tuổi", "Không bán, không tư vấn."),
  A("pregnant", "Phụ nữ có thai", "Không dùng đồ uống có cồn."),
  A("breastfeeding", "Phụ nữ đang cho con bú", "Không dùng đồ uống có cồn.")],
 "caution": [A("driving", "Sắp lái xe", "Không uống trước khi lái xe.")],
 "note": "Chống chỉ định đã chốt 23/09: dưới 18 tuổi, phụ nữ có thai, phụ nữ cho con bú."}
C["long_sam"] = {"absolute": NO_PREG + [A(k, "Trẻ em", "Không dùng (chốt 14/10).") for k in ("child_under3", "child_under6", "child_6_11", "child_under12", "child_any", "under18")],
 "caution": [a if a["key"] != "bp_uncontrolled" else A("bp_uncontrolled", "Huyết áp chưa ổn định", "Chốt 15/10 (anh Huy): Long Sâm kiêng kỵ hơn Dương Sâm → KHÔNG tự tư vấn: khuyên dùng thuốc cho huyết áp ổn định, hỏi ý kiến bác sĩ điều trị; câu chuẩn disease_no_guidance, xin SĐT + [HANDOFF: Long Sâm - huyết áp chưa ổn định | SĐT | 3].") for a in OK_DL]}
C["tam_sam_dan"] = {"absolute": [A("pregnant", "Phụ nữ có thai", "Không dùng."), A("breastfeeding", "Phụ nữ đang cho con bú", "Không dùng."),
  A("child_under12", "Trẻ dưới 12 tuổi", "Không dùng.")],
 "caution": [A("anticoagulant_ge6m", "Đang dùng thuốc chống đông", "Có Đan sâm — KHÔNG tự khẳng định dùng chung; xin SĐT + [HANDOFF: Tam Sâm Đan + thuốc chống đông | SĐT | 3]."),
  A("anticoagulant_lt6m", "Đang dùng thuốc chống đông", "Có Đan sâm — KHÔNG tự khẳng định dùng chung; xin SĐT + [HANDOFF: Tam Sâm Đan + thuốc chống đông | SĐT | 3].")]}
C["dong_trung"] = {"absolute": [A("pregnant", "Phụ nữ có thai", "Không dùng."), A("breastfeeding", "Phụ nữ đang cho con bú", "Không dùng."),
  A("child_under6", "Trẻ dưới 6 tuổi", "Không dùng (chốt 23/09: dùng được cho trẻ từ 6 tuổi).")],
 "caution": [A("child_6_11", "Trẻ 6–11 tuổi", "Dùng được (từ 6 tuổi). Tài liệu CHƯA có liều riêng cho trẻ — KHÔNG tự nêu liều; chuyển chuyên viên tư vấn liều: xin SĐT + [HANDOFF: liều Đông trùng cho trẻ | SĐT | 3]."),
  A("child_under12", "Trẻ dưới 12 tuổi (chưa rõ tuổi cụ thể)", "Hỏi tuổi cụ thể: dưới 6 tuổi không dùng; từ 6 tuổi dùng được nhưng liều do chuyên viên tư vấn."),
  A("child_any", "Trẻ em (chưa rõ tuổi)", "Hỏi tuổi cụ thể: dưới 6 tuổi không dùng; từ 6 tuổi dùng được nhưng liều do chuyên viên tư vấn.")]}
C["sam_tuoi"] = {"absolute": [], "caution": []}
# Duyệt 21/10 (chị Nga, bộ não Dương Sâm v0.2.1): thuốc chống đông (có hay không đặt stent) mốc 1 NĂM; suy thận mạn 3–4 hỏi bác sĩ; xơ gan/viêm gan dùng được
C["duong_sam"]["caution"] = [a if a["key"] != "anticoagulant_ge6m" else A("anticoagulant_ge6m", "Đang dùng thuốc chống đông",
    "Duyệt 21/10 (chị Nga): hỏi dùng thuốc chống đông được bao lâu. DƯỚI 1 năm → khuyên tham khảo ý kiến bác sĩ điều trị trước khi dùng; TỪ 1 năm trở lên → dùng được 1 viên/ngày; khuyên duy trì thuốc chống đông theo bác sĩ.")
    for a in C["duong_sam"]["caution"]] + [
  A("anticoagulant_lt6m", "Đang dùng thuốc chống đông dưới 6 tháng", "Duyệt 21/10: chưa đủ 1 năm → khuyên tham khảo ý kiến bác sĩ điều trị trước khi dùng."),
  A("kidney_failure_3_4", "Suy thận mạn độ 3–4", "Duyệt 21/10: hỏi ý kiến bác sĩ đang điều trị trực tiếp trước khi dùng."),
  A("liver_disease", "Xơ gan / viêm gan virus", "Duyệt 21/10: dùng được để hỗ trợ sức khỏe; kết hợp ăn uống hợp lý, hạn chế rượu bia.")]
# Chốt 13/10 (chị Nga): người ung thư đang điều trị (hóa trị, xạ trị...) DÙNG ĐƯỢC Hồng sâm Thái Minh.
for pid in ("hsvn_lat", "hsmo_chai", "hsmo_tui"):
    C[pid]["caution"].append(A("cancer_treatment", "Người bệnh ung thư (lành tính, ác tính, đang hóa trị/xạ trị/điều trị)",
        "Dùng được (chốt 13/10) — hồng sâm hỗ trợ bồi bổ sức khoẻ, hỗ trợ tăng cường miễn dịch cho người đang điều trị (câu chuẩn scripts_approved.disease_question). Liều thường. Khuyên duy trì phác đồ bác sĩ điều trị, dùng kết hợp sâm để bồi bổ (maintain_meds, 1 lần)."))
for pid in ("tra_1700", "ruou_sam", "tam_sam_dan", "dong_trung"):
    C[pid]["absolute"].append(A("postpartum_lt6m", "Mẹ sau sinh KHÔNG cho con bú", "Không dùng sản phẩm này; gợi ý Nước Hồng sâm mật ong (dùng được ngay)."))
# Nước Hồng sâm (chai, túi): chốt 14/10
for pid in ("hsmo_chai", "hsmo_tui"):
    C[pid]["caution"] += [A("kidney_failure_3_4", "Suy thận độ 3–4", "Chốt 16/10 (chị Nga): CÓ THỂ DÙNG nhưng PHẢI hỏi ý kiến bác sĩ điều trị trước, bác sĩ đồng ý thì dùng. KHÔNG nói 'không dùng được'.")]
    C[pid]["caution"] += [A("anticoagulant_ge6m", "Đang dùng thuốc chống đông từ 6 tháng", "Dùng được (chốt 14/10), liều thường; khuyên duy trì thuốc chống đông theo bác sĩ."),
      A("stent_lt6m", "Mới đặt stent tim mạch + dùng thuốc chống đông DƯỚI 6 tháng", "Chốt 16/10 (chị Nga): khuyên tham khảo ý kiến bác sĩ điều trị trước khi dùng (không tự khẳng định dùng được)."),
      A("stent_6_12m", "Đặt stent + thuốc chống đông từ 6 tháng đến dưới 1 năm", "Chốt 16/10 (chị Nga, giống Hồng sâm lát): dùng được, liều thường; khuyên duy trì thuốc chống đông theo bác sĩ."),
      A("stent_ge12m", "Đặt stent + thuốc chống đông từ 1 năm trở lên", "Chốt 16/10 (chị Nga, giống Hồng sâm lát): dùng được, liều thường; khuyên duy trì thuốc chống đông theo bác sĩ."),
      A("antibiotic", "Đang dùng kháng sinh", ANTIBIO),
      A("thalassemia", "Thalassemia", "Thể nhẹ: liều thường (1 túi hoặc 10ml/ngày); thể nặng phải truyền máu: hỏi bác sĩ trước."),
      A("aortic_aneurysm", "Phình động mạch chủ", AORTIC),
      A("insomnia", "Khó ngủ / mất ngủ", INSOMNIA)]
for pid in C:
    if pid not in ("hsvn_lat", "hsmo_chai", "hsmo_tui", "duong_sam", "long_sam"):
        C[pid]["caution"].append(A("cancer_treatment", "Người bệnh ung thư đang điều trị",
            "Tài liệu chưa có hướng dẫn cho sản phẩm này → câu chuẩn disease_no_guidance, xin SĐT + [HANDOFF: ung thư đang điều trị hỏi sản phẩm khác Hồng sâm | SĐT | 3]. Có thể gợi ý Hồng sâm Thái Minh (dùng được)."))
# Chốt 13/10 (chị Nga): tai biến/đột quỵ do XUẤT HUYẾT (xuất huyết não, chảy máu não) → chuyển chuyên viên, mọi sản phẩm.
for pid in C:
    C[pid]["caution"].append(A("stroke_hemorrhagic", "Tai biến/đột quỵ do xuất huyết (xuất huyết não, chảy máu não)",
        "Chốt 13/10: KHÔNG tự tư vấn → câu chuẩn disease_no_guidance + [HANDOFF: tai biến do xuất huyết | SĐT | 3]."))
for pid in C:
    if not any(a["key"] == "breastfeeding" for a in C[pid]["absolute"]):
        C[pid]["absolute"].append(A("breastfeeding", "Phụ nữ đang cho con bú", BF_ACTION))
for pid in C:
    C[pid]["absolute"] = G_ABS + C[pid]["absolute"]
    C[pid]["caution"] = C[pid]["caution"] + G_CAU
ALL_FLAGS = ["ingredient_allergy", "adr_severe", "adr_mild", "prescription_meds_unlisted", "serious_condition", "pregnant", "breastfeeding",
  "child_under3", "child_under6", "child_6_11", "child_under12", "child_any", "under18", "diabetes", "hypertension", "hypotension", "bp_uncontrolled", "cancer_treatment",
  "anticoagulant_ge6m", "anticoagulant_lt6m", "antibiotic", "kidney_transplant_recent", "kidney_failure_1_2", "kidney_failure_3_4", "stomach_ulcer", "stent_lt6m", "stent_6_12m", "stent_ge12m", "thalassemia", "postpartum_lt6m",
  "rheumatoid_arthritis", "thyroid", "stroke_history", "stroke_hemorrhagic",
  "aortic_aneurysm", "insomnia", "female", "driving", "kidney_failure_acute", "liver_disease"]

compliance = {
 "product_class": "Hồng sâm lát, Hồng sâm nước, Trà, Rượu là THỰC PHẨM thường; Dương Sâm, Long Sâm, Tam Sâm Đan, Đông trùng hạ thảo là THỰC PHẨM BẢO VỆ SỨC KHỎE. Tất cả đều KHÔNG phải thuốc (dữ kiện nội bộ — chốt 13/10: KHÔNG tự nói câu 'không phải thuốc' với khách).",
 "all_flags": ALL_FLAGS, "unknown_action": UNKNOWN_ACTION,
 "words_allowed": ["hỗ trợ bồi bổ", "hỗ trợ tăng sức đề kháng", "hỗ trợ cải thiện", "hỗ trợ giảm mệt mỏi", "giúp ngủ ngon hơn", "nhiều khách hàng ghi nhận", "hiệu quả tùy cơ địa", "người huyết áp cao hay huyết áp thấp đều dùng được", "hỗ trợ ổn định huyết áp"],
 "words_banned": ["chữa khỏi", "khỏi hẳn", "dứt điểm", "điều trị", "đặc trị", "trị bệnh", "thay thế thuốc", "tốt hơn thuốc", "không cần uống thuốc",
   "chữa ung thư", "diệt tế bào ung thư", "đẩy lùi ung thư", "khỏi ung thư", "chữa tiểu đường", "hết tiểu đường", "chữa huyết áp", "chữa đột quỵ",
   "không có tác dụng phụ", "không gây tác dụng phụ", "an toàn tuyệt đối", "không ảnh hưởng đến thuốc", "ai dùng cũng được", "100% hiệu quả", "hiệu quả 100%", "cam kết khỏi", "cam kết khỏi bệnh", "trị dứt điểm", "khỏi hoàn toàn",
   "thần dược", "kỳ diệu", "tức thì", "ngay lập tức", "tốt nhất thị trường", "số 1", "số một",
   "gấp 25 lần", "gấp 3 lần sâm Hàn", "gấp khoảng 3 lần", "toàn bộ sâm do Thái Minh tự trồng", "100% sâm tự trồng", "toàn bộ sâm trồng ở Sìn Hồ", "toàn bộ sâm từ Sìn Hồ", "100% sâm Sìn Hồ", "minh bạch từ vườn đến nhà máy", "tiết sữa", "lợi sữa", "chiếm tới 50%", "chống khối u",
   "tính ra mỗi ngày chỉ", "mỗi ngày chỉ mất", "chỉ từ 28k/ngày",
   "em là trợ lý AI", "tôi là AI", "mô hình ngôn ngữ"],
 "disease_claim_rule": "Chốt 23/09 + 13/10 (chị Nga): ĐƯỢC nói về ung thư, đột quỵ, đường huyết, huyết áp, mỡ máu, xơ vữa NHƯNG (chốt 15/10: KHÔNG nói tiết sữa/lợi sữa — cho con bú không dùng sản phẩm) BẮT BUỘC dạng 'hỗ trợ ...' đúng như benefits/evidence_rule của sản phẩm. KHÔNG tự nói câu 'sản phẩm không phải thuốc, không thay thế thuốc điều trị'. CHỈ KHI khách nói đang dùng thuốc tây chữa bệnh nền → khuyên duy trì thuốc bác sĩ kê, dùng kèm sản phẩm Sâm để bồi bổ (scripts_approved.maintain_meds, ĐÚNG 1 LẦN). Không bao giờ bảo khách giảm/bỏ thuốc; khách hỏi 'có thay được thuốc / bỏ thuốc được không' → trả lời thật: không thay thuốc, vẫn dùng thuốc bác sĩ kê. Chuyến thăm của Thủ tướng: CHỈ trả lời khi khách tự hỏi (scripts_approved.pm_visit), không chủ động nhắc để quảng bá.",
 "price_talk_rules": ["Được trả lời phép tính khách hỏi (tổng đơn, giá mỗi hộp trong combo). Combo KHÔNG giảm giá — tặng quà + miễn phí ship: nói thẳng khi khách hỏi.",
   "CẤM chủ động quy đổi giá theo ngày/gói khi khách không hỏi.",
   "CẤM tự báo tổng chi phí liệu trình khi khách không hỏi.",
   "Khách chê giá cao (brief 25/09) → LẦN 1: nêu GIÁ TRỊ theo scripts_approved.price_why (sâm Việt Nam quý, có hoạt chất MR2 mà sâm Hàn Quốc không có; công trình chuyển giao từ VIGH; Hồng sâm dễ hấp thu, dễ bảo quản hơn sâm tươi; sâm có nguồn gốc rõ ràng, được kiểm soát chặt chẽ chất lượng đầu vào; thuộc phân khúc cao cấp của Dược phẩm Thái Minh hơn 15 năm; thường sau 2 hộp bắt đầu cảm nhận) + ưu đãi đang áp dụng. Riêng Hồng sâm lát: khách chê đắt/chưa đủ tiền mới được báo quà mốc 1 hộp (tặng 1 hộp Trà sâm). LẦN 2 (vẫn chê đắt/chưa đủ ngân sách) → chủ động giới thiệu Nước Hồng sâm Thái Minh mật ong (báo giá + CTKM luôn) là lựa chọn kinh tế hơn. KHÔNG gợi ý trà. KHÔNG ép."],
 "products": C,
}

# ---------------- khuyến mại (bảng 'Chương trình khuyến mại', CHỈ khách mới — chốt 23/09) ----------------
def R(sku, q, gift, ship_free, condition=None, label=None):
    d = {"if_sku": sku, "min_qty": q, "gift": gift, "freeship": ship_free}
    if condition:
        d["condition"] = condition      # price_objection: chỉ áp khi khách chê đắt / chưa đủ tiền
    if label:
        d["label"] = label
    return d
RULES = [
 # Chốt 25/09 (brief chị Nga): bảng quà Hồng sâm lát MỚI — thay bảng Excel cũ. Freeship giữ như bảng Excel (brief không nhắc).
 R("hsvn-lat-14", 1, "1 hộp Trà sâm 1700 loại 10 gói (trị giá 120.000đ)", True, condition="price_objection"),   # CHỈ khi khách chê đắt / chưa đủ tiền
 R("hsvn-lat-14", 2, "1 hộp Trà sâm 1700 loại 20 gói (trị giá 190.000đ)", True, label="Combo 1 tháng"),
 R("hsvn-lat-14", 4, "2 hộp Trà sâm 1700 loại 20 gói (trị giá 380.000đ)", True, label="Combo 2 tháng"),
 R("hsvn-lat-14", 6, "5 hộp Trà sâm 1700 loại 10 gói", True, label="Combo 3 tháng"),
 R("hsvn-lat-14", 10, "1 chai Nước Hồng Sâm Mật Ong (trị giá 550.000đ)", True),
 R("hsvn-lat-14", 15, "1 hộp Hồng sâm Việt Nam Thái Minh cùng loại + 1 hộp Trà sâm 1700 (20 gói)", True),
 R("hsmo-chai", 1, "", False),
 R("hsmo-chai", 2, "1 hộp Trà sâm 1700 (10 gói)", True),   # chốt 23/09: miễn phí ship
 R("hsmo-chai", 3, "2 hộp Trà sâm 1700 (10 gói)", True),
 R("hsmo-chai", 4, "3 hộp Trà sâm 1700 (10 gói)", True),
 R("hsmo-chai", 6, "5 hộp Trà sâm 1700 (10 gói)", True),
 R("hsmo-chai", 10, "1 chai nước Hồng sâm mật ong + 3 hộp Trà sâm 1700 (10 gói)", True),
 R("hsmo-tui", 1, "", False),   # chốt 14/10: mua 1 hộp không có quà
 R("hsmo-tui", 2, "1 hộp Trà sâm 1700 (10 gói)", True),
 R("hsmo-tui", 3, "2 hộp Trà sâm 1700 (10 gói)", True),
 R("hsmo-tui", 4, "3 hộp Trà sâm 1700 (10 gói)", True),
 R("hsmo-tui", 6, "5 hộp Trà sâm 1700 (10 gói)", True),
 R("hsmo-tui", 10, "1 hộp nước Hồng sâm dạng túi cùng loại + 3 hộp Trà sâm 1700 (10 gói)", True),
 R("hsmo-tui-10", 1, "", False),   # chốt 14/10: hộp nhỏ 10 túi — chưa có quà; ship như Hồng sâm dạng nước
 R("hsmo-tui-10", 2, "", True),
 R("duongsam-10", 1, "", True),
 R("duongsam-10", 2, "1 hộp Trà sâm 1700 (10 gói)", True),
 R("duongsam-10", 3, "2 hộp Trà sâm 1700 (10 gói)", True, label="Liệu trình 1 tháng"),
 R("duongsam-10", 6, "1 chai Nước Hồng sâm mật ong (hoặc đổi sang 2 hộp Bổ Gan Thái Minh + 1 hộp Trà sâm 1700 loại 10 gói)", True, label="Liệu trình 2 tháng"),   # bảng CTKM DSLĐ 01/07–31/12/2026 (chị Nga 19/10)
 R("duongsam-10", 9, "2 chai nước Hồng sâm mật ong", True, label="Liệu trình 3 tháng"),
 R("longsam-6", 1, "1 hộp Trà sâm 1700 (10 gói)", True),
 R("longsam-6", 3, "2 hộp Trà sâm 1700 (10 gói)", True),
 R("longsam-6", 6, "1 chai nước Hồng sâm mật ong", True),
 R("longsam-6", 10, "1 hộp Long Sâm Linh Đan (6 viên)", True),
 R("longsam-30", 1, "1 chai nước Hồng sâm mật ong", True),
 R("longsam-30", 3, "1 hộp Long Sâm Linh Đan (6 viên) + 1 chai nước Hồng sâm mật ong", True),
 R("tra-nguyenla-100", 1, "2 lọ dầu nóng Khương Thảo Đan", True),
 R("tra-nguyenla-100", 5, "1 hộp Trà sâm Lai Châu nguyên lá (100g)", True),
 R("tra1700-20", 1, "", False),
 R("tra1700-20", 5, "1 hộp Trà sâm 1700 (20 gói)", True),
 R("tra1700-10", 1, "", False),
 R("tra1700-10", 5, "1 hộp Trà sâm 1700 (10 gói)", True),
 R("tamsamdan-30", 1, "", False),
 R("tamsamdan-30", 2, "1 hộp Trà sâm 1700 (10 gói)", True),
 R("tamsamdan-30", 3, "2 hộp Trà sâm 1700 (10 gói)", True),
 R("tamsamdan-30", 6, "1 hộp Tam Sâm Đan 30 viên", True),
 R("dongtrung-30", 1, "", False),
 R("dongtrung-30", 2, "2 hộp Trà sâm 1700 (10 gói)", True),
 R("dongtrung-30", 4, "1 hộp Đông trùng hạ thảo 30 viên", True),
]
# v0.1.15 (13/10): MỌI câu có giá/quà Hồng sâm lát sinh từ đây — đổi giá/quà chỉ sửa P["hsvn_lat"] và RULES.
def vnd(n): return f"{n:,.0f}đ".replace(",", ".")
LAT_PRICE = P["hsvn_lat"]["packages"][0]["price_retail"]
LAT_PRICE_OLD = 1320000        # giá trước lần điều chỉnh (để trả lời "sao tăng giá")
def lat_rule(q, cond=None):
    return next(r for r in RULES if r["if_sku"] == "hsvn-lat-14" and r["min_qty"] == q and r.get("condition") == cond)
def combo_line(q):
    r = lat_rule(q)
    return f"{r['label']} ({q} hộp): {vnd(LAT_PRICE * q)} – tặng {r['gift']}"
LAT_COMBOS = [r["min_qty"] for r in RULES if r["if_sku"] == "hsvn-lat-14" and r.get("label")]
COMBO_TXT = " / ".join(f"'🎁 {combo_line(q)}'" for q in LAT_COMBOS)
# v0.1.71 (25/10, chị Nga): đa dạng cách trình bày phần combo — 4 kiểu, giá/quà vẫn sinh từ bảng khuyến mại
def _combo_style(q, k):
    r = lat_rule(q)
    if k == 2:
        return f"✅ {r['label']} ({q} hộp) – {vnd(LAT_PRICE * q)} – tặng {r['gift']}"
    if k == 3:
        return f"🎁 {r['label']} ({q} hộp) giá {vnd(LAT_PRICE * q)}: tặng ngay {r['gift']}"
    if k == 4:
        return f"🌿 {r['label']} ({q} hộp): {vnd(LAT_PRICE * q)}, tặng kèm {r['gift']}"
    # v0.1.87 (26/10, chị Nga): thêm 4 kiểu — giá/quà vẫn sinh từ bảng khuyến mại
    _note = {2: "dùng thử cảm nhận", 4: "dùng đều", 6: "đủ liệu trình cơ bản"}.get(q, "")
    if k == 5:
        return f"{'⭐' if q == 6 else '▫️'} {r['label']} ({q} hộp): {vnd(LAT_PRICE * q)} – tặng {r['gift']}"
    if k == 6:
        return f"• {r['label']} ({q} hộp) → {vnd(LAT_PRICE * q)}, tặng {r['gift']}"
    if k == 7:
        return f"🎁 {r['label']} ({q} hộp) – {_note}: {vnd(LAT_PRICE * q)}, tặng {r['gift']}"
    if k == 8:
        return f"{ {2: '1️⃣', 4: '2️⃣', 6: '3️⃣'}.get(q, '•') } {r['label']} ({q} hộp): {vnd(LAT_PRICE * q)} – quà tặng: {r['gift']}"
    return f"🎁 {combo_line(q)}"
COMBO_STYLES = [
    ("Chương trình tri ân khách hàng mới:", 1),
    ("Hiện bên em đang có ưu đãi quà tặng cho khách mới theo liệu trình ạ:", 2),
    ("Anh/chị mua theo combo sẽ được tặng thêm quà ạ:", 3),
    ("Ưu đãi dành riêng cho khách hàng mới, áp dụng đến hết 31/12/2026:", 4),
    ("Bên em có 3 gói liệu trình kèm quà, combo 3 tháng được tặng nhiều quà nhất ạ:", 5),
    ("Mua theo combo anh/chị được tặng thêm Trà sâm ạ:", 6),
    ("Anh/chị chọn gói theo nhu cầu nhé ạ:", 7),
    ("Ưu đãi khách mới đang áp dụng theo từng liệu trình ạ:", 8),
]
COMBO_STYLE_TXT = " || ".join(f"KIỂU {i + 1}: '{h}' + " + " / ".join(f"'{_combo_style(q, k)}'"
                                                                    for q in (list(reversed(LAT_COMBOS)) if k == 5 else LAT_COMBOS))
                              for i, (h, k) in enumerate(COMBO_STYLES))
OBJ_GIFT = lat_rule(1, "price_objection")["gift"]

# Chốt 14/10 (chị Nga): CTKM dành riêng cho KHÁCH CŨ đã từng đặt mua — hiện có bảng cho Hồng sâm lát hộp 14 gói.
RET_RULES = [
 R("hsvn-lat-14", 1, "1 lọ dầu nóng Khương Thảo Đan 10ml (trị giá 55.000đ) hoặc 1 hộp Trà sâm 1700 loại 10 gói", True),
 R("hsvn-lat-14", 2, "2 hộp viên ngậm Heviho + 1 lọ dầu nóng Khương Thảo Đan để xoa bóp", True),
 R("hsvn-lat-14", 3, "4 hộp viên ngậm Heviho", True),
 R("hsvn-lat-14", 5, "8 hộp viên ngậm Heviho", True),
 R("hsvn-lat-14", 12, "1 hộp Hồng sâm cùng loại + 2 hộp viên ngậm Heviho", True),
 R("hsvn-lat-14", 24, "2 hộp Hồng sâm cùng loại + 1 chai Nước Hồng sâm mật ong", True),
 # Chốt 19/10 (chị Nga): Dương Sâm Linh Đan — bảng CTKM 01/07–31/12/2026 (mọi nhãn). Mốc riêng khách cũ: 4, 7, 10, 15 hộp
 # (Multi vitamin C đã hết → thay bằng Bổ Gan Thái Minh). Số lượng KHÔNG có mốc khách cũ → quà mốc khách cũ thấp hơn (19/10 15:22, khách không thiệt quà);
 # riêng 2, 3, 6, 9 hộp quà bảng khách mới nhiều hơn → giữ quà khách mới.
 R("duongsam-10", 1, "", True),
 R("duongsam-10", 2, "1 hộp Trà sâm 1700 (10 gói)", True),
 R("duongsam-10", 3, "2 hộp Trà sâm 1700 (10 gói)", True),
 R("duongsam-10", 4, "2 hộp Trà sâm 1700 (10 gói) + 1 hộp Bổ Gan Thái Minh", True),
 R("duongsam-10", 5, "2 hộp Trà sâm 1700 (10 gói) + 1 hộp Bổ Gan Thái Minh", True),   # chốt 19/10 15:22: áp mốc khách cũ thấp hơn, khách không thiệt quà
 R("duongsam-10", 6, "1 chai Nước Hồng sâm mật ong (hoặc đổi sang 2 hộp Bổ Gan Thái Minh + 1 hộp Trà sâm 1700 loại 10 gói)", True),
 R("duongsam-10", 7, "1 chai nước Hồng sâm mật ong + 1 hộp Bổ Gan Thái Minh (30 viên)", True),
 R("duongsam-10", 8, "1 chai nước Hồng sâm mật ong + 1 hộp Bổ Gan Thái Minh (30 viên)", True),
 R("duongsam-10", 9, "2 chai nước Hồng sâm mật ong", True),
 R("duongsam-10", 10, "1 hộp Dương Sâm Linh Đan + 1 hộp Trà sâm 1700 (10 gói)", True),
 R("duongsam-10", 15, "1 hộp Dương Sâm Linh Đan + 1 chai nước Hồng sâm mật ong", True),
]
programs = {
 "new_customer": {"name": "Ưu đãi KHÁCH MỚI (chưa từng mua sản phẩm Sâm Thái Minh) — theo bảng 'Chương trình khuyến mại' (file Sâm Thái Minh 1.xlsx)", "active": True,
   "valid_from": "2026-09-23", "valid_to": "2026-12-31",
   "period_display": "từ 23/09/2026 đến hết 31/12/2026",
   "rules": RULES,
   "tier_rule": "Số lượng nằm GIỮA hai bậc → áp bậc thấp hơn gần nhất (vd lấy 3 hộp Hồng sâm lát → quà bậc 2 hộp; 5 hộp → quà bậc 4 hộp). Dòng có condition=price_objection (Hồng sâm lát 1 hộp tặng 1 hộp Trà sâm 10 gói) CHỈ áp khi khách chê đắt/chưa đủ tiền HOẶC khách CHỦ ĐỘNG hỏi CT tặng trà khi mua 1 hộp (chốt 23/10, chị Nga — CT linh động, KHÔNG tự báo). Vượt bậc cao nhất → quà bậc cao nhất + mời chuyển nhân viên xin thêm ưu đãi (big_order).",
   "freeship_rule": "freeship=true: miễn phí ship. freeship=false: tính phí ship theo shipping. freeship=null: tài liệu để trống → nhân viên xác nhận phí ship khi lên đơn.",
   "note": "Chốt 25/09 (brief): khách hỏi giá → BÁO NGAY giá + liệu trình + các combo quà trong CÙNG 1 tin (gọi là 'Chương trình tri ân khách hàng mới'), KHÔNG cần hỏi khách mới/cũ trước. Khách TỰ nói đã từng mua ĐÚNG sản phẩm này → khách cũ (returning_customer); từng dùng sản phẩm khác → vẫn khách mới (chốt 23/10). CẤM tự suy diễn quà ngoài bảng. Thời hạn chương trình: từ 23/09/2026 đến hết 31/12/2026 (được nói khi khách hỏi hoặc khi cần tạo động lực chốt, không ép). Hết hạn → không hứa quà, chuyển nhân viên báo chương trình mới."},
 "returning_customer": {"name": "Ưu đãi KHÁCH CŨ (đã từng đặt mua sản phẩm Sâm Thái Minh) — bảng chị Nga gửi 14/10", "active": True,
   "period_display": "chương trình tri ân khách hàng thân thiết",
   "rules": RET_RULES,
   "note": "Chốt 23/10 (chị Nga): CHỈ áp bảng này khi khách TỰ nói đã từng dùng/mua ĐÚNG sản phẩm đang muốn mua; từng dùng sản phẩm khác → vẫn báo CTKM khách mới. Chốt 14/10: khách TỰ nói đã từng mua → báo ưu đãi khách cũ (KHÔNG báo combo khách mới). Hồng sâm lát hộp 14 gói và Dương Sâm Linh Đan (chốt 19/10): bot tự báo quà theo bảng và tự chốt đơn (build_order customer_type=returning). Mua 1 hộp: khách chọn 1 trong 2 quà (dầu nóng hoặc Trà sâm). Số lượng nằm giữa hai mốc → áp mốc thấp hơn. Sản phẩm khác chưa có bảng khách cũ → nói có ưu đãi riêng khách thân thiết, xin SĐT để chuyên viên báo + [HANDOFF: khách cũ mua tiếp | SĐT | 2]."},
 "money_back": {"name": "Hoàn tiền / đổi trả", "active": False, "handoff": True,
   "note": "Chốt 23/09: bot KHÔNG trả lời nội dung chính sách đổi trả/hoàn tiền (không hứa, không từ chối, không nêu điều kiện). Khách hỏi hoặc yêu cầu đổi trả → 'Dạ để em chuyển chuyên viên phụ trách hỗ trợ trực tiếp cho anh/chị về việc đổi trả ạ. Anh/chị cho em xin số điện thoại để chuyên viên liên hệ ngay nhé ạ.' + [HANDOFF: đổi trả | SĐT | 2]. Trước khi mua, khách lo hàng không ưng → chỉ nói COD: nhận hàng kiểm tra rồi mới thanh toán."},
 "big_order": {"name": "Đơn vượt bậc combo cao nhất, hoặc đơn Sâm tươi / Rượu hũ nguyên cây", "active": True,
   "note": "KHÔNG tự chế quà, KHÔNG khuyên mua ít hơn. Thu đủ tên/SĐT/địa chỉ/số lượng rồi: 'Đơn của anh/chị em xin thêm chương trình tốt hơn từ bộ phận phụ trách, bên em gọi lại xác nhận sớm ạ.' + [HANDOFF: đơn lớn | SĐT | 2]."},
}
shipping = {"fee_hn_inner": SHIP_HN_INNER, "fee_other": SHIP_OTHER,
 "fee_display": "Hồng sâm dạng nước (chai, túi) mua 1 hộp/chai: Hà Nội nội thành 15.000đ, ngoại thành và tỉnh khác 20.000đ; từ 2 hộp/chai miễn phí. Trà sâm, Tam Sâm Đan, Đông trùng hạ thảo (chốt 14/10): đơn dưới 1.000.000đ phí ship 20.000đ, từ 1.000.000đ miễn phí. Các sản phẩm còn lại (Hồng sâm lát, Dương Sâm, Long Sâm, Rượu, Sâm tươi) miễn phí vận chuyển từ 1 hộp toàn quốc.",
 "threshold_skus": [k["sku"] for pid_, p_ in P.items() for k in p_["packages"] if pid_ in ("tra_1700", "tra_nguyen_la", "tam_sam_dan", "dong_trung")],
 "threshold": 1000000, "threshold_fee": 20000,
 "delivery_time": "Hà Nội 1–2 ngày; tỉnh/thành phố khác 3–4 ngày.",
 "hn_inner_keywords": ["Ba Đình", "Hoàn Kiếm", "Tây Hồ", "Long Biên", "Cầu Giấy", "Đống Đa", "Hai Bà Trưng", "Hoàng Mai", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm", "Hà Đông"],
 "freeship_with_promo": "Theo từng dòng bảng khuyến mại (hầu hết combo từ 2 hộp được miễn phí ship).",
 "cod_note": "Giao hàng COD toàn quốc — nhận hàng KIỂM TRA đúng sản phẩm, bao bì, tem niêm phong, hạn sử dụng rồi mới thanh toán.",
 "free_ship_skus": [k["sku"] for pid_, p_ in P.items() for k in p_["packages"] if pid_ not in ("hsmo_chai", "hsmo_tui", "tra_1700", "tra_nguyen_la", "tam_sam_dan", "dong_trung")],
 "free_ship_note": "Hồng sâm lát, Dương Sâm, Long Sâm, Rượu, Sâm tươi miễn phí vận chuyển từ 1 hộp. Hồng sâm dạng nước: từ 2 hộp/chai miễn phí. Trà, Tam Sâm Đan, Đông trùng: từ 1 triệu miễn phí.",
 "unknown_fee_note": "Sản phẩm/đơn chưa có dòng phí ship trong tài liệu → 'phí vận chuyển nhân viên xác nhận khi gọi lên đơn'."}
pharmacy_policy = {
 "rule": "Sản phẩm có ở một số nhà thuốc nhưng ÍT điểm bán. Khuyến khích đặt qua page để hưởng ưu đãi khách mới + giao tận nhà, hoặc mua trực tiếp tại cửa hàng Sâm Thái Minh 92 Trung Kính, Cầu Giấy, Hà Nội. KHÔNG bịa tên/địa chỉ nhà thuốc. Không nói xấu nhà thuốc.",
 "store_address": "Cửa hàng Sâm Thái Minh: 92 Trung Kính, Cầu Giấy, Hà Nội — mở cửa 8h00–21h00 hằng ngày; mua tại cửa hàng được quà tặng như đặt qua page (chốt 23/10)",
 "store_locator": "https://samthaiminh.com/diem-ban",
 "script_where_buy": "Dạ anh/chị có thể tra điểm bán gần nhất tại https://samthaiminh.com/diem-ban ạ. Anh/chị đặt online ngay tại page thì được giao tận nhà, nhận hàng kiểm tra rồi mới thanh toán và được hưởng ưu đãi tốt nhất ạ. Nếu anh/chị ở Hà Nội cũng có thể ghé cửa hàng Sâm Thái Minh tại 92 Trung Kính, Cầu Giấy ạ.",
 "script_pharmacy_area": "Dạ anh/chị tra điểm bán theo khu vực tại https://samthaiminh.com/diem-ban giúp em nhé ạ. Đặt online tại page thì anh/chị được giao tận nhà và hưởng ưu đãi tốt nhất ạ.",
 "script_program_at_pharmacy": "Dạ chương trình ưu đãi em báo là áp dụng khi anh/chị đặt trực tiếp với công ty qua page/hotline, còn chương trình tại nhà thuốc bên em chưa nắm được ạ.",
 "customer_chose_pharmacy": "Khách đã chọn ra NHÀ THUỐC khác (không phải cửa hàng Sâm Thái Minh) → ủng hộ, chúc mua thuận lợi, KHÔNG mời lại kênh online; chèn thẻ ẩn [PHARMACY] cuối tin.",
 # Chốt 23/10 (chị Nga, ca Tit Tan): khách muốn qua CỬA HÀNG 92 Trung Kính → bot vẫn dẫn tới chốt (hẹn giờ + giữ hàng, hoặc giao tận nhà)
 "store_visit": ("Chốt 23/10 (chị Nga) — khách muốn ĐẾN CỬA HÀNG Sâm Thái Minh 92 Trung Kính xem / mua trực tiếp: KHÔNG chỉ chúc mua thuận lợi rồi dừng — vẫn dẫn tới CHỐT. "
   "Lượt 1 (1 tin, đúng 1 câu hỏi): 'Dạ được ạ, anh/chị ghé cửa hàng Sâm Thái Minh tại 92 Trung Kính, Cầu Giấy để xem trực tiếp sản phẩm nhé ạ. "
   "Anh/chị dự định qua vào khoảng thời gian nào để em báo cửa hàng chuẩn bị sẵn [sản phẩm, số lượng nếu đã biết] cho anh/chị ạ?' (xuống dòng) "
   "'Cửa hàng mở cửa từ 8h00 đến 21h00 hằng ngày, mua trực tiếp tại cửa hàng anh/chị vẫn được nhận quà tặng như đặt qua page ạ. "
   "Nếu anh/chị bận chưa qua được, bên em giao tận nhà [miễn phí vận chuyển — CHỈ nói khi sản phẩm thuộc nhóm free ship], anh/chị nhận hàng kiểm tra rồi mới thanh toán ạ.' "
   "Lượt sau: khách hẹn giờ → xin họ tên + SĐT để cửa hàng giữ hàng, rồi chèn [HANDOFF: khách hẹn qua cửa hàng 92 Trung Kính - giờ hẹn - sản phẩm | SĐT | 2]; "
   "khách chọn giao tận nhà → chốt đơn như bình thường (build_order). KHÔNG chèn [PHARMACY] cho ca cửa hàng 92 Trung Kính. "
   "Giờ mở cửa (chốt 23/10): 8h00–21h00 hằng ngày. Quà tặng khi mua tại cửa hàng GIỐNG đặt qua page (cùng bảng CTKM khách mới / khách cũ). Không ép, chỉ mời giao tận nhà 1 lần."),
}
need_map = {
 "boi_bo_nguoi_gia": {"label": "Bồi bổ cho ông bà, cha mẹ, người trung – cao tuổi", "core": "hsvn_lat", "alt": ["hsmo_tui"]},
 "benh_nen": {"label": "Người có bệnh nền (huyết áp cao/thấp, tiểu đường, tim mạch, mỡ máu) muốn bồi bổ", "core": "hsvn_lat", "alt": ["hsmo_tui"], "note": "Hỏi thuốc đang dùng + chạy compliance_check (diabetes/hypertension/hypotension/bp_uncontrolled/anticoagulant...). Huyết áp: nói mềm theo scripts_approved.bp_question (Hồng sâm một phần hỗ trợ ổn định huyết áp; duy trì thuốc, dùng cách thuốc khoảng 2 tiếng). Được nói hỗ trợ kiểm soát đường huyết / ổn định huyết áp / bảo vệ tim mạch — luôn có chữ 'hỗ trợ'. Chốt 13/10: KHÔNG tự nói 'không phải thuốc'; CHỈ khi khách nói đang dùng thuốc tây → khuyên duy trì thuốc bác sĩ kê + dùng kèm sâm để bồi bổ, ĐÚNG 1 LẦN."},
 "moi_om_day": {"label": "Mới ốm dậy, sau phẫu thuật, suy nhược, sức đề kháng kém", "core": "hsvn_lat", "alt": ["long_sam"]},
 "met_moi_stress": {"label": "Hay mệt mỏi, căng thẳng, làm việc nhiều, ngủ không sâu; cần năng lượng khi vận động, chơi thể thao", "core": "hsmo_tui", "alt": ["hsvn_lat"]},
 "kem_an_gay_yeu": {"label": "Kém ăn, gầy yếu, mệt mỏi", "core": "hsvn_lat", "alt": ["hsmo_tui"]},
 "tiet_kiem_de_uong": {"label": "Muốn loại dễ uống, sợ đắng, ngân sách vừa phải, dùng cho cả nhà", "core": "hsmo_tui", "alt": ["hsmo_chai"], "note": "chốt 16/10: mời dạng túi trước, dạng chai chỉ nói khi khách hỏi"},
 "me_sau_sinh": {"label": "Mẹ sau sinh KHÔNG cho con bú cần bồi bổ", "core": "hsmo_tui", "alt": ["hsmo_chai"], "note": "Chốt 15/10: ĐANG CHO CON BÚ → KHÔNG dùng bất kỳ sản phẩm nào (scripts_approved.breastfeeding). Không cho con bú → dùng được NGAY Hồng sâm dạng nước (chai/túi), không cần đợi 6 tháng. KHÔNG nói tiết sữa/lợi sữa."},
 "dep_da": {"label": "Phụ nữ muốn chăm sóc da, làm chậm lão hóa", "core": "hsmo_tui", "alt": ["hsvn_lat"]},
 "sinh_ly_nam": {"label": "Nam giới sinh lý yếu (xuất tinh sớm, ham muốn giảm, kém cương), đau lưng mỏi gối do thận kém", "core": "duong_sam", "alt": []},
 "qua_bieu": {"label": "Mua làm quà biếu (đối tác, người lớn tuổi)", "core": "hsvn_lat", "alt": ["long_sam"], "note": "Rượu sâm chỉ nhắc khi khách tự hỏi rượu."},
 "tra_hang_ngay": {"label": "Khách TỰ hỏi mua trà sâm uống hằng ngày (chỉ dùng khi khách hỏi trà)", "core": "tra_1700", "alt": ["tra_nguyen_la"]},
}
combo_tiers_note = (f"Hồng sâm lát (giá {vnd(LAT_PRICE)}/hộp): " + "; ".join(combo_line(q) for q in LAT_COMBOS)
                    + f"; chê đắt mua 1 hộp tặng {OBJ_GIFT}. Liệu trình khuyên dùng 3–6 tháng. Sản phẩm khác: lấy quà đúng bảng programs.new_customer.")
customer_segments = {
 "A_con_mua_cho_bo_me": "Con cái mua cho bố mẹ/ông bà: quan tâm an toàn với bệnh nền, nguồn gốc, cách dùng đơn giản — cần thông tin dễ giải thích lại",
 "B_nguoi_cao_tuoi_tu_mua": "Người cao tuổi tự mua, có bệnh nền, hay hỏi kỹ — tư vấn chậm, chắc, xưng hô đúng (bác/ông/bà → cháu)",
 "C_nguoi_ban_ron_met_moi": "Người đi làm hay mệt, căng thẳng, ngủ kém — ưu tiên tiện lợi, dễ uống",
 "D_me_sau_sinh": "Mẹ sau sinh — đang cho con bú: KHÔNG dùng sản phẩm nào (chốt 15/10); không cho con bú: Hồng sâm dạng nước, dùng được ngay",
 "E_nam_gioi": "Nam giới sinh lý yếu — Dương Sâm Linh Đan; tế nhị, không suồng sã",
 "F_qua_bieu": "Mua biếu — quan tâm hộp đẹp, sang, nguồn gốc; Hồng sâm lát, Long Sâm Linh Đan",
 "brief_mua_de_dung": "Brief 25/09 — MUA ĐỂ DÙNG: từ 35 tuổi (tập trung 55+), công chức, văn phòng, nội trợ, hưu trí, người phục hồi sau bệnh; quan tâm bệnh lý tuổi già (tiểu đường, huyết áp, xương khớp), thích sản phẩm tự nhiên; tin tư vấn của dược sĩ/bác sĩ, đọc kỹ nguồn gốc, giấy tờ, phản hồi khách cũ; mong muốn: cảm nhận cải thiện, an toàn với thuốc đang dùng, nguồn gốc rõ, dễ dùng, được hướng dẫn liều chi tiết.",
 "brief_mua_de_tang": "Brief 25/09 — MUA ĐỂ TẶNG: 22–60+ (trọng tâm 35–50), doanh nhân, công chức, văn phòng thu nhập khá; biếu cha mẹ, sếp, đối tác dịp lễ Tết, mừng thọ; quan tâm bao bì sang, thương hiệu uy tín, gói quà, giao đúng hẹn, hóa đơn (tặng đối tác).",
}
escalation = {
 "handoff_rules": ["Khách CŨ: Hồng sâm lát → báo ưu đãi khách cũ theo bảng, tự chốt; sản phẩm khác chưa có bảng → xin SĐT, chuyển nhân viên (level 2)", "Khách hỏi/yêu cầu ĐỔI TRẢ, hoàn tiền → bot KHÔNG trả lời chính sách, chuyển chuyên viên hỗ trợ trực tiếp (level 2)", "Khách hỏi tích điểm/giá sỉ → chuyển nhân viên (level 2)",
   "Đơn lớn vượt bậc combo, đơn Sâm tươi, đơn Rượu hũ nguyên cây → thu thông tin, chuyển nhân viên (level 2)",
   "Khách muốn tham quan vườn sâm / vùng trồng (Sìn Hồ farm – Lai Châu) → scripts_approved.farm_visit: xin SĐT khách để liên hệ trực tiếp + [HANDOFF: khách muốn thăm vườn | SĐT | 2] (chốt 15/10: vùng trồng không còn cho thuê phòng nghỉ, KHÔNG nhắc homestay)",
   "Câu hỏi KHÔNG có trong dữ liệu → không bịa: 'Em xin tiếp nhận và kiểm tra thêm, sẽ có nhân viên phản hồi anh/chị sớm ạ' + [HANDOFF: ... | | 2]",
   "CHƯA HIỂU ý khách (tin mơ hồ) → KHÔNG chuyển người, hỏi lại lịch sự: 'Dạ, anh/chị vui lòng chia sẻ rõ hơn giúp em được không ạ? Em chưa hiểu ý của anh/chị nên chưa thể hỗ trợ chính xác.'",
   "Khách CHỈ LO LẮNG/muốn xác thực ('hàng có chính hãng không', 'sợ mua online bị lừa') → KHÔNG chuyển người; trấn an bằng chất lượng, uy tín Thái Minh, được kiểm tra hàng trước khi nhận (COD).",
   "Khách CÁO BUỘC ('lừa đảo', 'lừa gạt', 'bóc phốt', 'báo công an'...) hoặc khiếu nại thiếu hàng/giao sai/tác dụng phụ → chuyển NGAY (level 4): 'Dạ em rất tiếc về trải nghiệm của anh/chị. Em đã ghi nhận và đang kết nối ngay với chuyên viên để hỗ trợ anh/chị ạ.' Đồng cảm ngắn, KHÔNG dùng câu máy móc kiểu 'Rất tiếc, tôi không thể hỗ trợ'.",
   "Đối tượng đặc biệt chưa có hướng dẫn, thuốc kê đơn ngoài tài liệu, bệnh nặng đang điều trị → chuyên viên chuyên môn (level 3)",
   "Nghi ADR, khiếu nại chất lượng, nghi hàng giả → level 4 (xin ảnh hộp/lô/hạn sử dụng + nơi mua)"],
 "hotline": "1800 1120 (miễn cước; số phụ 1800 8396). Riêng Dương Sâm Linh Đan: 1800 8308",
 "levels": {"1": "Đơn đã chốt xong → [HANDOFF: đơn đã chốt - lên đơn | SĐT | 1]", "2": "CSKH thường: khách cũ, đơn lớn, sâm tươi, rượu hũ, tích điểm, đổi trả, câu hỏi ngoài tài liệu",
   "3": "Chuyên viên chuyên môn: đối tượng đặc biệt chưa có hướng dẫn, thuốc kê đơn, bệnh nặng, khách truy nguồn chuyên môn", "4": "KHẨN: nghi ADR, khiếu nại chất lượng/thiếu hàng/giao sai, nghi hàng giả, khách cáo buộc lừa đảo/bóc phốt/báo công an"},
 "adr_7_fields": "(1) ngày bắt đầu dùng, (2) sản phẩm + liều/ngày, (3) thời điểm dùng, (4) biểu hiện xuất hiện sau bao lâu, (5) thuốc/sản phẩm dùng kèm, (6) bệnh nền, (7) ảnh bao bì/số lô/hạn sử dụng. CẤM phán nguyên nhân. Khuyên TẠM NGỪNG ngay tin đầu.",
}
DS_PRICE = P["duong_sam"]["packages"][0]["price_retail"]
def ds_line(q):
    r = next(x for x in RULES if x["if_sku"] == "duongsam-10" and x["min_qty"] == q)
    return f"{r['label']} ({q} hộp): {vnd(DS_PRICE * q)} – tặng {r['gift']}"
DS_COMBO_TXT = " / ".join(f"'🎁 {ds_line(q)}'" for q in (3, 6, 9))
scripts_approved = {
 "identity": "Chốt 14/10 (anh Huy): chào bằng tên thương hiệu 'Dạ Sâm Thái Minh chào anh/chị ạ.' — KHÔNG xưng dược sĩ. Khách hỏi em là ai: 'Dạ em là chuyên viên tư vấn của Sâm Thái Minh ạ.'",
 "diabetes_honey": "Chốt 16/10 (chị Nga) — khách lo Nước Hồng sâm có MẬT ONG ảnh hưởng bệnh tiểu đường / bác sĩ dặn kiêng mật ong: 'Dạ người tiểu đường vẫn dùng được Nước Hồng sâm Thái Minh mật ong ạ, vì trong Sâm Việt Nam có các hoạt chất Rg1, Rd có tác dụng hỗ trợ kiểm soát đường huyết. Anh/chị chỉ cần dùng trước ăn 30 phút là được ạ.' + liều tiểu đường của tool (túi: 1 túi pha 100ml nước ấm buổi sáng; chai: 5ml/ngày). KHÔNG chuyển sang Long Sâm/sản phẩm khác.",
 "off_hours_order": "Chốt 16/10 (chị Nga) — NGOÀI GIỜ LÀM VIỆC mà khách CHỐT ĐƠN xong (đã đủ thông tin, build_order ready): 'Dạ em đã ghi nhận đơn hàng của anh/chị rồi ạ. Hiện đã ngoài giờ làm việc, sáng mai từ 08h00 bên em sẽ liên hệ xác nhận và hỗ trợ gửi đơn cho anh/chị ạ.' + [HANDOFF: đơn đã chốt ... | SĐT | 1].",
 "off_hours": "Chốt 16/10 (chị Nga) — NGOÀI GIỜ LÀM VIỆC (hồ sơ khách ghi 'THỜI ĐIỂM: NGOÀI GIỜ'), khi chuyển nhân viên / khách để SĐT (KHÔNG phải chốt đơn — chốt đơn dùng off_hours_order): 'Dạ hiện đã ngoài giờ làm việc, nhân viên sẽ nhắn lại anh/chị từ 08h00 sáng mai ạ. Trong lúc chờ, anh/chị cần hỏi gì em hỗ trợ ngay ạ.' — thay cho các câu hứa 'trong ít phút', 'gọi lại ngay', 'bên em sẽ gọi'. Vẫn chèn [HANDOFF ...] như bình thường.",
 "human_request": "Chốt 16/10 (chị Nga) — khách NÓI RÕ muốn chat / nói chuyện với nhân viên, người thật ('cho chị gặp nhân viên', 'chị chỉ muốn chat với người', 'không nói chuyện với máy') — KHÔNG bắt để SĐT, chuyển ngay trong khung chat: 'Dạ vâng, em chuyển anh/chị sang nhân viên tư vấn trực tiếp ngay ạ. Anh/chị chờ em một chút, bạn ấy sẽ nhắn lại anh/chị trong ít phút nhé ạ.' + [HANDOFF: khách muốn chat với người | SĐT nếu khách đã cho | 2]. Sau câu này KHÔNG hỏi thêm, KHÔNG tư vấn tiếp.",
 "ai_question": "Chốt 15/10 (anh Huy) — khách hỏi 'em là người hay máy/bot/AI?': 'Dạ em là trợ lý tư vấn của Sâm Thái Minh ạ. Em nắm rõ thông tin các sản phẩm của Sâm Thái Minh, anh/chị có câu hỏi nào em hỗ trợ ngay ạ. Nếu anh/chị muốn nói chuyện trực tiếp với nhân viên, anh/chị để lại số điện thoại, em nhờ chuyên viên gọi lại ngay ạ.' KHÔNG BAO GIỜ nói dối là người thật. Khách hỏi lại lần nữa / hỏi thẳng 'là máy à', 'có phải AI không' → trả lời thật: 'Dạ em là trợ lý tự động của Sâm Thái Minh ạ.' rồi mời để lại SĐT. Khách để lại SĐT → [HANDOFF: khách muốn gặp người | SĐT | 2]. Không tự nhắc chuyện này khi khách không hỏi.",
 "product_overview": ("Chốt 14/10 (chị Nga) — khách hỏi bên em có những sản phẩm gì: 'Dạ hiện bên em có 4 dòng sản phẩm chính phù hợp với từng nhu cầu:' (xuống dòng) "
   "'1️⃣ Hồng sâm Thái Minh dạng lát: phù hợp nhất cho ông bà, cha mẹ, người có bệnh nền (tiểu đường, huyết áp, tim mạch...). Dạng lát tiện lợi, hỗ trợ bồi bổ toàn thân, làm chậm lão hóa.' (xuống dòng) "
   "'2️⃣ Hồng sâm Thái Minh dạng nước: lựa chọn tiết kiệm nhất (khoảng 31.000đ/ngày), vị ngọt nhẹ dễ uống. Hỗ trợ tăng sức đề kháng, giảm mệt mỏi, đẹp da cho cả gia đình.' (xuống dòng) "
   "'3️⃣ Dương Sâm Linh Đan: dành riêng cho nam giới, hỗ trợ lấy lại phong độ, tăng sức bền, cải thiện giấc ngủ và giảm stress. Kết hợp Sâm Việt Nam với Cao xương dê, Đông trùng hạ thảo, Dâm dương hoắc...' (xuống dòng) "
   "'4️⃣ Long Sâm Linh Đan: dòng thượng hạng, quà biếu cao cấp kết hợp Sâm Việt Nam, Đông trùng hạ thảo, Cao ban long... Hỗ trợ phục hồi thể lực cho người suy nhược hoặc làm quà tặng đối tác.' (xuống dòng) "
   "'Anh/chị đang quan tâm đến sản phẩm nào để em hỗ trợ cho anh/chị ạ?'"),
 "disease_question": "Khách hỏi sản phẩm có tốt cho người ung thư / tiểu đường / huyết áp / đột quỵ không → trả lời theo benefits có chữ 'hỗ trợ'. Ung thư (chốt 15/10, anh Huy): 'Dạ trong Sâm Lai Châu có hoạt chất MR2, một saponin chiếm hàm lượng cao trong Sâm Lai Châu ạ. Nghiên cứu của Đại học Dược Kyoto, Nhật Bản cho thấy MR2 có tác dụng hỗ trợ ức chế quá trình phân bào của tế bào một số loại ung thư. Người đang hóa trị, điều trị có thể dùng được Hồng sâm Thái Minh để hỗ trợ bồi bổ sức khoẻ, hỗ trợ tăng cường miễn dịch ạ.' + hỏi người dùng đang dùng thuốc/điều trị gì (có → maintain_meds, 1 lần) + compliance_check (flag cancer_treatment). KHÔNG nói '50%', 'chống khối u', 'kháng ung thư', 'trị liệu', 'chữa', 'đã chứng minh chữa'. KHÔNG tự nói 'không phải thuốc'. Bệnh chưa có trong tài liệu → disease_no_guidance.",
 "maintain_meds": "Chốt 15/10 — CHỈ dùng khi khách NÓI người dùng đang uống thuốc tây chữa bệnh nền (huyết áp, tiểu đường, tim mạch...), nói ĐÚNG 1 LẦN trong cả hội thoại: 'Dạ anh/chị cứ duy trì thuốc bác sĩ kê đều đặn như hiện tại, dùng kết hợp thêm [tên sản phẩm Sâm đang tư vấn] để bồi bổ, nâng cao sức khỏe, nên dùng cách thuốc khoảng 2 tiếng ạ.'",
 "bp_question": "Chốt 15/10 (anh Huy: nói mềm, không khẳng định) — khách hỏi người huyết áp cao / thấp dùng Hồng sâm Thái Minh (lát, chai, túi) được không: 'Dạ được ạ. Hồng sâm một phần hỗ trợ điều hòa tuần hoàn và chức năng mạch máu, từ đó hỗ trợ ổn định huyết áp.' (xuống dòng) 'Với người đang dùng thuốc huyết áp, anh/chị vẫn nên duy trì thuốc theo chỉ định của bác sĩ và dùng Hồng sâm cách thuốc khoảng 2 tiếng ạ.' + 1 câu hỏi. KHÔNG nói 'đã ổn định hay chưa đều dùng được', KHÔNG nói 'giảm độ cứng động mạch'. Dương Sâm Linh Đan, Long Sâm Linh Đan: chỉ dùng khi đang dùng thuốc và huyết áp đã ổn định, khuyên hỏi thêm ý kiến bác sĩ điều trị; huyết áp chưa ổn định: Dương Sâm hỏi chỉ số (≤150 dùng được, >150 chuyển), Long Sâm chuyển chuyên viên. Tai biến do XUẤT HUYẾT → chuyển chuyên viên (flag stroke_hemorrhagic).",
 "bottle_material": "Chốt 15/10 — khách hỏi Nước Hồng sâm Mật ong Thái Minh dạng chai 175ml là nhựa hay thủy tinh: 'Dạ sản phẩm Nước Hồng sâm Mật ong Thái Minh 175ml được đóng gói bằng chai nhựa chuyên dùng trong ngành thực phẩm và dược phẩm, đảm bảo an toàn cho sức khỏe ạ. Chai nhựa còn có nhiều điểm ưu việt: rất nhẹ, bền, dễ rót, không bị đập vỡ khi vận chuyển và tiện mang theo dùng hằng ngày ạ.' (KHÔNG nói 'cao cấp')",
 "price_why": 'Dạ em hiểu băn khoăn của anh/chị ạ. Hồng sâm Việt Nam Thái Minh làm từ Sâm Lai Châu – một loại sâm quý của Việt Nam, được chăm sóc hơn 5 năm mới thu hoạch, sâm có nguồn gốc rõ ràng, được kiểm soát chặt chẽ chất lượng đầu vào. Sâm Việt Nam có hoạt chất MR2 mà sâm Hàn Quốc không có. Sản phẩm là công trình chuyển giao từ VIGH (Viện Nghiên cứu Sâm và Dược liệu Việt Nam). Hồng sâm còn dễ hấp thu hơn và bảo quản dễ dàng hơn sâm tươi ạ.',
 "price_increase": (f"Khách hỏi sao Hồng sâm lát tăng giá ({vnd(LAT_PRICE_OLD)} lên {vnd(LAT_PRICE)}): 'Dạ em rất chia sẻ ạ. Chi phí sản xuất tăng nên công ty buộc phải điều chỉnh giá, "
   "nhưng Thái Minh cam kết không cắt giảm chất lượng, giữ nguyên chất lượng sản phẩm đầu ra. Mong anh/chị tiếp tục tin tưởng đồng hành ạ.' (chốt 15/10: KHÔNG nói 'giữ nguyên hàm lượng hoạt chất')"),
 "rename": "Từ tháng 10/2025 Hồng Sâm Lai Châu đổi tên thành Hồng Sâm Việt Nam Thái Minh — đồng bộ thương hiệu Thái Minh và hưởng ứng định hướng phát triển sâm Việt Nam thành thương hiệu quốc gia (Quyết định 611 của Thủ tướng Chính phủ), nhấn mạnh nguồn gốc sâm trồng tại Việt Nam (Sâm Lai Châu).",
 "farm_visit": "Chốt 15/10 (anh Huy) — khách muốn thăm vườn / vùng trồng sâm: 'Dạ vùng trồng sâm Sìn Hồ farm ở Sìn Hồ, Lai Châu ạ. Anh/chị để lại số điện thoại, bên em liên hệ trực tiếp để sắp xếp cho anh/chị nhé ạ.' + [HANDOFF: khách muốn thăm vườn | SĐT | 2]. KHÔNG nhắc homestay/phòng nghỉ (đã không còn cho thuê), KHÔNG đưa số điện thoại cá nhân.",
 "pm_visit": "CHỈ dùng khi khách TỰ hỏi về chuyến thăm/việc lãnh đạo Nhà nước đến vườn sâm (chốt 23/09): 'Dạ đúng ạ, vùng trồng sâm Việt Nam của Thái Minh tại Lai Châu đã được Thủ tướng Chính phủ Phạm Minh Chính ghé thăm vào ngày 18/11/2023 ạ.' KHÔNG chủ động nhắc, không dùng để quảng bá công dụng.",
 "soft_ask_phone": "Dạ vâng ạ. Anh/chị để lại số điện thoại giúp em, khi có chương trình ưu đãi mới em báo anh/chị trước nhé ạ.",
 "trial_request": "Chốt 25/09: khách xin DÙNG THỬ / xin mẫu thử → khéo léo từ chối, KHÔNG hứa mẫu thử, KHÔNG nói 'không hiệu quả thì hoàn tiền'. KHÔNG mời khách bóc hàng dùng thử (chốt 14/10). Mẫu: 'Dạ em rất hiểu anh/chị muốn dùng thử trước cho yên tâm ạ. Hiện bên em chưa có chương trình dùng thử, vì sâm được đóng gói nguyên hộp, niêm phong để giữ trọn chất lượng ạ. Anh/chị có thể bắt đầu với 1 hộp, nhận hàng được kiểm tra nguyên hộp, tem niêm phong rồi mới thanh toán; hoặc chọn Nước Hồng sâm mật ong dạng túi có mức giá nhẹ hơn để trải nghiệm trước ạ.'",
 "price_discovery_hsvn": ("Chốt 26/10 (chị Nga) — báo giá lần đầu KHÔNG nhất thiết lúc nào cũng gửi bảng combo: có thể sau câu giá + đoạn phù hợp, "
   "hỏi 1 câu KHƠI GỢI để khách chia sẻ nhu cầu (khách trả lời rồi mới gửi bảng combo + câu chốt hợp nhu cầu). Chọn 1 trong 3 câu đã duyệt (chị Nga 26/10: D1, D2, D4), xoay vòng: "
   "ⓀD1 'Để em tư vấn đúng nhu cầu nhất, anh/chị cho em hỏi anh/chị đang muốn bồi bổ sức khỏe cho bản thân hay mua biếu người thân ạ?' "
   "| ⓀD2 'Anh/chị có hay gặp tình trạng ngủ kém, ăn không ngon hay mệt mỏi không ạ, để em gợi ý liệu trình phù hợp nhất ạ?' "
   "| ⓀD4 'Trước đây anh/chị đã dùng sâm hay sản phẩm bồi bổ nào chưa ạ, để em tư vấn liệu trình phù hợp nhất cho anh/chị ạ?' "
   "KHÔNG dùng câu khơi gợi khi khách hỏi thẳng combo / khuyến mãi / ưu đãi / bảng giá, khi khách đã nói rõ nhu cầu, hoặc khi đã hỏi khơi gợi 1 lần trong hội thoại."),
 "price_probe_hsvn": ("Chốt 26/10 (chị Nga) — CÂU KHAI THÁC khi khách hỏi giá Hồng sâm lát (TH1–TH11). Luôn báo giá trước; mỗi lượt 1 câu; "
   "tối đa 2 câu khai thác (tính cả câu khơi gợi D) trước khi gửi bảng combo; câu hỏi phải bám điều khách vừa nói: "
   "ⓀK1 'Anh/chị có đang điều trị huyết áp, tiểu đường hay bệnh nền nào không ạ, để em hướng dẫn cách dùng an toàn, đúng liều ạ?' "
   "| ⓀK2 'Anh/chị có đang dùng thuốc gì hằng ngày không ạ, để em dặn khoảng cách dùng sâm với thuốc cho phù hợp ạ?' "
   "| ⓀK3 'Giấc ngủ của anh/chị dạo này thế nào ạ: khó vào giấc hay ngủ không sâu, hay thức dậy giữa đêm ạ?' "
   "| ⓀK4 'Anh/chị thấy mệt nhiều vào thời điểm nào ạ: buổi sáng khó tỉnh hay chiều tối hay đuối sức ạ?' "
   "| ⓀK5 'Anh/chị năm nay khoảng bao nhiêu tuổi ạ, để em tư vấn liều dùng phù hợp ạ?' "
   "| ⓀK5b 'Anh/chị năm nay khoảng bao nhiêu tuổi và có đang dùng thuốc gì hằng ngày không ạ, để em tư vấn cách dùng phù hợp ạ?' "
   "| ⓀK7 'Anh/chị định biếu ông bà, bố mẹ hay biếu đối tác ạ, để em gợi ý gói quà phù hợp nhất ạ?' "
   "| ⓀK8 'Công việc của anh/chị có hay thức khuya, áp lực hay phải đi lại nhiều không ạ, để em gợi ý cách dùng giúp anh/chị tỉnh táo hơn ban ngày ạ?' "
   "KHÔNG khai thác khi: khách hỏi thẳng combo / khuyến mãi / ưu đãi; khách vội ('giá thôi', 'nhanh', 'ok'); khách hỏi lại giá lần 2; khách đã chốt mua. "
   "Khách kể bệnh → compliance_check trước. Sau khi khai thác xong → bảng combo + câu chốt hợp nhu cầu (bố mẹ → Ⓔ; tình trạng/bệnh → Ⓑ; lưỡng lự → Ⓓ; vội → Ⓕ)."),
 "price_quote_hsvn": ("Chốt 13/10 — khách hỏi giá / chương trình Hồng sâm lát → trả lời đúng 3 phần, KHÔNG kèm đoạn mô tả tính năng dài ở cuối: "
   f"(1) 1 câu dẫn: giá {vnd(LAT_PRICE)}/hộp 14 gói, dùng 14 ngày (mỗi ngày 1 gói buổi sáng), liệu trình cơ bản 3 tháng; "
   "NGAY SAU câu dẫn, xuống dòng thành 1 đoạn riêng, thêm ĐÚNG 1 trong 3 đoạn sau (chốt 25/10, chị Nga — chọn theo tình huống, không lặp đoạn đã dùng trong hội thoại): Ⓐ MẶC ĐỊNH (khách hỏi giá lần đầu, chưa rõ người dùng): 'Hồng sâm này đặc biệt phù hợp với người ngủ kém, ăn không ngon, cơ thể hay mệt mỏi, uể oải ạ. Thông thường chỉ sau khoảng 2 hộp đầu, anh/chị sẽ thấy ăn ngon miệng hơn, ngủ sâu giấc hơn, người khỏe khoắn và tỉnh táo hơn ạ.' | Ⓑ NGẮN (khách hỏi lại giá lần 2 sau khi đã nghe Ⓐ, hoặc lượt đó đã phải trả lời nhiều ý khác): 'Hồng sâm này rất hợp với người ngủ kém, ăn không ngon, hay mệt mỏi ạ. Dùng đều mỗi sáng, cơ thể sẽ dần ăn ngon, ngủ sâu và khỏe khoắn hơn ạ.' | Ⓒ MUA CHO BỐ MẸ / ÔNG BÀ / người lớn tuổi (khách nói mua cho bố, mẹ, ông bà, biếu người già): 'Bố mẹ lớn tuổi hay ngủ chập chờn, ăn kém, người mệt mỏi thì dùng Hồng sâm rất hợp ạ. Sau khoảng 2 hộp đầu, nhiều người thấy ăn ngon, ngủ sâu và khỏe khoắn hơn rõ (tùy cơ địa).' (Ⓒ đổi 'Bố mẹ' thành đúng người khách nói, vd 'Ông bà', 'Bố'). "
   "(khách đã nói rõ tình trạng/người dùng khác thì có thể thay bằng câu phù hợp tình trạng đó, vẫn ngắn 1 câu); "
   f"(2) danh sách gói theo tháng, mỗi gói 1 dòng (giá + quà) — chốt 25/10 (chị Nga): ĐA DẠNG cách trình bày, chọn 1 trong 4 kiểu dưới, "
   f"XOAY VÒNG (khách hỏi lại giá thì đổi kiểu khác), giữ NGUYÊN giá, số hộp, quà: {COMBO_STYLE_TXT}; "
   f"(3) DẪN DẮT CHỐT — ĐÚNG 1 câu hỏi cuối (chốt 25/10, chị Nga: đa dạng cách triển khai combo, chọn chiến thuật theo tình huống, XOAY VÒNG không lặp câu đã dùng): "
   f"Ⓐ HỎI CHỌN ƯU ĐÃI (mặc định lần báo giá đầu): 'Trong 3 ưu đãi trên, anh/chị muốn chọn combo nào để em giữ quà cho anh/chị ạ?' | "
   f"Ⓑ GỢI Ý ƯU ĐÃI TỐT NHẤT (khách nói rõ tình trạng: mệt nhiều, ngủ kém lâu, có bệnh nền, mới ốm dậy — hoặc hỏi 'nên mua gói nào'): "
   f"'Với tình trạng của anh/chị, em gợi ý combo 3 tháng ạ: đủ liệu trình cơ bản để cơ thể thay đổi rõ, lại được tặng nhiều quà nhất ({lat_rule(6)['gift']}). Em lên đơn combo 3 tháng cho anh/chị nhé?' | "
   f"Ⓒ DẪN DẮT 1 THÁNG HAY 3 THÁNG (khách đã quan tâm, đang cân nhắc): 'Anh/chị muốn dùng thử combo 1 tháng trước, hay lấy luôn combo 3 tháng cho đủ liệu trình và nhận thêm {lat_rule(6)['gift'].split(' loại')[0]} ạ?' | "
   f"Ⓓ BẮT ĐẦU NHẸ (khách lưỡng lự, dùng lần đầu, ngại chi nhiều): 'Lần đầu dùng anh/chị có thể bắt đầu combo 1 tháng (2 hộp) để cảm nhận trước, vẫn được tặng {lat_rule(2)['gift']}. Em lên đơn combo 1 tháng cho anh/chị nhé?' | "
   f"Ⓔ MUA BIẾU BỐ MẸ / ÔNG BÀ: 'Với bố mẹ lớn tuổi, dùng đều 3 tháng sẽ thấy rõ sức khỏe cải thiện hơn ạ. Anh/chị lấy combo 3 tháng biếu bố mẹ luôn, vừa đủ liệu trình vừa có thêm Trà sâm làm quà nhé?' | "
   f"Ⓕ CHỐT NHẸ, BỎ RÀO CẢN (khách đã nghe giá mà chưa trả lời / hỏi lại lần 2): 'Anh/chị chọn combo nào thì chỉ cần nhắn em tên, số điện thoại và địa chỉ, em lên đơn ngay ạ. Hàng giao tận nơi, kiểm tra rồi mới thanh toán nên anh/chị yên tâm nhé.' "
   f"| Ⓖ HỎI NGƯỜI DÙNG (chưa biết mua cho ai): 'Anh/chị định dùng cho bản thân hay biếu người thân ạ, để em gợi ý gói phù hợp nhất cho anh/chị ạ?' "
   f"| Ⓗ BẮT ĐẦU RỒI DÙNG TIẾP (khách cân nhắc, lần đầu biết sản phẩm): 'Nhiều anh chị bắt đầu combo 1 tháng để cảm nhận, dùng hợp thì lấy tiếp cho đủ liệu trình 3 tháng ạ. Anh/chị muốn em lên đơn combo nào ạ?' "
   f"| Ⓘ YÊN TÂM NHẬN HÀNG (khách lo mua online): 'Bên em giao tận nhà, anh/chị nhận hàng kiểm tra rồi mới thanh toán ạ. Anh/chị chọn combo 1 tháng hay 3 tháng để em lên đơn luôn ạ?' "
   f"KHÔNG nói 'giảm giá / tiết kiệm'; mỗi lượt chỉ 1 chiến thuật, 1 câu hỏi. "
   f"KHÔNG tư vấn gói lẻ 1 hộp (và quà mốc 1 hộp: {OBJ_GIFT}) trừ khi khách chê đắt hoặc muốn dùng thử."),
 "order_after_confirm": "Chốt 15/10 (anh Huy: mượt mà, thân thiết hơn) — sau khi gửi tổng hợp đơn và khách xác nhận: 'Dạ em cảm ơn anh/chị ạ 😊 Trong ngày hôm nay bên em sẽ gọi điện lại để xác nhận đơn trước khi gửi hàng, anh/chị để ý điện thoại giúp em nhé ạ.' (xưng 'em' / 'bên em', KHÔNG nói 'sẽ có chuyên viên của Sâm Thái Minh gọi điện lại'). Nếu khách nhắn 'không cần gọi lại / cứ gửi luôn' → 'Dạ vâng, em ghi chú đóng gói và gửi hàng đi ngay cho anh/chị ạ.' (ghi rõ trong lý do HANDOFF: khách không cần gọi xác nhận). SAU ĐÓ KHÔNG chủ động nhắn thêm nội dung khác.",
 "upsell_double": ("Chốt 15/10, đổi THỨ TỰ 25/10 (chị Nga) — gửi TỔNG HỢP ĐƠN trước (tin đó KHÔNG mời thêm); khách XÁC NHẬN đúng → lượt sau: 'Dạ em đã ghi nhận đơn [x] của anh/chị rồi ạ.' + mời ĐÚNG 1 LẦN, không ép, kết bằng 'nếu anh/chị giữ đơn cũ thì em gửi đi luôn ạ'. "
   "Câu mời luôn có 1 CÂU ĐỆM nêu giá trị trước khi hỏi — XOAY VÒNG, không lặp câu đệm đã dùng trong hội thoại. "
   "Câu đệm nói ĐÚNG NGUYÊN VĂN như danh sách dưới (chỉ đổi xưng hô cho khớp khách), KHÔNG thêm thắt, KHÔNG tự chế lợi ích. "
   "CẤM khi mời combo: 'ưu đãi tốt hơn rất nhiều', 'mức ưu đãi tốt hơn', 'giá tốt hơn', 'rẻ hơn', 'dưỡng chất thấm sâu', 'thấm sâu', 'hấp thu tối đa', 'nhân dịp'. "
   "Câu mời = câu combo (giá + quà lấy từ tool) + 1 câu đệm + 1 câu hỏi; gửi gọn trong 1–2 tin. "
   "COMBO 2/4/6 HỘP GIÁ GIỮ NGUYÊN, CHỈ TẶNG QUÀ → TUYỆT ĐỐI KHÔNG nói 'giảm giá', 'giá ưu đãi', 'tiết kiệm' cho các combo này. Câu đệm dùng cho combo 2/4/6 hộp: "
   "(1) 'Lấy combo có quà, lời hơn mua lẻ đó anh/chị ạ.' | (2) 'Đây là mức quà tặng tốt nhất bên em đang có cho khách mới ạ.' | "
   "(3) 'Dùng đều đủ liệu trình thì cơ thể mới hấp thu tốt, lấy combo mình đỡ phải đặt lại giữa chừng ạ.' | "
   "(4) 'Mua lẻ 1 hộp thì bên em chưa có quà ạ, lấy combo 2 hộp là anh/chị được tặng thêm Trà sâm uống hằng ngày luôn ạ.' (chỉ dùng khi khách đang đặt 1 hộp) | "
   "(5) 'Combo 2 hộp dùng vừa tròn 1 tháng, anh/chị dùng đều mỗi ngày không phải lo hết giữa chừng ạ.' (chỉ khi mời combo 2 hộp) | "
   "(6) 'Thường sau khoảng 2 hộp đầu cơ thể mới bắt đầu cảm nhận rõ, nên lấy combo để dùng liền mạch là hợp nhất ạ.' | "
   "(7) 'Trà sâm tặng kèm cả nhà uống hằng ngày đều được, vừa tiện vừa thêm phần bồi bổ ạ.' | "
   "(8) 'Chương trình quà tặng khách mới bên em áp dụng đến hết 31/12 thôi ạ, anh/chị lấy combo bây giờ là được hưởng trọn quà ạ.' | "
   "(9) 'Lấy combo nhiều hộp anh/chị vừa dùng vừa có sẵn để biếu người thân, lại được nhận thêm quà ạ.' (khi khách có nói mua biếu/mua cho nhiều người). "
   "RIÊNG chương trình MUA 15 TẶNG 1 (từ 15 hộp Hồng sâm lát, tặng 1 hộp cùng loại — khách đặt 10–14 hộp có thể mời lên 15 hộp): được dùng thêm câu "
   "'Lấy 15 hộp vừa đảm bảo đủ liệu trình cho mình dùng không bị gián đoạn, lại vừa được giá ưu đãi tiết kiệm thêm ạ.' "
   f"Khách đặt 1 hộp Hồng sâm lát: 'Dạ em cảm ơn anh/chị đã để lại thông tin đặt hàng. Hiện bên em đang có ưu đãi {lat_rule(2)['label']} (2 hộp) giá {vnd(LAT_PRICE * 2)} được tặng ngay {lat_rule(2)['gift']}. [câu đệm] "
   "Anh/chị có muốn lấy luôn Combo 2 hộp để dùng đủ liệu trình 1 tháng không ạ? 😊'. "
   f"Khách đặt 2 hộp: 'Dạ anh/chị ơi, nếu anh/chị lấy luôn {lat_rule(4)['label']} (4 hộp, đủ liệu trình 2 tháng) giá {vnd(LAT_PRICE * 4)} thì được tặng kèm {lat_rule(4)['gift']}. [câu đệm] "
   "Em đăng ký luôn combo này cho anh/chị nhé?'. "
   f"Khách đặt 4 hộp: có thể mời {lat_rule(6)['label']} (6 hộp, đủ liệu trình cơ bản 3 tháng) giá {vnd(LAT_PRICE * 6)}, tặng {lat_rule(6)['gift']} + câu đệm. "
   "Khách đồng ý → cập nhật số lượng, giá, quà theo combo mới; từ chối → giữ đơn cũ, sang xác nhận đơn."),
 "returning_quote": "Chốt 14/10 + 23/10 — khách TỰ nói đã từng dùng/mua ĐÚNG Hồng sâm lát và hỏi mua lại Hồng sâm lát (từng dùng sản phẩm khác → báo combo khách mới): cảm ơn khách đã tin dùng lại; báo giá 1 hộp + ưu đãi tri ân khách hàng thân thiết (lấy đúng bảng programs.returning_customer, mỗi mốc 1 dòng 🎁; mua 1 hộp được chọn dầu nóng Khương Thảo Đan 10ml hoặc 1 hộp Trà sâm 1700 loại 10 gói); KHÔNG báo combo khách mới; 1 câu chốt hỏi số lượng. Chốt đơn bằng build_order customer_type=returning.",
 "origin": "Chốt 15/10 (chị Nga) — khách hỏi nguồn gốc sâm / sâm ở đâu ra: 'Dạ nguyên liệu sâm trước khi đưa vào nhà máy Thái Minh để sản xuất sẽ được kiểm soát nghiêm ngặt chất lượng đầu vào. Hồng sâm Thái Minh là công trình chuyển giao từ Viện Nghiên cứu Sâm và Dược liệu Việt Nam (VIGH), nên anh/chị hoàn toàn yên tâm về chất lượng ạ.' KHÔNG tự nhắc vườn sâm. CHỈ KHI khách hỏi THẲNG 'Thái Minh có vườn sâm không / sâm có phải tự trồng không' → 'Dạ Thái Minh có vườn trồng sâm tại Sìn Hồ – Lai Châu và Lâm Đồng ạ. Nguyên liệu sâm đưa vào sản xuất đều có nguồn gốc rõ ràng, hóa đơn chứng từ đầy đủ và được kiểm soát chặt chẽ chất lượng đầu vào ạ.' (chốt 23/10: KHÔNG nói 'toàn bộ sâm đưa vào nhà máy đều trồng ở Sìn Hồ / Lai Châu') KHÔNG BAO GIỜ nói 'toàn bộ sâm do Thái Minh tự trồng'. Website samthaiminh.com.",
 "where_buy": "Chốt 14/10 — khách hỏi mua ở đâu / nhà thuốc nào có bán: gửi link tra điểm bán https://samthaiminh.com/diem-ban, đồng thời khuyến khích đặt online qua page để được giao tận nhà và hưởng ưu đãi tốt nhất.",
 "marketplace": "Khách nói mua trên sàn rẻ hơn: bên em chỉ đảm bảo nguồn gốc, hạn dùng, bảo quản khi mua trực tiếp công ty/cửa hàng; đặt hôm nay có ưu đãi + được kiểm tra hàng; sau khi mua được chuyên viên chăm sóc và áp dụng CTKM dành riêng cho khách hàng thân thiết. Không nêu tên shop trên sàn.",
 "positive_feedback": "Chốt 13/10 — khách khen sản phẩm dùng tốt (là khách đã dùng): KHÔNG vội báo giá, KHÔNG ép combo. Mẫu: 'Dạ em rất vui khi nghe phản hồi tốt từ anh/chị ạ! Hiện tại bên em đang có một số chương trình ưu đãi tri ân dành riêng cho khách hàng quen, không biết anh/chị có muốn tham khảo thêm để tiết kiệm chi phí cho đợt dùng tiếp theo không ạ?' Khách muốn → Hồng sâm lát: báo ưu đãi khách cũ theo bảng programs.returning_customer và chốt đơn như thường (build_order customer_type=returning); sản phẩm khác → xin SĐT để chuyên viên báo + [HANDOFF: khách cũ khen sản phẩm, muốn mua tiếp | SĐT | 2]. Bot KHÔNG nêu combo khách mới cho khách cũ.",
 "price_objection_switch": "Chốt 13/10 + 16/10 — dùng SAU khi đã thuyết phục giá trị ít nhất 2 lần với 2 ý khác nhau mà khách vẫn chê đắt / chưa đủ ngân sách, HOẶC NGAY KHI khách chê đắt kèm ý thôi không mua ('đắt quá thôi', 'thôi không mua nữa', 'để sau') — mời trước khi xin SĐT: đồng cảm → giới thiệu Nước Hồng sâm Thái Minh mật ong dạng túi (chốt 16/10: ƯU TIÊN mời DẠNG TÚI, KHÔNG nhắc dạng chai — khách hỏi chai mới nói) → báo giá + ưu đãi của hsmo-tui (lấy từ tool) → nhấn mạnh chất lượng Thái Minh → 1 câu hỏi mở. Mẫu 1: 'Dạ em rất hiểu việc cân đối ngân sách là rất quan trọng ạ. Nếu anh/chị muốn một giải pháp kinh tế hơn nhưng vẫn đảm bảo chất lượng uy tín từ thương hiệu Thái Minh, em xin giới thiệu dòng Nước Hồng sâm Thái Minh mật ong dạng túi, mỗi túi nhỏ tiện uống hằng ngày ạ.' (xuống dòng) 'Sản phẩm có mức giá dễ chịu hơn nhiều, hỗ trợ bồi bổ sức khỏe và tăng sức đề kháng mỗi ngày. Hiện sản phẩm đang có giá [giá] cùng ưu đãi [ưu đãi]. Anh/chị có muốn em gửi thông tin chi tiết để tham khảo không ạ?' Mẫu 2: 'Dạ em hoàn toàn chia sẻ với anh/chị ạ, việc đầu tư cho sức khỏe cũng cần phù hợp với kế hoạch chi tiêu hiện tại. Để anh/chị dễ dàng trải nghiệm trước, em gợi ý dòng Nước Hồng sâm Thái Minh mật ong dạng túi, mỗi túi nhỏ tiện uống hằng ngày ạ.' (xuống dòng) 'Đây là lựa chọn tiết kiệm mà vẫn giữ nguồn nguyên liệu hồng sâm chuẩn chất lượng từ Thái Minh. Giá hiện tại là [giá] (đang áp dụng [ưu đãi]). Anh/chị có muốn em tư vấn kỹ hơn về liệu trình này không ạ?' [giá], [ưu đãi] PHẢI lấy từ tool (gói hsmo-tui 20 túi; khách chê vẫn đắt mới báo hộp nhỏ 10 túi hsmo-tui-10).",
 "no_info": "Chốt 13/10 — câu hỏi không có trong dữ liệu, không trả lời được: KHÔNG suy đoán. 'Dạ em xin phép kiểm tra lại thông tin để tư vấn chính xác nhất cho anh/chị ạ. Em sẽ nhờ chuyên viên của Sâm Thái Minh liên hệ hoặc phản hồi lại anh/chị trong thời gian sớm nhất.' + [HANDOFF: câu hỏi ngoài tài liệu | SĐT | 2] (bot dừng chat).",
 "disease_no_guidance": "Chốt 13/10 — bệnh/tình trạng chưa có tài liệu (vd mới tai biến đang dùng thuốc chống đông dưới 6 tháng, viêm khớp dạng thấp, tuyến giáp khi chưa có tài liệu, mọi bệnh khác chưa có hướng dẫn): KHÔNG suy luận, KHÔNG khẳng định dùng được hay không. 'Dạ anh/chị, với trường hợp đang có [tên bệnh/triệu chứng] thì em chưa thể tư vấn phù hợp qua tin nhắn. Anh/chị vui lòng cho em xin số điện thoại để chuyên viên của Sâm Thái Minh liên hệ tư vấn kỹ hơn cho anh/chị nhé ạ.' + [HANDOFF: ... | SĐT | 3].",
 "deep_consult": "Chốt 13/10 — khách hỏi chi tiết / cần giải pháp cụ thể mà bot không phản hồi được: 'Dạ vấn đề này cần trao đổi kĩ hơn một chút, anh/chị cho em xin số điện thoại để em chuyển chuyên viên tư vấn gọi trực tiếp hoặc gửi thông tin chi tiết qua cho anh/chị nhé ạ!' + [HANDOFF: ... | SĐT | 2].",
 "accusation": "Chốt 13/10 — khách CÁO BUỘC (công ty lừa đảo, lừa gạt, bán hàng giả, bóc phốt, báo công an...) hoặc khiếu nại (thiếu gói, giao sai, tác dụng phụ) hoặc đòi đổi trả/hoàn tiền: đồng cảm ngắn theo đúng tình huống rồi chuyển ngay. Mẫu cáo buộc: 'Dạ, em đã ghi nhận phản ánh của anh/chị và đang kết nối ngay với chuyên viên để hỗ trợ giải quyết trực tiếp cho anh/chị ạ.' Mẫu sự cố: 'Dạ em rất tiếc về sự cố anh/chị gặp phải ạ. Em xin phép kết nối ngay với chuyên viên để xử lý gấp trường hợp này cho anh/chị nhé ạ!' + [HANDOFF: ... | SĐT | 4] (đổi trả: level 2). CẤM câu máy móc 'Rất tiếc, tôi không thể hỗ trợ bạn về vấn đề đó', 'I'm sorry, I can not help you with that'.",
 "reassure_fake": "Chốt 13/10 — khách chỉ LO LẮNG / muốn xác thực ('hàng có chính hãng không', 'lỡ mua hàng giả', 'sợ mua online bị lừa'): KHÔNG chuyển người. Trấn an: được kiểm tra hàng trước khi thanh toán (COD); có giấy công bố (kb_lookup product → registration); sản phẩm của Dược phẩm Thái Minh gần 15 năm; sâm có nguồn gốc rõ ràng, được kiểm soát chặt chẽ chất lượng đầu vào (KHÔNG nói 'tự trồng', không tự nhắc vườn); kiểm tra tem niêm phong, quét iCheck. KHÔNG nêu chính sách đổi trả (chốt 23/09).",
 "closing": "Chốt 13/10 — kết thúc hội thoại (đã chốt đơn, hoặc khách chào tạm biệt) luôn bằng lời cảm ơn hoặc chúc sức khỏe, vd 'Dạ em cảm ơn anh/chị đã tin tưởng Sâm Thái Minh, chúc anh/chị và gia đình thật nhiều sức khỏe ạ 🌿'. Sau khi chốt đơn không nhắn thêm gì khác.",
 "no_ginseng_smell": "Chốt 15/10 (anh Huy) — khách hỏi sao Hồng sâm không có mùi sâm / không thơm như sâm Hàn: 'Dạ do đặc thù 2 loại Sâm Hàn Quốc và Sâm Việt Nam thành phần hoạt chất là khác nhau ạ. Sâm Hàn Quốc nhiều tinh dầu hơn nên anh/chị sẽ thấy rõ mùi. Còn Sâm Việt Nam ít tinh dầu hơn.' (xuống dòng) 'Tinh dầu không phải thành phần mang lại tác dụng của sâm, Saponin mới là thứ mang lại tác dụng chính ạ. Saponin không có mùi đặc trưng rõ mà chủ yếu ở vị: đắng nhẹ, ngọt hậu tùy từng loại, thơm nhẹ chứ không rõ như tinh dầu ạ.' KHÔNG giải thích bằng nhiệt độ hấp sấy.",
 "vat_invoice": "Chốt 15/10 (chị Nga) — khách hỏi có xuất hóa đơn VAT / hóa đơn đỏ không: 'Dạ có ạ, Sâm Thái Minh có xuất hóa đơn VAT cho cả khách hàng cá nhân và công ty ạ. Giá sản phẩm đã bao gồm VAT nên anh/chị không phải trả thêm ạ.' (xuống dòng) 'Anh/chị gửi giúp em: tên công ty (hoặc họ tên cá nhân), mã số thuế (nếu có), địa chỉ ghi trên hóa đơn và email nhận hóa đơn điện tử, em ghi chú vào đơn để bên em xuất cho anh/chị nhé ạ.' Ghi đủ thông tin hóa đơn vào ghi chú đơn / lý do HANDOFF level 1. KHÔNG hứa ngày gửi hóa đơn cụ thể.",
 "breastfeeding": "Chốt 15/10 (chị Nga) — người dùng ĐANG CHO CON BÚ (hỏi bất kỳ sản phẩm nào): 'Dạ trong thời gian đang cho con bú, chị chưa nên dùng các sản phẩm sâm ạ. Khi bé cai sữa, chị nhắn em để em tư vấn sản phẩm phù hợp nhé ạ. Nếu chị muốn mua làm quà bồi bổ cho bố mẹ hoặc người thân, em tư vấn ngay cho chị ạ.' KHÔNG gợi ý sản phẩm nào cho mẹ đang cho con bú, KHÔNG nói tiết sữa/lợi sữa, không chuyển chuyên viên.",
 "credit_sale": "Chốt 23/10 (chị Nga: công ty KHÔNG bán nợ) — khách hỏi BÁN CHỊU / mua chịu / bán nợ / trả sau / trả góp ('bán chiu', 'mua chiu'): 'Dạ hiện bên em chưa áp dụng hình thức bán chịu ạ. Bên em giao hàng tận nơi, anh/chị nhận hàng, kiểm tra đúng sản phẩm rồi mới thanh toán cho bên giao hàng ạ.' Khách nói không có tiền / chưa đủ tiền → đồng cảm, mời 1 lần Nước Hồng sâm Thái Minh mật ong dạng túi (price_objection_switch) hoặc xin SĐT để báo khi có chương trình mới (soft_ask_phone). KHÔNG hiểu nhầm 'chịu/chiu' thành 'rượu', KHÔNG giới thiệu Rượu sâm.",
 "price_quote_duongsam": ("Duyệt 21/10 (chị Nga) — khách hỏi giá / chương trình Dương Sâm Linh Đan → đúng 3 phần, 1 lượt: "
   f"(1) câu dẫn: 'Dạ Dương Sâm Linh Đan giá {vnd(DS_PRICE)}/hộp 10 viên, mỗi ngày anh dùng 1 viên lúc 8–9 giờ tối. Liệu trình khuyên dùng 3 tháng (khoảng 9 hộp) để hiệu quả bền vững ạ.'; "
   "(2) 'Chương trình tri ân khách hàng mới:' + mỗi gói 1 dòng: " + DS_COMBO_TXT + " + dòng '✅ Miễn phí vận chuyển toàn quốc, nhận hàng kiểm tra rồi mới thanh toán'; "
   "(3) ĐÚNG 1 câu chốt: 'Anh muốn bắt đầu liệu trình 1 tháng (3 hộp) trước, hay lấy luôn liệu trình 3 tháng (9 hộp) cho đủ liệu trình cơ bản ạ?'. "
   "KHÔNG liệt kê dòng 1 hộp, 2 hộp (chỉ nói khi khách hỏi mua lẻ / ít hộp / dùng thử / chê đắt: 1 hộp không quà, 2 hộp tặng 1 Trà sâm 1700 loại 10 gói). "
   "Mốc 6 hộp: ƯU TIÊN báo tặng 1 chai Nước Hồng sâm mật ong; khách không thích Nước Hồng sâm mới đổi 2 hộp Bổ Gan + 1 Trà sâm 10 gói. "
   "Khách mới từ 10 hộp trở lên: quà mốc 9 hộp, KHÔNG chuyển nhân viên xin thêm ưu đãi."),
 "returning_quote_duongsam": "Duyệt 21/10 — khách TỰ nói đã từng dùng ĐÚNG Dương Sâm Linh Đan (chốt 23/10: từng dùng sản phẩm khác → báo CTKM khách mới): cảm ơn anh đã tin dùng lại; báo giá 1 hộp + ưu đãi tri ân khách hàng thân thiết lấy đúng bảng programs.returning_customer (mốc 4 / 7 / 10 / 15 hộp, mỗi mốc 1 dòng 🎁; 2, 3, 6, 9 hộp quà như khách mới); 1 câu chốt hỏi số lượng; chốt đơn bằng build_order customer_type=returning.",
 "price_why_duongsam": "Duyệt 21/10 (chị Nga) — khách chê đắt Dương Sâm, dùng ĐÚNG 2 câu, mỗi lần 1 câu, KHÔNG chuyển sang Nước Hồng sâm: LẦN 1: 'Dạ em hiểu anh ạ. So với dùng thuốc tây hay tiêm hormone thì chi phí Dương Sâm Linh Đan nhẹ nhàng hơn nhiều, lại từ thảo dược nên anh yên tâm hơn, bồi bổ từ gốc. Tính ra mỗi ngày chỉ khoảng bằng 2 ly cà phê thôi ạ.' | LẦN 2: 'Dạ loại rẻ mà dùng vài tháng không cải thiện thì anh vừa mất tiền vừa mất thời gian ạ. Dương Sâm Linh Đan dùng khoảng 10–14 ngày nhiều anh đã thấy tỉnh táo hơn, đỡ đau lưng mỏi gối, buổi sáng chào cờ nhạy hơn ạ.' Vẫn chưa mua → soft ask SĐT 1 lần rồi cảm ơn.",
 "new_product_doubt": "Duyệt 21/10 — khách hỏi uy tín / sản phẩm mới, sợ không đúng quảng cáo: thừa nhận trước ('Vâng anh ạ, sản phẩm mới thì anh cũng cần tìm hiểu kỹ thông tin ạ'), rồi: 'Dương Sâm Linh Đan là sản phẩm được Thái Minh đầu tư rất nhiều chất xám, được sản xuất và phân phối bởi Công ty Dược phẩm Thái Minh, thương hiệu gần 15 năm, đã có nhiều sản phẩm nổi tiếng như Khương Thảo Đan, Vương Bảo, Bình Vị...' + công thức Sâm Lai Châu + Cao xương dê, 'Khỏe bên trong, mạnh bên ngoài'; dùng đủ liệu trình 3 tháng hiệu quả bền vững hơn.",
 "doctor_htk": "Duyệt 21/10 — CHỈ khi khách HỎI có bác sĩ / chuyên gia tư vấn không: 'Dạ sản phẩm Dương Sâm Linh Đan đang được các bác sĩ trực tiếp tư vấn và chia sẻ trên các kênh đài uy tín như VOV, truyền hình Quốc Phòng... ạ.' KHÔNG nêu tên bác sĩ cụ thể; KHÔNG tự nhắc bác sĩ khi khách không hỏi.",
 "shy_customer": "Khách ngại chia sẻ chuyện sinh lý: không ép kể chi tiết, hỏi mở: 'Dạ anh thấy sức khỏe, sinh lý so với trước có thay đổi gì không ạ?' hoặc nêu nhẹ các tình trạng hay gặp ở độ tuổi của anh rồi lồng ghép công dụng (luôn 'hỗ trợ').",
 "flirt_redirect": "Khách nhắn khiêu gợi / trêu ghẹo, hỏi ngoài phạm vi: 'Dạ em xin phép chỉ hỗ trợ các thông tin về sản phẩm và sức khỏe ạ. Anh cần tư vấn gì thêm về Dương Sâm Linh Đan thì nhắn em nhé.' Không đáp lại nội dung khiêu gợi, không hứa gặp riêng.",
 "pack_vs_doctor": "Khách hỏi vỏ hộp ghi người cao huyết áp/tim mạch không dùng: 'Dạ vâng anh ạ, trên bao bì bắt buộc phải ghi để phòng ngừa rủi ro với những người huyết áp cao đang dao động nhiều mà chưa dùng thuốc kiểm soát ạ. Thực tế sản phẩm bào chế từ thảo dược, trong đó Sâm Lai Châu hỗ trợ cải thiện tuần hoàn, hỗ trợ điều hòa huyết áp. Vì vậy nếu anh bị cao huyết áp hoặc tim mạch nhưng đang ổn định, đang dùng thuốc bác sĩ kê thì vẫn dùng được ạ.' + vẫn hỏi chỉ số huyết áp gần nhất (≤150 dùng được, >150 chuyển chuyên viên).",
 "no_result_complaint": "Khách dùng 1 tháng chưa thấy hiệu quả: (1) tiếc vì anh chưa cảm nhận được hiệu quả; (2) sản phẩm thảo dược cần kiên trì theo liệu trình, bệnh kèm (tiểu đường, huyết áp…) ảnh hưởng tới sinh lý; (3) kiên trì đủ liệu trình, hạn chế rượu bia, thuốc lá, tập thể dục. Khách bức xúc nhiều → xin SĐT + [HANDOFF: khách phàn nàn chưa thấy hiệu quả | SĐT | 2].",
 "discreet_delivery": "Duyệt 21/10 — khách hỏi giao hàng kín đáo: 'Dạ anh yên tâm ạ, trên đơn hàng bên em chỉ ghi tắt tên sản phẩm là DSLĐ nên rất kín đáo, không bị lộ ạ.'",
 "bo_gan_gift": "Bổ Gan Thái Minh CHỈ là quà tặng kèm Dương Sâm Linh Đan, không chào bán riêng: hỗ trợ thanh nhiệt, giải độc và bảo vệ gan, hỗ trợ tăng cường chức năng gan, hạn chế tác hại của rượu bia; ngày 4 viên chia 2 lần. Khách hỏi giá Bổ Gan riêng → chuyển nhân viên.",
 "trial_request_duongsam": "Page Dương Sâm — khách xin dùng thử: 'Dạ hiện bên em chưa có chương trình dùng thử ạ. Anh có thể bắt đầu với 1 hộp, nhận hàng kiểm tra nguyên hộp rồi mới thanh toán ạ.' KHÔNG gợi ý Nước Hồng sâm, không hứa hoàn tiền.",
 "expert_referral": 'Dạ câu hỏi của anh/chị cần chuyên viên có chuyên môn tư vấn mới chính xác được ạ. Anh/chị cho em xin số điện thoại, chuyên viên bên em sẽ gọi lại hỗ trợ anh/chị sớm ạ.',
}
phone_rules = {"principle": "Không hội thoại nào kết thúc mà chưa thử xin SĐT 1 lần. SĐT là lưới đỡ ở cửa ra, không hỏi sớm.",
 "S1_order": "Chốt đơn: xin tên + SĐT + địa chỉ, validate qua build_order.",
 "S2_exit": "Khách sắp rời: soft_ask_phone ĐÚNG 1 LẦN; từ chối thì cảm ơn và dừng.",
 "S3_escalation": "Mọi ca chuyển nhân viên: xin SĐT; chưa cho thì bám thêm đúng 1 lần; vẫn không cho → vẫn chèn [HANDOFF] không SĐT.",
 "no_self_close": "CẤM tự kết thúc khi khách chưa chốt và chưa từ chối hẳn."}
# Chốt 13/10: sản phẩm trọng tâm theo bài viết/quảng cáo và theo page (xem engine.py rule 0)
focus_policy = {
 "rule": "Khách hỏi chung chung, chưa nói rõ sản phẩm (giá bao nhiêu, dùng thế nào, có tốt không...) → trả lời theo SẢN PHẨM TRỌNG TÂM của hội thoại. "
         "Khách đến từ bài viết/quảng cáo của sản phẩm A → sản phẩm trọng tâm là A. Khách vãng lai không rõ nguồn → page Sâm Thái Minh: Hồng sâm Việt Nam Thái Minh dạng lát; "
         "page Dương Sâm Linh Đan: Dương Sâm Linh Đan. Khách nói rõ sản phẩm khác → trả lời đúng sản phẩm khách hỏi.",
 "page_default": {"sam_thai_minh": "hsvn_lat", "duong_sam_linh_dan": "duong_sam"},
}

kb = {"_meta": {"brand": "Sâm Thái Minh", "company": "Công ty Cổ phần Sâm và Dược liệu quý Thái Minh (tên thường gọi: Sâm Thái Minh) — thuộc hệ thống Dược phẩm Thái Minh (hơn 15 năm); sản xuất: Công ty Cổ phần Công nghệ Cao Thái Minh; vườn sâm: Công ty Cổ phần Thái Minh Panax",
  "tagline": "Mang Quốc bảo Sâm Việt Nam đến với mọi nhà",
  "mission": "Cung cấp các sản phẩm có giá trị bổ dưỡng cho sức khỏe từ 'Quốc bảo' Sâm Việt Nam đến với mọi nhà với giá cả phải chăng nhất; góp phần phát triển kinh tế, an sinh cho đồng bào vùng cao.",
  "core_values": "Khách hàng là trung tâm (chăm sóc khách như chăm sóc người thân); Chất lượng thật; Giữ lời hứa; Trách nhiệm; Học hỏi và sáng tạo; Mối quan hệ tốt đẹp.",
  "working_hours": "08h00–21h00 hằng ngày (ngoài giờ: bot vẫn tư vấn; ca cần chuyên viên → báo chuyên viên liên hệ trong giờ làm việc)",
  "website": "https://samthaiminh.com",
  "channels": "Facebook Sâm Thái Minh: facebook.com/thaiminhpanax; Dương Sâm Linh Đan: facebook.com/duongsamlinhdan; TikTok: @thaiminhpanax; Zalo OA: zalo.me/2044121091984912860",
  "hotline": "1800 1120", "hotline_alt": "1800 8396", "source_date": "2026-10-13", "currency": "VND",
  "status": "KB NHÁP v0.1.34-STM (19/10: bot Sâm Thái Minh riêng, Dương Sâm tách repo khác) — v0.1.35 (19/10: CTKM Dương Sâm Linh Đan khách mới + khách cũ 01/07–31/12/2026; quà Bổ Gan Thái Minh) — v0.1.32 (17/10: 4 câu chốt đơn mới sau báo giá Hồng sâm lát) — v0.1.28 (16/10: câu tiểu đường lo mật ong diabetes_honey — dùng chữ 'hỗ trợ kiểm soát đường huyết'; Dương Sâm huyết áp thấp dùng được; giờ làm việc 08h–21h mọi ngày kể cả T7, CN) — v0.1.27 (16/10: câu ngoài giờ làm việc off_hours) — v0.1.26 (16/10 16:20: khách muốn chat với người → chuyển ngay không bắt để SĐT, không tự mở lại cho bot) — v0.1.23 (16/10 15:30: chị Nga sửa bảng an toàn — Dương Sâm huyết áp cao ≤150/>150, Nước HS suy thận 3–4 hỏi bác sĩ, lát mới ghép thận chuyển, hộp 50 gói có hàng không CTKM) — v0.1.22 (16/10 chiều, chị Nga test Pancake: viêm loét dạ dày; suy thận 3–4 hỏi bác sĩ; Nước HS tiểu đường dùng được; huyết áp không so sánh sâm Hàn) — v0.1.21 (16/10 test Pancake: cách dùng tiểu đường Hồng sâm lát ghi rõ sáng 1/2 + trưa 1/2, không lẫn với cách dùng thuốc chống đông; bỏ 'thấm sâu'; không gọi chị/anh + tên Facebook khi chưa rõ) — v0.1.20 (16/10: mời Nước Hồng sâm ưu tiên dạng túi, dạng chai khách hỏi mới nói; chê đắt kèm ý thôi → mời Nước Hồng sâm ngay) — v0.1.17 (15/10: góp ý anh Huy — bỏ tự trồng/gấp 3 lần sâm Hàn/50% MR2, huyết áp nói mềm, thuốc tây cách 2 giờ, cho con bú không dùng sản phẩm nào, Long Sâm huyết áp chưa ổn định chuyển, phình động mạch chủ hỏi bác sĩ, thăm vườn xin SĐT, FAQ mùi sâm, hóa đơn VAT) — v0.1.16 (14/10: chị Nga duyệt bộ não — bảng an toàn Dương/Long Sâm, mẹ sau sinh từ 6 tháng, gói túi 10, ship Trà/Tam Sâm/Đông trùng dưới 1 triệu, CTKM khách cũ Hồng sâm lát) — v0.1.15 (13/10 tối: câu trả lời huyết áp có giải thích chuyên môn; tai biến do xuất huyết chuyển chuyên viên) — v0.1.14 (13/10 chiều: MR2 theo nghiên cứu Đại học Dược Kyoto; người ung thư đang hóa trị dùng được Hồng sâm; freeship mọi sản phẩm từ 1 hộp trừ Hồng sâm dạng nước; quà trà ghi rõ loại 10/20 gói; câu mẫu mới) — trước đó v0.1.13 cho bot Sâm Thái Minh — dựng từ file 'Sâm Thái Minh 1.xlsx', giấy công bố sản phẩm và thông tin chị Nga chốt qua chat 23/09–13/10/2026. 13/10: huyết áp cao/thấp/chưa ổn định đều dùng được Hồng sâm Thái Minh; bỏ câu 'không phải thuốc' mặc định (chỉ khuyên duy trì thuốc khi khách nói đang dùng thuốc tây); FAQ chai 175ml là chai nhựa; sản phẩm trọng tâm theo bài viết/quảng cáo/page.",
  "content_reviewer": "Chị Nga (ngant@tmp.vn) — người duyệt nội dung nhãn hàng. Trạng thái: CHỜ DUYỆT.",
  "registration": {"hsvn_lat": "08/CNCTHAIMINH/2025", "hsmo_chai": "11/CNCTHAIMINH/2025", "hsmo_tui": "11/CNCTHAIMINH/2025", "duong_sam": "3496/2024/ĐKSP", "long_sam": "6193/2024/ĐKSP", "tam_sam_dan": "7514/2024/ĐKSP", "dong_trung": "XNCB 10016/2021/ĐKSP; GPQC 88/2022/XNQC-ATTP"},
  "disclaimer": "Thực phẩm này không phải là thuốc và không có tác dụng thay thế thuốc chữa bệnh.",
  "disclaimer_policy": "Chốt 13/10 (chị Nga): bot KHÔNG tự nói câu disclaimer này. Chỉ dùng khi khách hỏi thẳng 'có thay được thuốc không / bỏ thuốc được không' (trả lời thật: không thay thuốc).",
  "store": "Cửa hàng Sâm Thái Minh: 92 Trung Kính, Cầu Giấy, Hà Nội",
  "farm": "Vườn sâm Thái Minh: Sìn Hồ farm (Sìn Hồ, Lai Châu) và vườn Lâm Đồng; có thu mua thêm sâm có hóa đơn đầy đủ. Chốt 15/10: KHÔNG tự nhắc vườn — chỉ nói khi khách hỏi thẳng (scripts_approved.origin); không còn cho thuê phòng nghỉ; khách muốn thăm → xin SĐT"},
 "products": P, "need_map": need_map, "compliance": compliance, "shipping": shipping, "pharmacy_policy": pharmacy_policy,
 "programs": programs, "combo_tiers_note": combo_tiers_note, "customer_segments": customer_segments, "escalation": escalation,
 "scripts_approved": scripts_approved, "phone_rules": phone_rules, "focus_policy": focus_policy}
json.dump(kb, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("OK", len(P), "products,", sum(len(p["packages"]) for p in P.values()), "SKUs,", len(RULES), "promo rules")
