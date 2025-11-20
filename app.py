# streamlit_app.py (예시 이름)
# 한글 모음 분위기 분석기 - 슬라이드 알고리즘을 Streamlit UI로 구현

import unicodedata
from collections import Counter

import streamlit as st
import pandas as pd

# NFD에서 나오는 '중성(모음)' 코드 → 우리가 보기 쉬운 'ㅏ,ㅑ,…'로 매핑
JUNG_TO_VOWEL = {
    "\u1161": "ㅏ",  # ᅡ
    "\u1163": "ㅑ",  # ᅣ
    "\u1165": "ㅓ",  # ᅥ
    "\u1167": "ㅕ",  # ᅧ
    "\u1169": "ㅗ",  # ᅩ
    "\u116D": "ㅛ",  # ᅭ
    "\u116E": "ㅜ",  # ᅮ
    "\u1172": "ㅠ",  # ᅲ
    "\u1173": "ㅡ",  # ᅳ
    "\u1175": "ㅣ",  # ᅵ
    # 복모음(ㅘ, ㅝ, ㅢ 등)은 과제 단순화를 위해 제외 (네 코드 그대로)
}

BRIGHT = "ㅏㅑㅗㅛ"   # 밝음계
DARK = "ㅓㅕㅜㅠ"     # 어둠계
NEUTRAL = "ㅡㅣ"     # 중성계


def extract_vowels(line: str) -> list[str]:
    """'한글만 남기고 NFD 분해 → 중성(모음)만 필터링' (네 슬라이드 로직 그대로)"""
    norm = unicodedata.normalize("NFD", line)
    vowels = []
    for ch in norm:
        if ch in JUNG_TO_VOWEL:      # 중성에 해당하는 문자만 선택
            vowels.append(JUNG_TO_VOWEL[ch])
    return vowels


def analyze_vowels(vowels: list[str]):
    """모음 분포 계산 + 밝음/어둠/중성 비율 + BrightIndex, Neutrality"""
    counts = Counter(vowels)
    total = sum(counts.values())
    if total == 0:
        # 원래 코드에 없던 neutrality(중성 비율) 0.0 하나 더 추가해서 7개로 맞춤
        return counts, total, 0.0, 0.0, 0.0, 0.0, 0.0

    bright = sum(counts[v] for v in BRIGHT)
    dark = sum(counts[v] for v in DARK)
    neutral = sum(counts[v] for v in NEUTRAL)

    bright_ratio = bright / total
    dark_ratio = dark / total
    neutral_ratio = neutral / total

    bright_index = bright_ratio - dark_ratio
    neutrality = neutral_ratio

    return counts, total, bright_ratio, dark_ratio, neutral_ratio, bright_index, neutrality


def label_mood(bright_index: float, neutrality: float) -> str:
    """슬라이드의 분위기 라벨 규칙 그대로"""
    if bright_index >= 0.15:
        mood = "밝음"
    elif bright_index <= -0.15:
        mood = "어둠"
    else:
        mood = "중성/부드러움"

    if neutrality >= 0.45:
        mood += " (평온/잔잔)"
    return mood


def sliding_window_analysis(all_vowels: list[str], n: int):
    """창 사이즈 n(2 또는 3)로 연쇄 분석 → 결과 리스트로 반환 (UI에서 보여주기용)"""
    results = []
    if n <= 0 or len(all_vowels) < n:
        return results

    for i in range(len(all_vowels) - n + 1):
        window = all_vowels[i:i + n]
        _, _, _, _, _, bidx, neu = analyze_vowels(window)
        mood = label_mood(bidx, neu)
        results.append({
            "start": i,
            "end": i + n - 1,
            "window": "".join(window),
            "BrightIndex": bidx,
            "Neutrality": neu,
            "라벨": mood
        })
    return results


# -----------------------------
# Streamlit UI
# -----------------------------
def main():
    st.title("한글 모음 분위기 분석기")
    st.caption("슬라이드 알고리즘 버전을 기반으로 한 Streamlit UI")

    st.markdown(
        """
        1. 텍스트를 여러 줄 입력하면, 각 줄에서 모음을 추출합니다.  
        2. 밝음/어둠/중성 비율과 BrightIndex, Neutrality를 계산해서 분위기를 라벨링합니다.  
        3. 원하면 모음 시퀀스에 대해 2글자/3글자 슬라이딩 윈도우 분석도 할 수 있습니다.
        """
    )

    default_text = "아슬히 고개 내민 내게 첫 봄인사를 건네줘요\n여기에 두 번째 줄을 써도 돼요."
    text = st.text_area("분석할 텍스트(여러 줄 입력 가능)", value=default_text, height=200)

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        line_mode = st.checkbox("줄 단위 분석 출력", value=True)
    with col_opt2:
        window_n = st.selectbox(
            "연쇄 분석용 창 크기 n",
            options=[0, 2, 3],
            format_func=lambda x: "연쇄 분석 안 함" if x == 0 else f"{x}글자씩",
            index=0
        )

    if st.button("분석하기"):
        lines = text.splitlines()
        lines = [line for line in lines if line.strip() != ""]

        if not lines:
            st.warning("내용이 없습니다. 텍스트를 입력해 주세요.")
            return

        # 각 줄에서 모음 추출
        line_vowels = [extract_vowels(line) for line in lines]
        all_vowels = [v for vs in line_vowels for v in vs]

        # 전체 텍스트 기준 요약
        st.subheader("전체 텍스트 기준 분석")
        counts_all, total_all, br, dr, nr, bidx, neu = analyze_vowels(all_vowels)

        if total_all == 0:
            st.write("모음을 찾지 못했습니다.")
        else:
            mood_all = label_mood(bidx, neu)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("총 모음 수", total_all)
            c2.metric("밝음 비율", f"{br:.1%}")
            c3.metric("어둠 비율", f"{dr:.1%}")
            c4.metric("중성 비율", f"{nr:.1%}")

            st.metric("BrightIndex (밝음-어둠)", f"{bidx:.4f}")
            st.metric("Neutrality (중성 비율)", f"{neu:.4f}")
            st.write(f"**전체 분위기 라벨:** {mood_all}")

            # 모음별 개수 테이블
            df_counts = pd.DataFrame(
                {"모음": list(counts_all.keys()),
                 "개수": list(counts_all.values())}
            ).sort_values("모음")
            df_counts = df_counts.set_index("모음")
            st.markdown("**모음별 개수(전체)**")
            st.table(df_counts)

        # 줄 단위 분석
        if line_mode:
            st.subheader("줄 단위 분석 결과")
            for i, (line, vs) in enumerate(zip(lines, line_vowels), start=1):
                with st.expander(f"{i}번째 줄: {line}"):
                    counts, total, br, dr, nr, bidx, neu = analyze_vowels(vs)
                    if total == 0:
                        st.write("모음을 찾지 못했습니다.")
                        continue

                    mood = label_mood(bidx, neu)

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("총 모음 수", total)
                    c2.metric("밝음 비율", f"{br:.1%}")
                    c3.metric("어둠 비율", f"{dr:.1%}")
                    c4.metric("중성 비율", f"{nr:.1%}")

                    st.metric("BrightIndex", f"{bidx:.4f}")
                    st.metric("Neutrality", f"{neu:.4f}")
                    st.write(f"**분위기 라벨:** {mood}")

                    df_line = pd.DataFrame(
                        {"모음": list(counts.keys()),
                         "개수": list(counts.values())}
                    ).sort_values("모음")
                    df_line = df_line.set_index("모음")
                    st.table(df_line)

        # 슬라이딩 윈도우 연쇄 분석
        if window_n in (2, 3) and all_vowels:
            st.subheader(f"연쇄 분석 결과 (창 크기 {window_n})")
            win_results = sliding_window_analysis(all_vowels, window_n)
            if win_results:
                df_win = pd.DataFrame(win_results)
                df_win["범위"] = df_win.apply(
                    lambda row: f"{row['start']}~{row['end']}번",
                    axis=1
                )
                df_win_display = df_win[["범위", "window", "BrightIndex", "Neutrality", "라벨"]]
                st.dataframe(df_win_display, use_container_width=True)
            else:
                st.write("연쇄 분석을 수행할 만큼 모음이 충분하지 않습니다.")

        st.success("분석이 끝났습니다.")


if __name__ == "__main__":
    main()
