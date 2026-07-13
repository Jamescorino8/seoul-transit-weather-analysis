import json
import re
import time
from pathlib import Path

import pandas as pd
import requests
from openai import OpenAI

from config import YOUTUBE_API_KEY, DEEPSEEK_API_KEY, DEEPSEEK_MODEL

# ----- Configuration -----

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
COMMENT_URL = "https://www.googleapis.com/youtube/v3/commentThreads"

MAX_COMMENTS_PER_VIDEO = 100
SELECTED_CANDIDATE_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9]

PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR = PROCESSED_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

FINAL_OUTPUT_PATH = PROCESSED_DIR / "Rain_Commute_Clean.csv"
LABEL_PROGRESS_PATH = TEMP_DIR / "temp_Rain_Comment_Labels.csv"
EMOTION_PROGRESS_PATH = TEMP_DIR / "temp_Emotion_Labels.csv"


# ----- API Validation -----
def validate_api_keys():
    if not YOUTUBE_API_KEY:
        raise ValueError("Add your YouTube Data API key to YOUTUBE_API_KEY.")

    if not DEEPSEEK_API_KEY:
        raise ValueError("Add your DeepSeek API key to DEEPSEEK_API_KEY.")


# ----- YouTube Video Collection -----
def search_rainy_commuting_videos():
    rain_search_keywords = [
        "서울 폭우 출근길 지하철",
        "서울 폭우 출근길 버스",
        "비 오는 날 서울 지하철 혼잡",
        "장마 서울 대중교통 불편",
        "서울 비 출근길 교통 대란",
        "폭우 서울 지하철 지연",
        "폭우 서울 버스 지연",
        "비 오는 날 출근길 서울",
    ]

    rain_videos = []

    for keyword in rain_search_keywords:
        params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "maxResults": 20,
            "regionCode": "KR",
            "relevanceLanguage": "ko",
            "key": YOUTUBE_API_KEY,
        }

        response = requests.get(SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]

            rain_videos.append(
                {
                    "Search_Keyword": keyword,
                    "Video_ID": video_id,
                    "Video_Title": snippet["title"],
                    "Channel_Title": snippet["channelTitle"],
                    "Video_Date": snippet["publishedAt"],
                    "Description": snippet["description"],
                    "Video_URL": f"https://www.youtube.com/watch?v={video_id}",
                }
            )

    rain_video_df = pd.DataFrame(rain_videos)

    if rain_video_df.empty:
        raise RuntimeError("No videos were returned by the YouTube search API.")

    rain_video_df = rain_video_df.drop_duplicates(
        subset="Video_ID"
    ).reset_index(drop=True)

    rain_video_df["Video_Date"] = pd.to_datetime(
        rain_video_df["Video_Date"], errors="coerce"
    )

    print("Number of unique rain-related videos:", len(rain_video_df))
    return rain_video_df


def add_video_statistics(rain_video_df):
    rain_video_ids = rain_video_df["Video_ID"].tolist()
    statistics_rows = []

    # YouTube videos.list accepts up to 50 IDs per request.
    for start in range(0, len(rain_video_ids), 50):
        batch_ids = rain_video_ids[start : start + 50]

        params = {
            "part": "statistics",
            "id": ",".join(batch_ids),
            "key": YOUTUBE_API_KEY,
        }

        response = requests.get(VIDEO_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            statistics = item.get("statistics", {})

            statistics_rows.append(
                {
                    "Video_ID": item["id"],
                    "View_Count": int(statistics.get("viewCount", 0)),
                    "Like_Count": int(statistics.get("likeCount", 0)),
                    "Comment_Count": int(statistics.get("commentCount", 0)),
                }
            )

    statistics_df = pd.DataFrame(statistics_rows)
    rain_video_df = rain_video_df.merge(
        statistics_df, on="Video_ID", how="left"
    )

    rain_video_df["Comment_Count"] = (
        rain_video_df["Comment_Count"].fillna(0).astype(int)
    )

    return rain_video_df.sort_values(
        by="Comment_Count", ascending=False
    ).reset_index(drop=True)


def contains_any(text, keywords):
    text = str(text).lower()
    return any(keyword.lower() in text for keyword in keywords)


def filter_video_candidates(rain_video_df):
    rain_keywords = [
        "비", "폭우", "호우", "장마", "침수", "물폭탄", "장대비"
    ]
    seoul_keywords = [
        "서울", "강남", "영등포", "서초", "관악", "신림",
        "동작", "광운대", "청량리", "한강"
    ]
    commute_keywords = [
        "출근", "퇴근", "출퇴근", "통근", "지하철", "버스",
        "대중교통", "교통", "열차", "운행", "지연"
    ]
    exclude_keywords = [
        "폭설", "눈", "태풍", "사고", "부상", "사망", "성남",
        "수원", "인천", "부산", "대구", "대전", "광주",
        "playlist", "플레이리스트", "asmr", "드라이브", "drive",
        "장화", "우산", "제품", "광고"
    ]

    candidate_df = rain_video_df.copy()
    candidate_df["Combined_Text"] = (
        candidate_df["Video_Title"].fillna("")
        + " "
        + candidate_df["Description"].fillna("")
    )

    candidate_df = candidate_df[
        candidate_df["Combined_Text"].apply(
            lambda text: contains_any(text, rain_keywords)
        )
        & candidate_df["Combined_Text"].apply(
            lambda text: contains_any(text, seoul_keywords)
        )
        & candidate_df["Combined_Text"].apply(
            lambda text: contains_any(text, commute_keywords)
        )
        & ~candidate_df["Combined_Text"].apply(
            lambda text: contains_any(text, exclude_keywords)
        )
        & (candidate_df["Comment_Count"] >= 10)
    ].copy()

    candidate_df = candidate_df.sort_values(
        by="Comment_Count", ascending=False
    ).reset_index(drop=True)

    candidate_df.insert(0, "Candidate_No", range(1, len(candidate_df) + 1))

    final_video_df = candidate_df[
        candidate_df["Candidate_No"].isin(SELECTED_CANDIDATE_NUMBERS)
    ].copy().reset_index(drop=True)

    print("Final candidate videos:", len(candidate_df))
    print("Final selected videos:", len(final_video_df))

    if final_video_df.empty:
        raise RuntimeError("No videos remained after filtering.")

    return final_video_df


# ----- YouTube Comment Collection -----
def collect_comments(final_video_df):
    rain_comments = []

    for index, video in final_video_df.iterrows():
        params = {
            "part": "snippet",
            "videoId": video["Video_ID"],
            "maxResults": 100,
            "order": "relevance",
            "textFormat": "plainText",
            "key": YOUTUBE_API_KEY,
        }

        try:
            response = requests.get(COMMENT_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            video_comment_count = 0

            for item in data.get("items", []):
                comment_data = item["snippet"]["topLevelComment"]["snippet"]

                rain_comments.append(
                    {
                        "Video_ID": video["Video_ID"],
                        "Video_Title": video["Video_Title"],
                        "Channel_Title": video["Channel_Title"],
                        "Video_Date": video["Video_Date"],
                        "Comment": comment_data["textDisplay"],
                        "Comment_Date": comment_data["publishedAt"],
                        "Comment_Like_Count": comment_data.get("likeCount", 0),
                    }
                )

                video_comment_count += 1
                if video_comment_count >= MAX_COMMENTS_PER_VIDEO:
                    break

            print(
                f"{index + 1}/{len(final_video_df)} "
                f"{video['Video_Title'][:40]}: "
                f"{video_comment_count} comments"
            )

        except Exception as error:
            print(f"Failed: {video['Video_Title'][:40]} | {error}")

        time.sleep(0.1)

    comments_df = pd.DataFrame(rain_comments)

    if comments_df.empty:
        raise RuntimeError("No comments were collected from the selected videos.")

    comments_df["Comment_Date"] = pd.to_datetime(
        comments_df["Comment_Date"], errors="coerce"
    )
    comments_df["Video_Date"] = pd.to_datetime(
        comments_df["Video_Date"], errors="coerce"
    )

    comments_df = comments_df.drop_duplicates(
        subset=["Video_ID", "Comment"]
    ).reset_index(drop=True)

    print("Total rain-related comments:", len(comments_df))
    print("Videos represented:", comments_df["Video_ID"].nunique())
    return comments_df


# ----- Comment Cleaning -----
def clean_comment(text):
    text = str(text)
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def has_meaningful_text(text):
    return bool(re.search(r"[가-힣A-Za-z0-9]", str(text)))


def clean_comments(comments_df):
    clean_df = comments_df.copy()
    clean_df["Clean_Comment"] = clean_df["Comment"].apply(clean_comment)

    clean_df = clean_df[
        clean_df["Clean_Comment"].apply(has_meaningful_text)
    ].copy()

    clean_df = clean_df.drop_duplicates(
        subset=["Video_ID", "Clean_Comment"]
    ).reset_index(drop=True)

    print("Comments before cleaning:", len(comments_df))
    print("Comments after cleaning:", len(clean_df))
    return clean_df


# ----- DeepSeek Labeling -----
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

COMMENT_SYSTEM_PROMPT = """
You are coding Korean YouTube comments for an academic study
about rainy commuting and transportation experiences in Seoul.

Return exactly one valid JSON object with no additional text.
Use the comment as the primary evidence. Use the video title only to
clarify an obvious contextual reference. Do not classify a comment as
commute-relevant merely because the video title concerns commuting or rain.

Weather_Relevant:
1 = The comment mentions rain, heavy rain, flooding, water, precipitation,
or clearly refers to the rainy situation shown in the video.
0 = No meaningful weather reference.

Commute_Relevant:
1 = The comment discusses commuting, going to work or school, returning
home, public transit, traffic, roads, stations, buses, subways, walking,
driving, transportation delay, or travel disruption.
0 = No transportation or travel meaning.

Personal_Experience:
1 = The commenter describes an event experienced by themselves or someone
personally known to them.
0 = General reaction, observation, joke, prediction, or opinion.

Frustration_Score:
0 = No commute-related frustration or inconvenience.
1 = Mild inconvenience, concern, discomfort, or resigned complaint.
2 = Clear frustration, criticism, sarcasm, stress, or substantial travel
inconvenience.
3 = Severe anger, danger, inability to travel, extreme delay, or major
disruption.

Issue_Type: choose exactly one of Congestion, Delay, Flooding, Safety,
Comfort, Workplace_Pressure, Transportation_Preference, Other, or None.

Consistency requirements:
- If Commute_Relevant = 0, Frustration_Score must be 0 and Issue_Type must
  be "None".
- If Commute_Relevant = 1, Issue_Type must not be "None".
- Personal_Experience refers to an actual personal event, not merely an
  opinion or emotional reaction.
"""


def label_comment(video_title, comment):
    user_prompt = f"""
Video title:
{video_title}

Comment:
{comment}

Return JSON using exactly these keys:
{{
  "Weather_Relevant": 0,
  "Commute_Relevant": 0,
  "Personal_Experience": 0,
  "Frustration_Score": 0,
  "Issue_Type": "None"
}}
"""

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": COMMENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    return json.loads(response.choices[0].message.content)


ALLOWED_ISSUE_TYPES = {
    "Congestion", "Delay", "Flooding", "Safety", "Comfort",
    "Workplace_Pressure", "Transportation_Preference", "Other", "None"
}


def validate_comment_label(result):
    label = {
        "Weather_Relevant": int(result["Weather_Relevant"]),
        "Commute_Relevant": int(result["Commute_Relevant"]),
        "Personal_Experience": int(result["Personal_Experience"]),
        "Frustration_Score": int(result["Frustration_Score"]),
        "Issue_Type": result["Issue_Type"],
    }

    for column in [
        "Weather_Relevant", "Commute_Relevant", "Personal_Experience"
    ]:
        if label[column] not in [0, 1]:
            raise ValueError(f"Invalid {column}")

    if label["Frustration_Score"] not in [0, 1, 2, 3]:
        raise ValueError("Invalid Frustration_Score")

    if label["Issue_Type"] not in ALLOWED_ISSUE_TYPES:
        raise ValueError(f"Invalid Issue_Type: {label['Issue_Type']}")

    if label["Commute_Relevant"] == 0:
        label["Frustration_Score"] = 0
        label["Issue_Type"] = "None"
    elif label["Issue_Type"] == "None":
        raise ValueError("Commute-relevant comments require an issue type.")

    return label


def label_all_comments(clean_comments_df):
    full_comments_df = clean_comments_df.copy().reset_index(drop=True)
    full_comments_df.insert(0, "Comment_ID", range(1, len(full_comments_df) + 1))

    labels = []

    for index, row in full_comments_df.iterrows():
        success = False

        for attempt in range(3):
            try:
                label = validate_comment_label(
                    label_comment(row["Video_Title"], row["Clean_Comment"])
                )
                label["Comment_ID"] = row["Comment_ID"]
                labels.append(label)
                success = True
                break

            except Exception as error:
                print(
                    f"Attempt {attempt + 1} failed for comment "
                    f"{row['Comment_ID']}: {error}"
                )
                time.sleep(2)

        if not success:
            labels.append(
                {
                    "Comment_ID": row["Comment_ID"],
                    "Weather_Relevant": None,
                    "Commute_Relevant": None,
                    "Personal_Experience": None,
                    "Frustration_Score": None,
                    "Issue_Type": None,
                }
            )

        print(f"Initial labeling: {index + 1}/{len(full_comments_df)} completed")

        if (index + 1) % 25 == 0:
            pd.DataFrame(labels).to_csv(
                LABEL_PROGRESS_PATH, index=False, encoding="utf-8-sig"
            )

        time.sleep(0.3)

    labels_df = pd.DataFrame(labels)
    labeled_df = full_comments_df.merge(labels_df, on="Comment_ID", how="left")

    print("Total labeled comments:", len(labeled_df))
    print("Failed labels:", labeled_df["Weather_Relevant"].isna().sum())
    return labeled_df


EMOTION_SYSTEM_PROMPT = """
You are coding Korean YouTube comments for an academic study about rainy
commuting experiences in Seoul. Return exactly one valid JSON object and no
additional text. Use the comment as the primary evidence and the video title
only to clarify obvious context.

Choose exactly one dominant Emotion_Type:
Frustration, Anxiety, Fear, Exhaustion, Resignation, Humor, Appreciation,
Relief, Neutral, or Other.

Emotion_Intensity:
0 = No clear emotion.
1 = Mild emotional expression.
2 = Clear or moderate emotional expression.
3 = Strong or intense emotional expression.

Important rules:
- Humor markers such as ㅋㅋ or ㅎㅎ do not automatically mean Humor.
- If humor mainly expresses anger or criticism, choose Frustration.
- If humor mainly communicates helpless acceptance, choose Resignation.
- Choose Fear for immediate danger and Anxiety for concern about what may
  happen.
- Constructive criticism of companies, government, drainage systems, or
  commuting policies should generally be Frustration.
- Choose Appreciation for gratitude, admiration, respect, or praise.
- Choose Neutral only when no clear emotion is expressed.
- If Emotion_Type is Neutral, Emotion_Intensity must be 0.
- Otherwise, Emotion_Intensity must be 1, 2, or 3.
"""


def label_emotion(video_title, comment):
    user_prompt = f"""
Video title:
{video_title}

Comment:
{comment}

Return JSON using exactly these keys:
{{
  "Emotion_Type": "Neutral",
  "Emotion_Intensity": 0
}}
"""

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": EMOTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    return json.loads(response.choices[0].message.content)


ALLOWED_EMOTIONS = {
    "Frustration", "Anxiety", "Fear", "Exhaustion", "Resignation",
    "Humor", "Appreciation", "Relief", "Neutral", "Other"
}


def validate_emotion_label(result):
    emotion_type = result["Emotion_Type"]
    emotion_intensity = int(result["Emotion_Intensity"])

    if emotion_type not in ALLOWED_EMOTIONS:
        raise ValueError(f"Invalid emotion: {emotion_type}")

    if emotion_intensity not in [0, 1, 2, 3]:
        raise ValueError("Invalid emotion intensity")

    if emotion_type == "Neutral" and emotion_intensity != 0:
        raise ValueError("Neutral must have intensity 0")

    if emotion_type != "Neutral" and emotion_intensity == 0:
        raise ValueError("Non-neutral emotion must have intensity 1-3")

    return emotion_type, emotion_intensity


def label_all_emotions(analysis_comments_df):
    emotion_labels = []

    for index, row in analysis_comments_df.iterrows():
        success = False

        for attempt in range(3):
            try:
                emotion_type, emotion_intensity = validate_emotion_label(
                    label_emotion(row["Video_Title"], row["Clean_Comment"])
                )

                emotion_labels.append(
                    {
                        "Comment_ID": row["Comment_ID"],
                        "Emotion_Type": emotion_type,
                        "Emotion_Intensity": emotion_intensity,
                    }
                )
                success = True
                break

            except Exception as error:
                print(
                    f"Attempt {attempt + 1} failed for comment "
                    f"{row['Comment_ID']}: {error}"
                )
                time.sleep(2)

        if not success:
            emotion_labels.append(
                {
                    "Comment_ID": row["Comment_ID"],
                    "Emotion_Type": None,
                    "Emotion_Intensity": None,
                }
            )

        print(
            f"Emotion labeling: {index + 1}/{len(analysis_comments_df)} completed"
        )

        if (index + 1) % 20 == 0:
            pd.DataFrame(emotion_labels).to_csv(
                EMOTION_PROGRESS_PATH, index=False, encoding="utf-8-sig"
            )

        time.sleep(0.3)

    emotion_labels_df = pd.DataFrame(emotion_labels)
    return analysis_comments_df.merge(
        emotion_labels_df, on="Comment_ID", how="left"
    )


# ----- Final Dataset -----
def add_grouped_categories(final_df):
    emotion_group_map = {
        "Frustration": "Negative_Emotion",
        "Anxiety": "Negative_Emotion",
        "Fear": "Negative_Emotion",
        "Exhaustion": "Negative_Emotion",
        "Resignation": "Resigned_Humor",
        "Humor": "Resigned_Humor",
        "Appreciation": "Positive_Emotion",
        "Relief": "Positive_Emotion",
        "Neutral": "Neutral_Other",
        "Other": "Neutral_Other",
    }

    issue_group_map = {
        "Flooding": "Flooding",
        "Workplace_Pressure": "Workplace_Pressure",
        "Delay": "Delay",
        "Comfort": "Other_Issues",
        "Congestion": "Other_Issues",
        "Safety": "Other_Issues",
        "Transportation_Preference": "Other_Issues",
        "Other": "Other_Issues",
    }

    final_df["Emotion_Group"] = final_df["Emotion_Type"].map(emotion_group_map)
    final_df["Issue_Group"] = final_df["Issue_Type"].map(issue_group_map)
    return final_df


def main():
    validate_api_keys()

    video_df = search_rainy_commuting_videos()
    video_df = add_video_statistics(video_df)
    final_video_df = filter_video_candidates(video_df)

    comments_df = collect_comments(final_video_df)
    clean_df = clean_comments(comments_df)
    labeled_df = label_all_comments(clean_df)

    analysis_df = labeled_df[
        (labeled_df["Weather_Relevant"] == 1)
        & (labeled_df["Commute_Relevant"] == 1)
    ].copy().reset_index(drop=True)

    print("Final analysis comments:", len(analysis_df))

    if analysis_df.empty:
        raise RuntimeError("No comments met both relevance requirements.")

    final_df = label_all_emotions(analysis_df)
    final_df = add_grouped_categories(final_df)

    final_df.to_csv(FINAL_OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("Total emotion-labeled comments:", len(final_df))
    print("Failed emotion labels:", final_df["Emotion_Type"].isna().sum())
    print(f"Final text analysis saved to {FINAL_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
