---
name: hep-redesign
description: Điều phối đội Hép Bookstore (thiết kế, lập trình, QA giao diện, kiểm toán code) theo màu logo be, navy, cam và hiệu ứng phong phú, kể cả 3D three.js. Dùng khi được yêu cầu đổi giao diện, thêm hiệu ứng hoặc 3D, làm đẹp trang shop hoặc quản trị, chạy lại hay sửa tiếp bản thiết kế, "chỉ làm lại trang POS", "QA lại giao diện", "cho agent kiểm soát lại hết", "review toàn bộ trước khi bàn giao", "cập nhật theo phản hồi của Nga". Bản thân việc sửa webhook, model, logic kho thì làm trực tiếp, nhưng kiểm lại chúng thì dùng bước kiểm toán của skill này.
---

# Điều phối thiết kế lại giao diện Hép Bookstore

**Chế độ chạy:** uỷ quyền subagent theo đường ống thiết kế, lập trình, kiểm thử, có vòng sửa. Các bước phụ thuộc nhau theo thứ tự và chỉ cần nhận kết quả một lần, nên không cần agent hội thoại liên tục hay Workflow.

| Agent | File định nghĩa | Model | Skill dùng |
| --- | --- | --- | --- |
| hep-ui-designer | `.claude/agents/hep-ui-designer.md` | opus | hep-brand-ui |
| hep-frontend-dev | `.claude/agents/hep-frontend-dev.md` | opus | hep-brand-ui |
| hep-ui-qa | `.claude/agents/hep-ui-qa.md` | sonnet | hep-ui-qa-check |
| hep-code-auditor | `.claude/agents/hep-code-auditor.md` | opus | (đọc code, chạy test) |

Việc có 3D: designer và dev đọc thêm `hep-brand-ui/references/threejs-recipes.md`; three.js đã vendor ở `static/vendor/three/`.

Gọi agent bằng `subagent_type` đúng tên. Nếu phiên hiện tại chưa nạp được loại agent mới (file tạo trong phiên), gọi `general-purpose` với prompt mở đầu: "Đọc `.claude/agents/<tên>.md` và làm đúng vai trò trong đó."

## Bước 0. Xác định loại yêu cầu
- Chưa có `_workspace/01_designer_spec.md`: chạy đủ bước 1 đến 4.
- Có đặc tả và người dùng chỉ muốn sửa một phần (một trang, một hiệu ứng, màu): bỏ bước 1 nếu đặc tả không đổi, hoặc gọi designer chỉ sửa đúng phần đó; rồi bước 2 đến 4.
- Người dùng chỉ hỏi "kiểm lại" giao diện: chỉ bước 3. "Kiểm soát lại hết", "review toàn bộ": bước 3 và bước 3b song song.
- Thêm 3D hoặc đợt hiệu ứng mới trên đặc tả cũ: designer viết phần bổ sung `_workspace/0N_designer_<chủ đề>.md` (không ghi đè đặc tả gốc), rồi bước 2 đến 4.
- Yêu cầu mới hoàn toàn (đổi thương hiệu): chuyển `_workspace/` thành `_workspace_<YYYYMMDD-HHMM>/` rồi chạy lại từ đầu.
- Làm trên nhánh git riêng `redesign/...`, không commit thẳng lên `master`.

## Bước 1. Thiết kế
Gọi `hep-ui-designer`. Đầu vào: yêu cầu của người dùng nguyên văn, đường dẫn repo. Đầu ra: `_workspace/01_designer_spec.md`. Đọc lướt đặc tả trước khi qua bước 2: phải có token, đặc tả theo trang, danh sách việc đánh số.

## Bước 2. Lập trình
Gọi `hep-frontend-dev` với đường dẫn đặc tả. Đầu ra: code trong repo và `_workspace/02_dev_changelog.md`. Khối lượng lớn (khoảng 35 template) thì chia hai lượt tuần tự: lượt A gồm token, `base.html`, `motion.js`, trang shop; lượt B gồm `management/*`, POS, quét mã. Không chạy song song hai lượt vì cùng sửa `app.css`.

## Bước 3. Kiểm thử
Gọi `hep-ui-qa`. Đầu ra: `_workspace/03_qa_report.md` và ảnh trong `_workspace/qa/shots/`.

## Bước 3b. Kiểm toán code (song song với bước 3)
Gọi `hep-code-auditor` cùng lúc với `hep-ui-qa` (một tin nhắn, hai lệnh gọi) vì cả hai chỉ đọc và chạy test, không sửa code. Đầu ra: `_workspace/06_auditor_report.md`. Hai agent cùng chạy `manage.py test` trên CSDL test riêng nên không đụng nhau.

## Bước 4. Vòng sửa
- `KẾT LUẬN: PASS`: sang bước 5.
- `FAIL`: gọi lại `hep-frontend-dev` kèm đường dẫn báo cáo, chỉ sửa mục FAIL, rồi QA lại. Tối đa 2 vòng.
- Auditor báo FAIL ở Python (tiền, kho, quyền): người điều phối tự sửa hoặc giao một agent `general-purpose` có test kèm; không giao cho `hep-frontend-dev` vì agent đó bị cấm sửa models, views, services. Sau khi sửa, chạy lại auditor chỉ cho các mục FAIL. Sau 2 vòng còn FAIL thì dừng và báo người dùng các mục còn lại.
- Nếu QA báo lỗi do chính đặc tả (ví dụ màu không đạt tương phản), gọi designer sửa đặc tả trước.

## Bước 5. Bàn giao
Tự chạy lại `python3 manage.py test shop` và `lint_ui.py` để xác nhận, không chỉ tin báo cáo. Báo người dùng: đã đổi gì, ảnh chụp tiêu biểu, cảnh báo còn lại, việc cần khách cung cấp (logo gốc, ảnh bìa thật). Commit trên nhánh chỉ khi người dùng yêu cầu.

## Truyền dữ liệu
Qua file trong `_workspace/`, đặt tên `{bước}_{agent}_{sản phẩm}`. Giữ lại sau khi xong để đối chiếu.

## Lỗi
- Agent lỗi một lần: gọi lại một lần với cùng đầu vào. Lỗi lần hai: dừng bước đó, ghi vào báo cáo cuối.
- Hết hạn mức, mất quyền, bị từ chối quyền: không thử lại. Mở file đầu ra dở dang, ghi rõ đã tới đâu, báo người dùng.
- Không tự bịa nội dung thay agent bị dừng. Chỉ điền điều đã tự kiểm chứng.

## Kịch bản kiểm thử
**Bình thường:** "đổi giao diện theo màu logo, nhiều hiệu ứng" → designer viết đặc tả → dev sửa lượt A, B → QA PASS → báo cáo kèm ảnh.
**Lỗi:** QA báo FAIL vì `pos.js` còn `alert()` và tương phản `--orange-ink` 4.2:1 → dev sửa `pos.js`; designer chỉnh `--orange-ink` sậm hơn trong biên độ skill → dev cập nhật token → QA PASS ở vòng 2.
**3D:** "nạp three.js cho hiệu ứng lồng lộn và cho agent kiểm soát lại hết" → designer viết `05_designer_three_spec.md` theo threejs-recipes → dev làm `three-stage.js` và các cảnh → QA (lint 3D, E2E canvas bật/tắt) song song auditor → sửa → bàn giao.
**Sửa một phần:** "chỉ làm lại trang POS cho dễ bấm hơn" → bỏ bước 1 toàn phần, designer chỉ cập nhật mục POS → dev → QA.
