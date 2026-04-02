"""
TruthLens — AI-Powered Content Credibility Analyzer
Flask Backend Server
"""

import os
import re
import json
import hashlib
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
CORS(app)

# ─── CONFIG ────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_OPENAI = bool(OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here")

# In-memory history store (persists during server lifetime)
analysis_history = []

# ─── SCAM / TOXIC KEYWORD LISTS ───────────────────────
SCAM_PATTERNS = [
    r"(?i)you('ve| have) won",
    r"(?i)congratulations.*winner",
    r"(?i)claim (your|this) (prize|reward|gift|bonus)",
    r"(?i)act now|limited time|urgent",
    r"(?i)click (here|below) to (claim|verify|confirm)",
    r"(?i)free (iphone|gift card|money|bitcoin|crypto)",
    r"(?i)make \$?\d+.*per (day|hour|week)",
    r"(?i)no experience (needed|required)",
    r"(?i)guaranteed (income|profit|return)",
    r"(?i)double your (money|investment|bitcoin)",
    r"(?i)nigerian prince",
    r"(?i)wire transfer.*urgent",
    r"(?i)your account.*(suspended|locked|compromised)",
    r"(?i)verify your (identity|account|password)",
    r"(?i)social security number",
    r"(?i)100% free|risk[ -]free",
    r"(?i)buy now.*discount.*expires",
    r"(?i)miracle (cure|pill|supplement)",
    r"(?i)doctors (hate|don't want)",
    r"(?i)one weird trick",
]

TOXIC_PATTERNS = [
    r"(?i)\b(kill|murder|destroy|eliminate)\b.*\b(all|every|them|those)\b",
    r"(?i)\b(hate|despise)\b.*\b(race|religion|gender|community|group)\b",
    r"(?i)(go back to|don't belong|get out of) (your|their|this) country",
    r"(?i)\b(subhuman|inferior|vermin|filth|scum)\b",
    r"(?i)death (threats?|to)\b",
    r"(?i)\b(terroris[tm]|extremis[tm]|radical)\b.*\b(all|every|muslim|christian|jew|hindu)\b",
    r"(?i)\bwhite\s*(supremac|power|nationalist)\b",
    r"(?i)\b(ethnic|racial)\s*cleansing\b",
    r"(?i)\bgenocide\b",
]

MISLEADING_INDICATORS = [
    r"(?i)breaking(\s*:|\s*news)",
    r"(?i)exposed!|exposed:",
    r"(?i)what (they|the government|media) (don't|doesn't|won't) tell you",
    r"(?i)mainstream media (lies|won't|refuses|is hiding)",
    r"(?i)exposed.*truth",
    r"(?i)wake up|sheeple|open your eyes",
    r"(?i)banned (video|information|truth)",
    r"(?i)big pharma (conspiracy|doesn't want|hides)",
    r"(?i)deep state",
    r"(?i)fake news (media|cnn|bbc)",
    r"(?i)they don't want you to (know|see|read)",
    r"(?i)(exposed|leaked|secret) (documents?|files?|info)",
    r"(?i)share (this )?before (it's|they) (deleted|removed|taken down)",
]

CREDIBLE_DOMAINS = [
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk",
    "nytimes.com", "washingtonpost.com", "theguardian.com",
    "nature.com", "science.org", "pubmed.ncbi.nlm.nih.gov",
    "who.int", "cdc.gov", "nasa.gov", "gov.uk",
    "edu", "ac.uk", "ac.in",
    "wikipedia.org", "britannica.com",
    "snopes.com", "factcheck.org", "politifact.com",
]

# ─── HELPERS ───────────────────────────────────────────

def fetch_page_content(url):
    """Fetch and extract meaningful text from a URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Could not fetch URL: {str(e)}")

    soup = BeautifulSoup(resp.text, "lxml")

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "iframe", "noscript", "svg"]):
        tag.decompose()

    # Extract title
    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)

    # Extract meta description
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag:
        meta_desc = meta_tag.get("content", "")

    # Extract main text
    article = soup.find("article") or soup.find("main") or soup.find("body")
    paragraphs = []
    if article:
        for p in article.find_all(["p", "h1", "h2", "h3", "li"]):
            text = p.get_text(strip=True)
            if len(text) > 20:
                paragraphs.append(text)

    full_text = "\n".join(paragraphs)

    # Limit text length
    if len(full_text) > 8000:
        full_text = full_text[:8000]

    return {
        "title": title,
        "meta_description": meta_desc,
        "text": full_text,
        "text_length": len(full_text),
    }


def check_domain_credibility(url):
    """Assess credibility based on the domain."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")

    score_bonus = 0
    is_credible = False

    for credible in CREDIBLE_DOMAINS:
        if domain.endswith(credible):
            score_bonus = 20
            is_credible = True
            break

    has_https = parsed.scheme == "https"
    if has_https:
        score_bonus += 5

    return {
        "domain": domain,
        "is_credible_source": is_credible,
        "has_https": has_https,
        "score_bonus": score_bonus,
    }


def detect_patterns(text, patterns):
    """Return matching patterns found in text."""
    matches = []
    for pattern in patterns:
        found = re.findall(pattern, text)
        if found:
            matches.append({
                "pattern": pattern,
                "count": len(found),
                "sample": found[0] if isinstance(found[0], str) else str(found[0]),
            })
    return matches


def analyze_with_fallback(text, title, url):
    """Analyze content using heuristic NLP (no API needed)."""

    # ── Scam Detection ──
    scam_matches = detect_patterns(text, SCAM_PATTERNS)
    scam_score = min(len(scam_matches) * 15, 100)
    is_scam = scam_score >= 30

    # ── Toxic Content Detection ──
    toxic_matches = detect_patterns(text, TOXIC_PATTERNS)
    toxicity_score = min(len(toxic_matches) * 20, 100)
    is_toxic = toxicity_score >= 20

    # ── Misleading Content Detection ──
    misleading_matches = detect_patterns(text, MISLEADING_INDICATORS)
    misleading_score = min(len(misleading_matches) * 12, 100)

    # ── Sentiment / Quality Signals ──
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
    total_sentences = len(sentences)

    exclamation_ratio = text.count("!") / max(len(text), 1) * 1000
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    question_marks = text.count("?")

    # ── Truth Score Calculation ──
    truth_score = 65  # Base score

    # Domain credibility
    domain_info = check_domain_credibility(url)
    truth_score += domain_info["score_bonus"]

    # Penalize for scam/toxic/misleading
    truth_score -= scam_score * 0.4
    truth_score -= toxicity_score * 0.3
    truth_score -= misleading_score * 0.3

    # Penalize excessive caps and exclamation marks
    if caps_ratio > 0.3:
        truth_score -= 15
    if exclamation_ratio > 5:
        truth_score -= 10

    # Reward longer, well-structured content
    if total_sentences > 10:
        truth_score += 5
    if total_sentences > 30:
        truth_score += 5

    # Clamp
    truth_score = max(0, min(100, int(truth_score)))

    # ── Summary Generation (extractive) ──
    if total_sentences >= 3:
        summary_sentences = sentences[:4]
        summary = ". ".join(summary_sentences) + "."
    elif title:
        summary = f"{title}. {sentences[0] if sentences else 'No detailed content could be extracted.'}"
    else:
        summary = "The content of this page could not be summarized effectively."

    if len(summary) > 500:
        summary = summary[:497] + "..."

    # ── Warnings ──
    warnings = []
    if is_scam:
        warnings.append({
            "type": "scam",
            "severity": "high",
            "message": "⚠ Potential scam or misleading content detected. Multiple deceptive patterns found.",
            "details": [m["sample"] for m in scam_matches[:3]],
        })
    if is_toxic:
        warnings.append({
            "type": "toxic",
            "severity": "high",
            "message": "🚨 Hate speech or toxic content detected. This content contains harmful language.",
            "details": [m["sample"] for m in toxic_matches[:3]],
        })
    if misleading_score >= 25:
        warnings.append({
            "type": "misleading",
            "severity": "medium",
            "message": "⚡ Potentially misleading content. Sensationalist or manipulative language detected.",
            "details": [m["sample"] for m in misleading_matches[:3]],
        })
    if caps_ratio > 0.3:
        warnings.append({
            "type": "style",
            "severity": "low",
            "message": "📢 Excessive use of capital letters — often associated with clickbait or aggressive content.",
        })
    if not domain_info["has_https"]:
        warnings.append({
            "type": "security",
            "severity": "medium",
            "message": "🔓 This website does not use HTTPS. Connection is not secure.",
        })

    return {
        "summary": summary,
        "truth_score": truth_score,
        "is_scam": is_scam,
        "scam_score": scam_score,
        "is_toxic": is_toxic,
        "toxicity_score": toxicity_score,
        "misleading_score": misleading_score,
        "warnings": warnings,
        "domain_info": domain_info,
        "analysis_method": "heuristic",
        "content_stats": {
            "sentences": total_sentences,
            "text_length": len(text),
        },
    }


def analyze_with_openai(text, title, url):
    """Analyze content using OpenAI GPT API."""
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""Analyze the following webpage content for credibility and safety.

Title: {title}
URL: {url}
Content (truncated):
{text[:4000]}

Provide your analysis as valid JSON with these exact fields:
{{
  "summary": "A concise 3-4 sentence summary of the content",
  "truth_score": <integer 0-100, where 100 is fully credible>,
  "is_scam": <boolean>,
  "scam_reasoning": "Brief explanation if scam detected",
  "is_toxic": <boolean>,
  "toxicity_reasoning": "Brief explanation if toxic content detected",
  "is_misleading": <boolean>,
  "misleading_reasoning": "Brief explanation if misleading content detected",
  "key_claims": ["list of key claims made in the content"],
  "credibility_factors": ["list of factors affecting credibility"]
}}

Be thorough and fair. Only flag content as scam/toxic if there is clear evidence."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a content credibility analyst. Respond only with valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800,
        )

        result_text = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if result_text.startswith("```"):
            result_text = re.sub(r"^```(?:json)?\n?", "", result_text)
            result_text = re.sub(r"\n?```$", "", result_text)

        ai_result = json.loads(result_text)

        # Build warnings
        warnings = []
        if ai_result.get("is_scam"):
            warnings.append({
                "type": "scam",
                "severity": "high",
                "message": f"⚠ Scam Alert: {ai_result.get('scam_reasoning', 'Potentially deceptive content detected.')}",
            })
        if ai_result.get("is_toxic"):
            warnings.append({
                "type": "toxic",
                "severity": "high",
                "message": f"🚨 Toxic Content: {ai_result.get('toxicity_reasoning', 'Harmful language detected.')}",
            })
        if ai_result.get("is_misleading"):
            warnings.append({
                "type": "misleading",
                "severity": "medium",
                "message": f"⚡ Misleading: {ai_result.get('misleading_reasoning', 'Potentially misleading claims detected.')}",
            })

        domain_info = check_domain_credibility(url)

        return {
            "summary": ai_result.get("summary", ""),
            "truth_score": max(0, min(100, ai_result.get("truth_score", 50))),
            "is_scam": ai_result.get("is_scam", False),
            "is_toxic": ai_result.get("is_toxic", False),
            "warnings": warnings,
            "domain_info": domain_info,
            "key_claims": ai_result.get("key_claims", []),
            "credibility_factors": ai_result.get("credibility_factors", []),
            "analysis_method": "openai-gpt4o-mini",
        }

    except Exception as e:
        print(f"OpenAI API error: {e}")
        # Fallback to heuristic
        return analyze_with_fallback(text, title, url)


# ─── TRANSLATION (English → Telugu) ───────────────────

TELUGU_STRINGS = {
    "summary": "సారాంశం",
    "truth_score": "నిజం స్కోర్",
    "scam_detected": "⚠ మోసం గుర్తించబడింది",
    "toxic_detected": "🚨 విషపూరిత కంటెంట్ కనుగొనబడింది",
    "misleading_detected": "⚡ తప్పుదారి పట్టించే కంటెంట్",
    "safe_content": "✅ ఈ కంటెంట్ సురక్షితంగా కనిపిస్తుంది",
    "credible_source": "విశ్వసనీయ మూలం",
    "not_credible": "అవిశ్వసనీయ మూలం",
    "high_risk": "అధిక ప్రమాదం",
    "medium_risk": "మధ్యస్థ ప్రమాదం",
    "low_risk": "తక్కువ ప్రమాదం",
    "no_risk": "ప్రమాదం లేదు",
    "analysis_complete": "విశ్లేషణ పూర్తయింది",
    "analyzing": "విశ్లేషిస్తోంది...",
    "enter_url": "URL ఇక్కడ నమోదు చేయండి",
    "analyze": "విశ్లేషించు",
    "history": "చరిత్ర",
    "no_history": "ఇంకా విశ్లేషణ జరగలేదు",
    "powered_by": "AI ద్వారా శక్తివంతం",
}


# ─── ROUTES ────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "No URL provided"}), 400

    url = data["url"].strip()

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    if not parsed.netloc:
        return jsonify({"error": "Invalid URL format"}), 400

    try:
        # Step 1: Fetch content
        page = fetch_page_content(url)

        if not page["text"] or len(page["text"]) < 50:
            return jsonify({
                "error": "Could not extract enough text from the page. "
                         "The site may be JavaScript-heavy or block scrapers."
            }), 422

        # Step 2: Analyze
        if USE_OPENAI:
            result = analyze_with_openai(page["text"], page["title"], url)
        else:
            result = analyze_with_fallback(page["text"], page["title"], url)

        # Step 3: Build response
        response = {
            "success": True,
            "url": url,
            "title": page["title"],
            "analyzed_at": datetime.now().isoformat(),
            **result,
        }

        # Step 4: Save to history
        history_entry = {
            "id": hashlib.md5(f"{url}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            "url": url,
            "title": page["title"],
            "truth_score": result["truth_score"],
            "is_scam": result.get("is_scam", False),
            "is_toxic": result.get("is_toxic", False),
            "warning_count": len(result.get("warnings", [])),
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        analysis_history.insert(0, history_entry)

        # Keep only last 50
        if len(analysis_history) > 50:
            analysis_history.pop()

        return jsonify(response)

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    return jsonify({"history": analysis_history})


@app.route("/api/translations/<lang>", methods=["GET"])
def get_translations(lang):
    if lang == "te":
        return jsonify(TELUGU_STRINGS)
    return jsonify({"error": "Language not supported"}), 404


# ─── MAIN ──────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "═" * 50)
    print("  🔍 TruthLens — AI Content Credibility Analyzer")
    print("═" * 50)
    if USE_OPENAI:
        print("  ✅ OpenAI API key detected — using GPT-4o-mini")
    else:
        print("  ⚡ No OpenAI key — using built-in heuristic analysis")
        print("  💡 Add OPENAI_API_KEY to .env for AI-powered analysis")
    print(f"  🌐 Running at http://localhost:5000")
    print("═" * 50 + "\n")

    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
