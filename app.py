import streamlit as st
import pandas as pd

from datetime import date, datetime
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel


class JournalAnalysis(BaseModel):
    emotion_summary: str
    key_themes: list[str]
    supportive_reflection: str
    small_action: str


class TrendAnalysis(BaseModel):
    overall_trend: str
    repeated_themes: list[str]
    mood_stress_pattern: str
    reflection_question: str


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "mindlog_records.csv"
BACKUP_DIR = DATA_DIR / "backups"


def initialize_session_state():
    defaults = {
        "ai_analysis": None,
        "analysis_input": None,
        "trend_analysis": None,
        "trend_source": None,
        "delete_message": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_openai_client():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def clean_ai_text(text):
    return str(text).replace("~", "–")


def analyze_journal(mood, stress, journal):
    client = get_openai_client()

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "당신은 사용자가 자신의 일상 기록을 따뜻하고 신중하게 "
                    "되돌아보도록 돕는 자기성찰 도우미입니다. "
                    "기록에 직접 나타난 내용만 바탕으로 답하세요. "
                    "정신질환을 진단하거나 치료를 지시하거나 확정적으로 "
                    "판단하지 마세요. 한국어로 짧고 이해하기 쉽게 작성하세요. "
                    "숫자 범위는 물결표 대신 하이픈을 사용하세요."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"기분 점수: {mood}/10\n"
                    f"스트레스 점수: {stress}/10\n"
                    f"일상 기록: {journal}"
                ),
            },
        ],
        text_format=JournalAnalysis,
        store=False,
    )

    return response.output_parsed


def show_journal_analysis(analysis):
    st.subheader("💭 감정 요약")
    st.write(clean_ai_text(analysis["emotion_summary"]))

    st.subheader("🔎 주요 주제")
    for theme in analysis["key_themes"]:
        st.write(f"• {clean_ai_text(theme)}")

    st.subheader("🪞 따뜻한 되돌아보기")
    st.write(clean_ai_text(analysis["supportive_reflection"]))

    st.subheader("🌱 오늘의 작은 제안")
    st.write(clean_ai_text(analysis["small_action"]))

    st.caption(
        "AI 결과는 자기성찰을 돕기 위한 참고 정보이며 "
        "전문적인 진단이나 치료를 대신하지 않습니다."
    )


def save_record(record_date, mood, stress, journal, analysis):
    if analysis is None:
        analysis_values = {
            "emotion_summary": "",
            "key_themes": "",
            "supportive_reflection": "",
            "small_action": "",
            "ai_model": "",
        }
    else:
        analysis_values = {
            "emotion_summary": analysis["emotion_summary"],
            "key_themes": " | ".join(analysis["key_themes"]),
            "supportive_reflection": analysis["supportive_reflection"],
            "small_action": analysis["small_action"],
            "ai_model": "gpt-5.6-luna",
        }

    new_record = pd.DataFrame(
        [
            {
                "recorded_at": datetime.now().isoformat(timespec="seconds"),
                "date": record_date.isoformat(),
                "mood": mood,
                "stress": stress,
                "journal": journal,
                **analysis_values,
            }
        ]
    )

    if DATA_FILE.exists():
        saved_records = pd.read_csv(DATA_FILE)
        saved_records = pd.concat(
            [saved_records, new_record],
            ignore_index=True,
        )
    else:
        saved_records = new_record

    saved_records.to_csv(
        DATA_FILE,
        index=False,
        encoding="utf-8-sig",
    )


def load_records():
    if not DATA_FILE.exists():
        return pd.DataFrame()

    records = pd.read_csv(DATA_FILE)

    required_columns = [
        "recorded_at",
        "date",
        "mood",
        "stress",
        "journal",
        "emotion_summary",
        "key_themes",
        "supportive_reflection",
        "small_action",
        "ai_model",
    ]

    for column in required_columns:
        if column not in records.columns:
            records[column] = ""

    return records


def is_duplicate_record(record_date, mood, stress, journal):
    records = load_records()

    if records.empty:
        return False

    saved_dates = records["date"].fillna("").astype(str)
    saved_moods = pd.to_numeric(records["mood"], errors="coerce")
    saved_stress = pd.to_numeric(records["stress"], errors="coerce")
    saved_journals = (
        records["journal"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    duplicate_rows = (
        (saved_dates == record_date.isoformat())
        & (saved_moods == mood)
        & (saved_stress == stress)
        & (saved_journals == journal.strip())
    )

    return bool(duplicate_rows.any())


def delete_record_with_backup(records, selected_index):
    BACKUP_DIR.mkdir(exist_ok=True)
    backup_name = (
        "mindlog_records_before_delete_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    backup_file = BACKUP_DIR / backup_name

    records.to_csv(
        backup_file,
        index=False,
        encoding="utf-8-sig",
    )

    updated_records = records.drop(index=selected_index)
    updated_records.to_csv(
        DATA_FILE,
        index=False,
        encoding="utf-8-sig",
    )


def show_record_deletion(records):
    with st.expander("🗑️ 저장된 기록 삭제"):
        st.caption(
            "삭제 버튼을 누르기 전에 현재 CSV의 백업 파일이 "
            "data/backups 폴더에 자동으로 만들어집니다."
        )

        sorted_records = records.sort_values(
            by=["date", "recorded_at"],
            ascending=False,
        )

        options = {}

        for index, row in sorted_records.iterrows():
            journal_text = row.get("journal", "")
            if pd.isna(journal_text):
                journal_text = ""

            preview = str(journal_text).replace("\n", " ")[:35]
            label = (
                f"{row.get('date', '')} | "
                f"기분 {row.get('mood', '')} | "
                f"스트레스 {row.get('stress', '')} | "
                f"{preview} | 기록 {index + 1}"
            )
            options[label] = index

        selected_label = st.selectbox(
            "삭제할 기록 선택",
            options=list(options.keys()),
            index=None,
            placeholder="기록을 선택해주세요.",
            key="delete_record_select",
        )

        if selected_label is not None:
            selected_index = options[selected_label]
            st.warning(f"선택한 기록: {selected_label}")

            confirmed = st.checkbox(
                "선택한 기록을 삭제하는 것에 동의합니다.",
                key="delete_record_confirm",
            )

            if st.button(
                "🗑️ 선택한 기록 삭제",
                disabled=not confirmed,
                key="delete_record_button",
            ):
                delete_record_with_backup(records, selected_index)
                st.session_state.trend_analysis = None
                st.session_state.trend_source = None
                st.session_state.delete_message = (
                    "선택한 기록을 삭제했습니다. 삭제 전 백업도 저장되었습니다."
                )
                st.rerun()


def show_records_table(records):
    st.divider()
    st.subheader("📋 저장된 기록")

    if st.session_state.delete_message is not None:
        st.success(st.session_state.delete_message)
        st.session_state.delete_message = None

    display_columns = [
        "date",
        "mood",
        "stress",
        "journal",
        "emotion_summary",
        "key_themes",
        "supportive_reflection",
        "small_action",
    ]

    display_records = (
        records[display_columns]
        .sort_values(by="date", ascending=False)
        .rename(
            columns={
                "date": "날짜",
                "mood": "기분",
                "stress": "스트레스",
                "journal": "일상 기록",
                "emotion_summary": "감정 요약",
                "key_themes": "주요 주제",
                "supportive_reflection": "따뜻한 되돌아보기",
                "small_action": "작은 제안",
            }
        )
    )

    st.dataframe(
        display_records,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = records.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="📥 전체 기록 CSV 다운로드",
        data=csv_data,
        file_name=f"mindlog_records_{date.today().isoformat()}.csv",
        mime="text/csv",
    )

    show_record_deletion(records)


def build_records_text(recent_records):
    record_blocks = []

    for _, row in recent_records.iterrows():
        journal_text = row.get("journal", "")
        if pd.isna(journal_text):
            journal_text = ""

        record_blocks.append(
            f"날짜: {row['date']}\n"
            f"기분: {row['mood']}/10\n"
            f"스트레스: {row['stress']}/10\n"
            f"일상 기록: {str(journal_text)[:1500]}"
        )

    return "\n\n".join(record_blocks)


def analyze_recent_records(recent_records):
    client = get_openai_client()
    records_text = build_records_text(recent_records)

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "당신은 여러 일상 기록에서 관찰되는 정서적 흐름을 "
                    "신중하게 요약하는 자기성찰 도우미입니다. 제공된 기록에 "
                    "직접 나타난 정보만 사용하세요. 기록 수가 적다는 한계를 "
                    "고려하고, 인과관계나 정신질환을 추정하거나 진단하지 마세요. "
                    "기분과 스트레스 점수의 관계도 관찰 가능한 수준으로만 "
                    "설명하세요. 한국어로 간결하고 따뜻하게 작성하세요. "
                    "숫자 범위는 물결표 대신 하이픈을 사용하세요."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"분석할 기록 수: {len(recent_records)}개\n\n"
                    f"{records_text}"
                ),
            },
        ],
        text_format=TrendAnalysis,
        store=False,
    )

    return response.output_parsed


def show_trend_result(trend, record_count):
    st.subheader("📊 전반적인 정서 흐름")
    st.write(clean_ai_text(trend["overall_trend"]))

    st.subheader("🔁 반복해서 나타난 주제")
    for theme in trend["repeated_themes"]:
        st.write(f"• {clean_ai_text(theme)}")

    st.subheader("📉 기분과 스트레스의 관찰된 패턴")
    st.write(clean_ai_text(trend["mood_stress_pattern"]))

    st.subheader("🤔 생각해볼 질문")
    st.info(clean_ai_text(trend["reflection_question"]))

    st.caption(
        f"최근 {record_count}개 기록을 바탕으로 생성된 "
        "자기성찰용 결과이며 임상적 평가가 아닙니다."
    )


def show_trend_analysis(records):
    st.divider()
    st.subheader("🧭 최근 기록 흐름 분석")
    st.caption("최근 최대 7개의 기록을 바탕으로 정서 흐름과 반복 주제를 살펴봅니다.")

    if len(records) < 2:
        st.info("흐름 분석을 하려면 최소 2개의 기록이 필요합니다.")
        return

    sort_column = "recorded_at" if "recorded_at" in records.columns else "date"
    recent_records = records.sort_values(sort_column).tail(7)
    trend_source = recent_records[sort_column].astype(str).tolist()

    if st.button("🔍 최근 기록 AI 종합 분석"):
        with st.spinner("최근 기록의 흐름을 분석하고 있어요..."):
            try:
                trend_analysis = analyze_recent_records(recent_records)

                if trend_analysis is None:
                    st.error("최근 기록 분석 결과를 불러오지 못했습니다.")
                else:
                    st.session_state.trend_analysis = trend_analysis.model_dump()
                    st.session_state.trend_source = trend_source
                    st.success("최근 기록 분석이 완료되었습니다!")

            except Exception as error:
                st.error("최근 기록 분석 중 오류가 발생했습니다.")
                st.code(str(error))

    if (
        st.session_state.trend_analysis is not None
        and st.session_state.trend_source == trend_source
    ):
        show_trend_result(
            st.session_state.trend_analysis,
            len(recent_records),
        )

    elif st.session_state.trend_analysis is not None:
        st.info(
            "새로운 기록이 추가되었습니다. "
            "현재 기록으로 다시 종합 분석해주세요."
        )


def show_score_chart(records):
    chart_records = records.copy()
    chart_records["date"] = pd.to_datetime(
        chart_records["date"],
        errors="coerce",
    )
    chart_records["mood"] = pd.to_numeric(
        chart_records["mood"],
        errors="coerce",
    )
    chart_records["stress"] = pd.to_numeric(
        chart_records["stress"],
        errors="coerce",
    )
    chart_records = chart_records.dropna(
        subset=["date", "mood", "stress"]
    )

    if chart_records.empty:
        return

    daily_scores = (
        chart_records
        .groupby("date", as_index=False)[["mood", "stress"]]
        .mean()
        .sort_values("date")
        .rename(
            columns={
                "mood": "기분",
                "stress": "스트레스",
            }
        )
        .set_index("date")
    )

    st.divider()
    st.subheader("📈 기분과 스트레스 변화")
    st.line_chart(
        daily_scores,
        y=["기분", "스트레스"],
    )
    st.caption("같은 날짜에 여러 기록이 있으면 그날의 평균 점수가 표시됩니다.")


def main():
    st.set_page_config(
        page_title="MindLog AI",
        page_icon="🧠",
    )
    initialize_session_state()

    st.title("🧠 MindLog AI")
    st.write("일상 속 정서와 스트레스를 기록하는 디지털 정신건강 연구 프로토타입")
    st.caption(
        "본 앱은 연구·자기모니터링용 프로토타입이며 "
        "진단이나 치료를 제공하지 않습니다."
    )
    st.divider()

    record_date = st.date_input(
        "기록 날짜",
        value=date.today(),
    )
    mood = st.slider(
        "오늘의 기분은 어떤가요?",
        min_value=1,
        max_value=10,
        value=5,
        help="1점은 매우 좋지 않음, 10점은 매우 좋음을 의미합니다.",
    )
    stress = st.slider(
        "오늘의 스트레스는 어느 정도인가요?",
        min_value=1,
        max_value=10,
        value=5,
        help="1점은 매우 낮음, 10점은 매우 높음을 의미합니다.",
    )
    journal = st.text_area(
        "오늘 하루를 자유롭게 기록해주세요.",
        placeholder="오늘 있었던 일, 느낀 감정, 기억에 남는 생각 등을 적어보세요.",
        height=180,
    )

    current_input = {
        "mood": mood,
        "stress": stress,
        "journal": journal.strip(),
    }

    if st.button("✨ AI로 기록 살펴보기"):
        if not journal.strip():
            st.warning("AI 분석을 위해 일상 기록을 먼저 입력해주세요.")
        else:
            with st.spinner("AI가 기록을 살펴보고 있어요..."):
                try:
                    analysis = analyze_journal(
                        mood,
                        stress,
                        journal.strip(),
                    )

                    if analysis is None:
                        st.error("AI 분석 결과를 불러오지 못했습니다.")
                    else:
                        st.session_state.ai_analysis = analysis.model_dump()
                        st.session_state.analysis_input = current_input.copy()
                        st.success("AI 분석이 완료되었습니다!")

                except Exception as error:
                    st.error("AI 분석 중 오류가 발생했습니다.")
                    st.code(str(error))

    current_analysis = None

    if (
        st.session_state.ai_analysis is not None
        and st.session_state.analysis_input == current_input
    ):
        current_analysis = st.session_state.ai_analysis
        show_journal_analysis(current_analysis)

    elif st.session_state.ai_analysis is not None:
        st.info(
            "AI 분석 후 입력 내용이 변경되었습니다. "
            "현재 내용으로 다시 분석해주세요."
        )

    if st.button("오늘의 기록 저장", type="primary"):
        if not journal.strip():
            st.warning("일상 기록을 입력해주세요.")
        elif is_duplicate_record(
            record_date,
            mood,
            stress,
            journal.strip(),
        ):
            st.warning(
                "같은 날짜·점수·일상 내용의 기록이 이미 저장되어 있어 "
                "중복 저장하지 않았습니다."
            )
        else:
            save_record(
                record_date,
                mood,
                stress,
                journal.strip(),
                current_analysis,
            )

            if current_analysis is None:
                st.success("오늘의 기록이 저장되었습니다!")
            else:
                st.success("오늘의 기록과 AI 분석 결과가 함께 저장되었습니다!")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("기분", f"{mood}/10")
            with col2:
                st.metric("스트레스", f"{stress}/10")

    records = load_records()

    if not records.empty:
        show_records_table(records)
        show_trend_analysis(records)
        show_score_chart(records)


if __name__ == "__main__":
    main()
