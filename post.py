import os, time, random, urllib.parse, requests

# ====== SETTINGS (inga maathunga) ======
BUSINESS = os.environ.get("BUSINESS_TYPE", "bakery")   # restaurant, salon, gym, boutique...
BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "Our Bakery")
LANGUAGE = os.environ.get("CAPTION_LANGUAGE", "Tamil and English mixed")
TOPICS = [
    "festival offer", "weekend special", "customer thanks",
    "new item launch", "behind the scenes", "motivational quote",
    "today's special", "combo offer",
]
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
POST_TO_INSTAGRAM = os.environ.get("POST_TO_INSTAGRAM", "true") == "true"
POST_TO_FACEBOOK = os.environ.get("POST_TO_FACEBOOK", "true") == "true"
# =======================================

GEMINI_KEY = os.environ["GEMINI_KEY"]
TOKEN = os.environ["META_TOKEN"]
IG_ID = os.environ.get("IG_ID", "")
PAGE_ID = os.environ.get("PAGE_ID", "")
G = "https://graph.facebook.com/v21.0"


def generate_text():
    topic = random.choice(TOPICS)
    ask = (
        f"You create social media posts for a {BUSINESS} called '{BUSINESS_NAME}'. "
        f"Topic: {topic}.\n"
        "Reply in EXACTLY this format, nothing else:\n"
        "IMAGE: <one-line English image prompt, photorealistic, NO text or words in the image>\n"
        f"CAPTION: <short engaging caption in {LANGUAGE}, with 2-3 emojis and 5 relevant hashtags>"
    )
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}")
    r = requests.post(url, json={"contents": [{"parts": [{"text": ask}]}]}, timeout=60)
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    image_part, caption_part = text.split("CAPTION:", 1)
    image_prompt = image_part.replace("IMAGE:", "").strip()
    return image_prompt, caption_part.strip()


def make_image_url(prompt):
    seed = random.randint(1, 10**6)
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
           + f"?width=1080&height=1080&nologo=true&seed={seed}")
    for attempt in range(4):           # image ready aaga retry
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                return url
        except requests.RequestException:
            pass
        time.sleep(10)
    raise RuntimeError("Image generate aagala")


def post_instagram(img_url, caption):
    c = requests.post(f"{G}/{IG_ID}/media",
                      data={"image_url": img_url, "caption": caption, "access_token": TOKEN},
                      timeout=60).json()
    if "id" not in c:
        raise RuntimeError(f"Instagram container error: {c}")
    for _ in range(10):                # container ready aaguthaanu check
        s = requests.get(f"{G}/{c['id']}",
                         params={"fields": "status_code", "access_token": TOKEN},
                         timeout=30).json()
        if s.get("status_code") == "FINISHED":
            break
        time.sleep(5)
    res = requests.post(f"{G}/{IG_ID}/media_publish",
                        data={"creation_id": c["id"], "access_token": TOKEN},
                        timeout=60).json()
    print("Instagram:", res)


def post_facebook(img_url, caption):
    res = requests.post(f"{G}/{PAGE_ID}/photos",
                        data={"url": img_url, "caption": caption, "access_token": TOKEN},
                        timeout=60).json()
    print("Facebook:", res)


if __name__ == "__main__":
    image_prompt, caption = generate_text()
    print("Image prompt:", image_prompt)
    print("Caption:", caption)
    img_url = make_image_url(image_prompt)
    print("Image URL:", img_url)
    if POST_TO_INSTAGRAM and IG_ID:
        post_instagram(img_url, caption)
    if POST_TO_FACEBOOK and PAGE_ID:
        post_facebook(img_url, caption)
