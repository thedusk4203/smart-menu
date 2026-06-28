# File: backend/app/modules/nutrition/constants.py
# Hằng số dùng chung cho module nutrition.
#
# Mục đích (P1 review D-04/D-09): gom mọi "magic number" của công thức dinh
# dưỡng vào MỘT nơi, để công thức tự tài liệu hoá và để KHOẢNG hợp lệ
# (age/weight/height) chỉ khai báo một lần — calculator.py dùng để validate,
# schemas.py dùng cho Field(ge=, le=) — tránh lệch nhau khi chỉnh.
#
# Thuần Python, không phụ thuộc framework.
from __future__ import annotations


# ---------------------------------------------------------------------------
# Khoảng hợp lệ của hồ sơ (dùng CHUNG cho schema Pydantic và calculator)
# ---------------------------------------------------------------------------

AGE_MIN, AGE_MAX = 15, 100
WEIGHT_MIN_KG, WEIGHT_MAX_KG = 30.0, 300.0
HEIGHT_MIN_CM, HEIGHT_MAX_CM = 100.0, 250.0


# ---------------------------------------------------------------------------
# Hệ số công thức Mifflin-St Jeor tính BMR
#   Nam:  10*kg + 6.25*cm − 5*tuổi + 5
#   Nữ:   10*kg + 6.25*cm − 5*tuổi − 161
# ---------------------------------------------------------------------------

class MifflinStJeor:
    WEIGHT_COEFF = 10.0
    HEIGHT_COEFF = 6.25
    AGE_COEFF = 5.0
    MALE_OFFSET = 5.0
    FEMALE_OFFSET = -161.0


# ---------------------------------------------------------------------------
# Năng lượng trên mỗi gram đa lượng (Atwater) — đổi calo ↔ gram
# ---------------------------------------------------------------------------

KCAL_PER_G_PROTEIN = 4
KCAL_PER_G_CARB = 4
KCAL_PER_G_FAT = 9


# ---------------------------------------------------------------------------
# Ngưỡng cảnh báo an toàn + ngưỡng bất khả thi
# ---------------------------------------------------------------------------

BMI_UNDERWEIGHT = 18.5
BMI_OBESE = 30.0
CALORIES_TOO_LOW = 1200
CALORIES_TOO_HIGH = 4000

# Dưới mức này, việc chia macro là vô nghĩa -> đánh dấu bất khả thi.
MINIMUM_SAFE_CALORIES = 800
