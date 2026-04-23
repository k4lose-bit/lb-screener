"""
주달 엑셀 → 테마 딕셔너리 추출기
────────────────────────────────
실행: python extract_theme_map.py
결과: theme_map.py 파일 생성 (LB 스크리너에 붙여넣기용)
"""

import pandas as pd
import glob
import os

# 엑셀 파일 자동 탐색
files = glob.glob("주달_테마별종목_*.xlsx")
if not files:
    print("❌ 주달_테마별종목_*.xlsx 파일을 찾을 수 없습니다.")
    print("   C:\\lb_screener 폴더에 엑셀 파일이 있는지 확인해주세요.")
    exit()

xlsx_file = sorted(files)[-1]  # 가장 최신 파일
print(f"✓ 파일 발견: {xlsx_file}")

# 시트3 (LB접목용) 읽기
df = pd.read_excel(xlsx_file, sheet_name="LB접목용")
print(f"✓ 종목 수: {len(df)}개")
print(f"✓ 컬럼: {list(df.columns)}")

# 종목코드 → 테마목록 딕셔너리 생성
theme_map = {}
theme_stocks = {}  # 테마 → 종목코드 목록

for _, row in df.iterrows():
    code   = str(row.get("종목코드", "")).zfill(6)
    name   = str(row.get("종목명", ""))
    themes = str(row.get("테마목록", ""))

    if not code or code == "nan":
        continue

    theme_list = [t.strip() for t in themes.split("|") if t.strip() and t.strip() != "nan"]
    theme_map[code] = {"name": name, "themes": theme_list}

    # 테마별 종목 목록도 구성
    for t in theme_list:
        if t not in theme_stocks:
            theme_stocks[t] = []
        if code not in theme_stocks[t]:
            theme_stocks[t].append(code)

print(f"✓ 테마 수: {len(theme_stocks)}개")

# theme_map.py 파일로 저장
with open("theme_map.py", "w", encoding="utf-8") as f:
    f.write('"""\n')
    f.write('테마-종목 매핑 데이터\n')
    f.write('주달 사이트 테마 분류 기반으로 직접 구성\n')
    f.write('"""\n\n')

    # THEME_MAP: 종목코드 → {종목명, 테마목록}
    f.write("THEME_MAP = {\n")
    for code, info in sorted(theme_map.items()):
        themes_str = str(info['themes'])
        f.write(f'    "{code}": {{"name": "{info["name"]}", "themes": {themes_str}}},\n')
    f.write("}\n\n")

    # THEME_STOCKS: 테마명 → 종목코드 목록
    f.write("THEME_STOCKS = {\n")
    for theme, codes in sorted(theme_stocks.items()):
        codes_str = str(codes)
        f.write(f'    "{theme}": {codes_str},\n')
    f.write("}\n\n")

    # 테마 목록 (정렬)
    f.write("THEME_LIST = [\n")
    for theme in sorted(theme_stocks.keys()):
        count = len(theme_stocks[theme])
        f.write(f'    "{theme}",  # {count}개 종목\n')
    f.write("]\n")

print(f"\n✅ theme_map.py 저장 완료!")
print(f"   - THEME_MAP: {len(theme_map)}개 종목")
print(f"   - THEME_STOCKS: {len(theme_stocks)}개 테마")
print(f"\n다음 단계: theme_map.py를 C:\\lb_screener 폴더에서 확인하세요.")
print("이 파일을 GitHub lb-screener 저장소에 업로드하면 됩니다.")
