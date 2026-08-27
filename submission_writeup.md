# Bài viết nộp Lab 25 — GPU FinOps

## Kết quả chính

Có 2.400 request với 7.533.027 token.

- Chi phí inference trước tối ưu: **$48,87/ngày** (**$6,488/1M token**).
- Sau tối ưu bằng cascade, caching và batch: **$8,48/ngày** (**$1,126/1M token**).
- Tiết kiệm inference: **82,6%**.
- Tổng chi phí GPU giảm từ **$27.133** xuống **$14.626/tháng**.
- Tổng tiết kiệm: **$12.507/tháng**, tương đương **46%**.

## Phân tích FinOps

Hai GPU có GPU-Util cao nhưng MFU thấp:

- `gpu-h100-4`: GPU-Util 98,2%, MFU 19,4%.
- `gpu-a10g-1`: GPU-Util 96,9%, MFU 26,8%.

GPU idle gây lãng phí **$20/ngày**, tương đương **$600/tháng**.

Kết hợp Spot cho workload có thể gián đoạn và Reserved cho workload ổn định giúp tiết kiệm **39,1%** chi phí mua GPU. Ngưỡng hòa vốn của Reserved là **55% utilization**.

Tag coverage đạt **92%**, đủ điều kiện chargeback. File FOCUS export có **50 dòng**.

## Hai phần mở rộng

### 1. Kiểm tra hiệu quả cache

Đã thêm hàm `cache_is_worth_it()`. Ngưỡng hòa vốn là **1,11 lượt đọc**, dữ liệu thực tế đạt **3,14 lượt đọc**, nên sử dụng cache là có lợi.

### 2. Ngân sách reasoning

Reasoning chiếm **201/2.400 request**, tương đương **8,4%**, tiêu tốn **$1,40/ngày** và **29.787,7 Wh/ngày**. Mức này đã thấp hơn giới hạn 10%, nên mô phỏng giảm thêm **0%**.

## Đề xuất

1. Điều tra hai GPU có GPU-Util lie và tối ưu workload.
2. Dùng Spot cho job có checkpoint, Reserved cho workload ổn định.
3. Duy trì tag team/project và theo dõi cache, reasoning hàng tháng.

Các số liệu là snapshot tháng 06/2026 và cần cập nhật trước khi áp dụng thực tế.
