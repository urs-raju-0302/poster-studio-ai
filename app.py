from __future__ import annotations

import io
import os
import random
import textwrap
from datetime import date
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    import qrcode
except ImportError:
    qrcode = None

APP_DIR = Path(__file__).parent
OUT_DIR = APP_DIR / "generated_posters"
OUT_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Poster Studio AI", page_icon="🎨", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --ink:#f5f7ff; --muted:#a7b0cb; --panel:#11172a; --line:rgba(255,255,255,.09); }
.stApp { background: radial-gradient(ellipse at 15% 0%, #20284a 0%, #0b1020 44%, #080c18 100%); color:var(--ink); }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.block-container { padding-top:1.5rem; max-width:1500px; }
section[data-testid="stSidebar"] { background:rgba(12,17,32,.94); border-right:1px solid var(--line); }
.hero { padding:1.4rem 1.5rem; border:1px solid var(--line); border-radius:22px; background:linear-gradient(120deg,rgba(91,80,210,.20),rgba(28,174,197,.08)); margin-bottom:1.25rem; }
.eyebrow { color:#9f9cff; letter-spacing:.18em; text-transform:uppercase; font-size:.72rem; font-weight:700; }
.hero h1 { font-family:'Space Grotesk',sans-serif; font-size:2.35rem; line-height:1.1; margin:.35rem 0 .5rem; color:#fff; }
.hero p { color:#b7c0d9; margin:0; max-width:760px; }
.panel { border:1px solid var(--line); border-radius:18px; padding:1rem 1.1rem; background:rgba(17,23,42,.76); }
.small-label { font-size:.76rem; color:#9ba8c8; text-transform:uppercase; letter-spacing:.12em; font-weight:700; }
.badge { display:inline-block; border:1px solid rgba(126,116,255,.35); color:#c9c5ff; background:rgba(126,116,255,.12); padding:.25rem .55rem; border-radius:999px; font-size:.75rem; }
div.stButton > button, div.stDownloadButton > button { border-radius:11px; border:1px solid rgba(140,130,255,.35); background:linear-gradient(110deg,#6557e8,#4778e7); color:white; font-weight:700; min-height:2.7rem; }
div.stButton > button:hover, div.stDownloadButton > button:hover { border-color:#aaa4ff; color:white; }
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stNumberInput input { background:#11182c; color:#f7f8ff; border-color:#303b5b; }
label, .stMarkdown, p { color:#e3e8f8; }
[data-testid="stMetric"] { background:rgba(255,255,255,.035); border:1px solid var(--line); padding:.7rem .9rem; border-radius:14px; }
hr { border-color:var(--line); }
footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ---------- Content generation (works without an API key) ----------
TITLE_BANK = {
    "Technology": ["FutureForge", "TechNova", "CodeVerse", "NextGen Summit", "Digital Frontiers"],
    "AI & Data": ["AI Innovate", "Neural Nexus", "DataVision", "MindMesh", "IntelliFest"],
    "Cultural Fest": ["Vibrance", "Rhythm & Roots", "Culture Carnival", "Mosaic", "Utsav"],
    "Workshop": ["SkillSprint", "The Learning Lab", "Build & Bloom", "NextStep Workshop", "Hands-On Hub"],
    "Business": ["VisionForward", "LaunchPoint", "Elevate Summit", "Impact Forum", "The Growth Exchange"],
    "Academic": ["Ideas in Action", "Knowledge Connect", "The Scholar Forum", "LearnSphere", "Research Connect"],
    "General Event": ["The Big Gathering", "Inspire Day", "Momentum", "Together Forward", "The Experience"]
}
TAGLINES = {
    "Technology": ["Imagine more. Build what’s next.", "Code ideas into reality.", "Where bold ideas become breakthroughs."],
    "AI & Data": ["Think beyond. Build the future.", "Human creativity meets machine intelligence.", "Turn data into discovery."],
    "Cultural Fest": ["One campus. A thousand stories.", "Feel the rhythm. Celebrate the moment.", "Different voices. One unforgettable vibe."],
    "Workshop": ["Learn it today. Use it tomorrow.", "Make skills happen.", "Curiosity in. New possibilities out."],
    "Business": ["Ideas that move business forward.", "Connect with possibility.", "Make the next move count."],
    "Academic": ["Question boldly. Discover deeply.", "Curiosity creates progress.", "Share ideas. Shape tomorrow."],
    "General Event": ["Come curious. Leave inspired.", "Good people. Great ideas. One moment.", "Be part of something memorable."]
}

def generate_copy(description: str, category: str, audience: str, style: str) -> dict:
    """Create event-copy suggestions locally from built-in templates; no API key or internet needed."""
    desc = " ".join(description.strip().split())
    rng = random.Random(f"{desc}|{category}|{audience}|{style}")
    title = rng.choice(TITLE_BANK.get(category, TITLE_BANK["General Event"]))
    tagline = rng.choice(TAGLINES.get(category, TAGLINES["General Event"]))
    clean = desc.replace("Organizing", "").replace("organizing", "").replace("Create a poster for", "").replace("create a poster for", "")
    clean = clean.strip(" .,!\n")
    if clean:
        topic = clean[:1].upper() + clean[1:]
        if len(topic) > 100:
            topic = topic[:97].rstrip() + "..."
    else:
        topic = f"A {category.lower()} event for {audience.lower()}"
    blurb = f"Join us for {topic[0].lower() + topic[1:]}. Discover fresh ideas, connect with your community, and be part of the experience."
    return {"title": title, "tagline": tagline, "description": blurb, "cta": "REGISTER NOW"}

# ---------- Background generation (local and free) ----------
def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

def blend(a, b, t):
    return tuple(round(a[i] * (1-t) + b[i] * t) for i in range(3))

def make_gradient(size: tuple[int, int], color1: str, color2: str, style: str, seed: str) -> Image.Image:
    w, h = size
    c1, c2 = hex_rgb(color1), hex_rgb(color2)
    img = Image.new("RGB", size)
    px = img.load()
    rng = random.Random(seed)
    for y in range(h):
        for x in range(w):
            if style == "Diagonal glow":
                t = min(1, max(0, (x / max(1,w-1) * .58 + y / max(1,h-1) * .42)))
            elif style == "Midnight radial":
                dx, dy = (x-w*.48)/(w*.8), (y-h*.25)/(h*.8)
                t = min(1, (dx*dx + dy*dy)**.5)
            elif style == "Sunset":
                t = min(1, max(0, y / max(1,h-1) * .8 + x / max(1,w-1) * .2))
            else:
                t = y / max(1,h-1)
            col = blend(c1, c2, t)
            # Soft, deterministic texture keeps local backgrounds from looking flat.
            noise = rng.randint(-2, 2)
            px[x, y] = tuple(max(0, min(255, v + noise)) for v in col)
    return img

def draw_background(size: tuple[int, int], color1: str, color2: str, style: str, seed: str, category: str) -> Image.Image:
    img = make_gradient(size, color1, color2, style, seed)
    w, h = size
    overlay = Image.new("RGBA", size, (0,0,0,0))
    d = ImageDraw.Draw(overlay, "RGBA")
    rng = random.Random(seed + category)
    # Abstract, decorative graphic shapes.
    if category in ("Technology", "AI & Data"):
        points = [(rng.randint(0,w), rng.randint(0,h)) for _ in range(24)]
        for i, (x,y) in enumerate(points):
            nearest = sorted(points, key=lambda p:(p[0]-x)**2+(p[1]-y)**2)[1:4]
            for xx, yy in nearest:
                if (xx-x)**2+(yy-y)**2 < (w*.24)**2:
                    d.line((x,y,xx,yy), fill=(175,220,255,40), width=max(1,w//700))
            r = max(2, w//120)
            d.ellipse((x-r,y-r,x+r,y+r), fill=(175,220,255,120))
        for r in (w*.18,w*.26,w*.34):
            d.ellipse((w*.52-r,h*.26-r,w*.52+r,h*.26+r), outline=(180,150,255,42), width=max(2,w//350))
    elif category == "Cultural Fest":
        for _ in range(34):
            x,y = rng.randint(-w//5,w), rng.randint(0,h)
            r = rng.randint(max(8,w//50),max(12,w//12))
            color = rng.choice([(255,190,95,38),(255,100,170,34),(255,240,170,30)])
            d.arc((x-r,y-r,x+r,y+r), rng.randint(0,180), rng.randint(180,360), fill=color, width=max(2,w//250))
        for _ in range(28):
            x,y = rng.randint(0,w), rng.randint(0,h)
            r=max(2,w//180)
            d.line((x-r*2,y,x+r*2,y),fill=(255,220,150,65),width=max(1,w//500))
            d.line((x,y-r*2,x,y+r*2),fill=(255,220,150,65),width=max(1,w//500))
    elif category == "Nature & Environment":
        for _ in range(30):
            x,y=rng.randint(-w//8,w),rng.randint(0,h)
            rw=rng.randint(max(8,w//45),max(12,w//16))
            rh=max(5,int(rw*.45))
            d.ellipse((x-rw,y-rh,x+rw,y+rh),outline=(140,255,190,38),width=max(2,w//350))
            d.line((x-rw,y+rh,x+rw,y-rh),fill=(140,255,190,25),width=max(1,w//500))
    elif category in ("Sports & Gaming", "Music Festival"):
        for _ in range(28):
            x,y=rng.randint(0,w),rng.randint(0,h)
            dx=rng.randint(-w//12,w//12)
            dy=rng.randint(w//30,w//8)
            d.line([(x,y),(x+dx,y-dy),(x-dx,y+dy),(x,y)],fill=(220,230,255,30),width=max(2,w//350))
    else:
        for _ in range(22):
            x,y = rng.randint(0,w), rng.randint(0,h)
            r = rng.randint(w//80,w//22)
            d.ellipse((x-r,y-r,x+r,y+r), outline=(220,230,255,22), width=max(1,w//450))
    overlay = overlay.filter(ImageFilter.GaussianBlur(max(1,w//500)))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


# ---------- Fonts and poster composition ----------
def get_font(size: int, bold: bool = False, family: str = "Sans"):
    """Load a locally available font family with sensible cross-platform fallbacks."""
    windows_fonts = {
        "Sans": (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
        "Serif": (r"C:\Windows\Fonts\georgia.ttf", r"C:\Windows\Fonts\georgiab.ttf"),
        "Mono": (r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\consolab.ttf"),
        "Display": (r"C:\Windows\Fonts\impact.ttf", r"C:\Windows\Fonts\impact.ttf"),
    }
    linux_fonts = {
        "Sans": ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        "Serif": ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
        "Mono": ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
        "Display": ("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"),
    }
    idx = 1 if bold else 0
    candidates = []
    if os.name == "nt":
        candidates.append(windows_fonts.get(family, windows_fonts["Sans"])[idx])
        candidates.append(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf")
    candidates.append(str(APP_DIR / "assets" / "fonts" / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")))
    candidates.append(linux_fonts.get(family, linux_fonts["Sans"])[idx])
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()

def wrap_by_pixels(draw, text, font, max_width):
    words = text.split()
    lines, line = [], ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textbbox((0,0), candidate, font=font)[2] <= max_width or not line:
            line = candidate
        else:
            lines.append(line); line = word
    if line: lines.append(line)
    return lines

def compose_poster(bg: Image.Image, data: dict, settings: dict, logo: Image.Image | None = None, qr_value: str = "") -> Image.Image:
    width, height = settings["dimensions"]
    img = bg.convert("RGB").resize((width,height), Image.Resampling.LANCZOS).convert("RGBA")
    # Gradient shade at the bottom and a light veil for reliable text contrast.
    shade = Image.new("RGBA", (width,height), (0,0,0,0)); sd = ImageDraw.Draw(shade)
    for y in range(height):
        t = y / height
        alpha = int(10 + 155 * max(0,(t-.25)/.75)**1.5)
        sd.line((0,y,width,y), fill=(5,8,22,alpha))
    img = Image.alpha_composite(img, shade)
    d = ImageDraw.Draw(img)
    margin = int(width*.075)
    accent = settings["accent"]
    text_color = settings["text_color"]
    template = settings.get("template", "Modern Gradient")
    # Decorative template-specific framing makes the same content feel like a new design.
    if template == "Neon Circuit":
        for offset in range(0, int(width*.42), max(18, width//22)):
            d.line((width-offset, 0, width, offset), fill=(*hex_rgb(accent), 85), width=max(2, width//280))
        d.rounded_rectangle((int(width*.045), int(height*.035), width-int(width*.045), height-int(height*.035)), radius=int(width*.035), outline=(*hex_rgb(accent), 150), width=max(2,width//300))
    elif template == "Festival Celebration":
        rng = random.Random(settings.get("seed", "festival"))
        for _ in range(38):
            x, y0 = rng.randint(0,width), rng.randint(0,int(height*.48))
            r = rng.randint(max(5,width//100), max(8,width//35))
            d.ellipse((x-r,y0-r,x+r,y0+r), outline=(*hex_rgb(accent), 120), width=max(2,width//350))
        d.rounded_rectangle((int(width*.045), int(height*.035), width-int(width*.045), height-int(height*.035)), radius=int(width*.06), outline=(*hex_rgb(accent), 110), width=max(2,width//350))
    elif template == "Editorial Minimal":
        d.rectangle((0,0,int(width*.035),height), fill=(*hex_rgb(accent),255))
        d.line((margin,int(height*.055),width-margin,int(height*.055)), fill=(*hex_rgb(accent),220), width=max(3,width//250))
    elif template == "Elegant Luxe":
        d.rounded_rectangle((int(width*.04),int(height*.035),width-int(width*.04),height-int(height*.035)), radius=int(width*.025), outline=(235,205,140,190), width=max(2,width//350))
        d.ellipse((width-int(width*.18),int(height*.04),width-int(width*.07),int(height*.15)), outline=(235,205,140,100), width=max(2,width//300))
    elif template == "Corporate Clean":
        d.polygon([(0,0),(int(width*.34),0),(0,int(height*.18))], fill=(*hex_rgb(accent),70))
        d.rectangle((0,int(height*.965),width,height), fill=(*hex_rgb(accent),220))
    elif template == "Sports Arena":
        d.polygon([(0,0),(int(width*.14),0),(0,int(height*.24))], fill=(*hex_rgb(accent),155))
        d.polygon([(width,int(height*.68)),(width,int(height*.96)),(int(width*.70),height)], fill=(*hex_rgb(accent),95))
        d.line((int(width*.06),int(height*.62),int(width*.94),int(height*.62)), fill=(*hex_rgb(accent),145), width=max(3,width//220))
    elif template == "Music Pulse":
        rng = random.Random(settings.get("seed","music"))
        bar_w=max(3,width//65)
        gap=max(2,width//150)
        x=int(width*.06)
        while x < int(width*.94):
            bh=rng.randint(int(height*.025),int(height*.10))
            d.rounded_rectangle((x,int(height*.045),x+bar_w,int(height*.045)+bh),radius=max(2,bar_w//2),fill=(*hex_rgb(accent),95))
            d.rounded_rectangle((x,height-int(height*.055)-bh,x+bar_w,height-int(height*.055)),radius=max(2,bar_w//2),fill=(*hex_rgb(accent),75))
            x += bar_w+gap
    elif template == "Nature Fresh":
        d.rounded_rectangle((int(width*.045),int(height*.035),width-int(width*.045),height-int(height*.035)),radius=int(width*.055),outline=(*hex_rgb(accent),140),width=max(2,width//350))
        for i in range(7):
            x=int(width*(.68+i*.025))
            y=int(height*(.06+(i%3)*.035))
            d.ellipse((x,y,x+int(width*.09),y+int(height*.035)),outline=(*hex_rgb(accent),65),width=max(2,width//400))
    elif template == "Retro Pop":
        d.rectangle((0,0,int(width*.22),int(height*.12)),fill=(*hex_rgb(accent),100))
        d.rectangle((width-int(width*.16),height-int(height*.20),width,height),fill=(*hex_rgb(accent),85))
        dot_r=max(2,width//260)
        for row in range(5):
            for col in range(6):
                x=int(width*.72)+col*dot_r*4
                y=int(height*.18)+row*dot_r*4
                d.ellipse((x-dot_r,y-dot_r,x+dot_r,y+dot_r),fill=(*hex_rgb(accent),55))
    # Advanced text controls: independent size, position, alignment, font and effects.
    title_y = int(height * settings.get("title_y", 11) / 100)
    title_size = int(width * settings.get("title_size", 8) / 100)
    font_family = settings.get("font_family", "Sans")
    title_font = get_font(max(22, title_size), True, font_family)
    title = data.get("title", "YOUR EVENT TITLE").strip() or "YOUR EVENT TITLE"
    title_lines = wrap_by_pixels(d, title.upper(), title_font, width-2*margin)
    line_h = int(title_size*1.18)
    title_align = settings.get("title_align", "Left")
    title_color = settings.get("title_color", text_color)
    effect = settings.get("text_effect", "Shadow")
    for i, line in enumerate(title_lines[:3]):
        bbox = d.textbbox((0,0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        tx = margin if title_align == "Left" else ((width-tw)//2 if title_align == "Center" else width-margin-tw)
        ty = title_y+i*line_h
        if effect == "Shadow":
            d.text((tx+max(2,width//450),ty+max(2,width//450)), line, font=title_font, fill=(0,0,0,180), stroke_width=0)
        elif effect == "Outline":
            d.text((tx,ty), line, font=title_font, fill=title_color, stroke_width=max(2,width//300), stroke_fill=(8,10,22,230))
        d.text((tx,ty), line, font=title_font, fill=title_color)
    y = title_y + min(len(title_lines),3)*line_h + int(height*.018)
    # Accent rule follows the title alignment.
    rule_w = int(width * settings.get("rule_width", 19) / 100)
    rule_h = max(5, width//120)
    rule_align = title_align
    rule_x = margin if rule_align == "Left" else ((width-rule_w)//2 if rule_align == "Center" else width-margin-rule_w)
    d.rounded_rectangle((rule_x,y,rule_x+rule_w,y+rule_h), radius=max(2,width//250), fill=accent)
    default_tag_y = y + int(height*.035)
    tag_y = int(height * settings.get("tagline_y", 25) / 100)
    tag_y = max(default_tag_y, tag_y)
    tag_size = int(width * settings.get("tagline_size", 3.8) / 100)
    tag_font = get_font(max(17,tag_size), True, font_family)
    tag_align = settings.get("tagline_align", title_align)
    tag_color = settings.get("tagline_color", text_color)
    for line in wrap_by_pixels(d, data.get("tagline", "Your tagline goes here"), tag_font, width-2*margin)[:3]:
        bbox = d.textbbox((0,0), line, font=tag_font); tw = bbox[2]-bbox[0]
        tx = margin if tag_align == "Left" else ((width-tw)//2 if tag_align == "Center" else width-margin-tw)
        d.text((tx,tag_y), line, font=tag_font, fill=tag_color)
        tag_y += int(tag_size*1.28)
    desc_y = max(tag_y + int(height*.018), int(height * settings.get("description_y", 37) / 100))
    desc_size = int(width * settings.get("description_size", 2.4) / 100)
    desc_font = get_font(max(14,desc_size), False, font_family)
    desc_align = settings.get("description_align", title_align)
    desc_color = settings.get("description_color", "#EBEFFF")
    for line in wrap_by_pixels(d, data.get("description", ""), desc_font, width-2*margin)[:5]:
        bbox = d.textbbox((0,0), line, font=desc_font); tw = bbox[2]-bbox[0]
        tx = margin if desc_align == "Left" else ((width-tw)//2 if desc_align == "Center" else width-margin-tw)
        d.text((tx,desc_y), line, font=desc_font, fill=desc_color)
        desc_y += int(desc_size*1.42)
    # Details cards near bottom.
    details_y = int(height*.70)
    card_h = int(height*.145)
    card_fill = (8,13,30,165) if template != "Editorial Minimal" else (5,8,18,115)
    card_outline = (*hex_rgb(accent), 120) if template in ("Neon Circuit", "Elegant Luxe") else (255,255,255,45)
    d.rounded_rectangle((margin,details_y,width-margin,details_y+card_h), radius=int(width*.025), fill=card_fill, outline=card_outline, width=max(1,width//500))
    small = get_font(max(13,int(width*.022)), True)
    normal = get_font(max(14,int(width*.025)), False)
    left_x = margin + int(width*.035)
    date_text = data.get("date", "DATE TO BE ANNOUNCED")
    time_text = data.get("time", "TIME TO BE ANNOUNCED")
    venue_text = data.get("venue", "VENUE TO BE ANNOUNCED")
    d.text((left_x,details_y+int(card_h*.18)), "WHEN", font=small, fill=accent)
    d.text((left_x,details_y+int(card_h*.42)), f"{date_text}  ·  {time_text}", font=normal, fill=text_color)
    d.text((left_x,details_y+int(card_h*.70)), "WHERE", font=small, fill=accent)
    d.text((left_x+int(width*.13),details_y+int(card_h*.70)), venue_text[:42], font=normal, fill=text_color)
    # CTA pill.
    cta = data.get("cta", "REGISTER NOW").strip().upper() or "REGISTER NOW"
    cta_font = get_font(max(14,int(width*.026)), True)
    cta_box = d.textbbox((0,0),cta,font=cta_font)
    pill_w = cta_box[2]+int(width*.07); pill_h = int(height*.055)
    pill_y = int(height*.88)
    pill_radius = 4 if template == "Editorial Minimal" else (int(pill_h*.18) if template == "Corporate Clean" else pill_h//2)
    d.rounded_rectangle((margin,pill_y,margin+pill_w,pill_y+pill_h),radius=pill_radius,fill=accent)
    d.text((margin+int(width*.035),pill_y+(pill_h-(cta_box[3]-cta_box[1]))//2-2),cta,font=cta_font,fill=(12,15,30))
    if logo is not None:
        logo.thumbnail((int(width*.16),int(height*.09)), Image.Resampling.LANCZOS)
        lx,ly = width-margin-logo.width, int(height*.045)
        if logo.mode == "RGBA": img.alpha_composite(logo,(lx,ly))
        else: img.paste(logo,(lx,ly))
    if qr_value.strip() and qrcode is not None:
        qr = qrcode.make(qr_value.strip()).convert("RGB")
        qr_size = int(width*.15); qr.thumbnail((qr_size,qr_size))
        qx,qy = width-margin-qr.width, int(height*.86)
        img.paste(qr,(qx,qy))
    return img.convert("RGB")

# ---------- Session defaults ----------
if "copy_data" not in st.session_state:
    st.session_state.copy_data = {"title":"AI INNOVATE 2026", "tagline":"Think beyond. Build the future.", "description":"Join an inspiring event for ideas, creativity, and collaboration.", "cta":"REGISTER NOW", "date":date.today().strftime("%d %b %Y"), "time":"10:00 AM", "venue":"College Auditorium"}
if "bg_image" not in st.session_state:
    st.session_state.bg_image = None
if "background_signature" not in st.session_state:
    st.session_state.background_signature = None
if "logo_image" not in st.session_state:
    st.session_state.logo_image = None
if "last_poster" not in st.session_state:
    st.session_state.last_poster = None
if "design_variations" not in st.session_state:
    st.session_state.design_variations = None

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 🎨 Poster Studio AI")
    st.caption("Create a poster. Keep the words yours.")
    st.markdown("---")
    st.markdown("**1 · Event brief**")
    description = st.text_area("Describe your event", value="A college hackathon focused on AI, machine learning, and creative software solutions.", height=115, help="Mention the event topic, audience, mood, and purpose.")
    category = st.selectbox(
        "Event category",
        ["Technology", "AI & Data", "Cultural Fest", "Workshop", "Business",
         "Academic", "Sports & Gaming", "Music Festival", "Nature & Environment", "General Event"],
        index=1,
    )
    audience = st.selectbox("Target audience", ["College students", "School students", "Professionals", "Researchers", "General public", "Entrepreneurs"])
    visual_style = st.selectbox("Background style", ["Diagonal glow", "Midnight radial", "Sunset", "Vertical gradient"])
    template = st.selectbox(
        "Design template",
        ["Modern Gradient", "Neon Circuit", "Festival Celebration", "Editorial Minimal",
         "Elegant Luxe", "Corporate Clean", "Sports Arena", "Music Pulse",
         "Nature Fresh", "Retro Pop"],
        help="Choose a distinct visual layout and decorative frame.",
    )
    with st.expander("🖼️ Background generator", expanded=False):
        st.caption("Free local graphics only: no API keys, account, paid credits, or internet-based image model required.")
        st.write("Choose a background style, template, category, and colors in the sidebar. The app draws a matching background locally.")
        st.info("This version does not generate diffusion-model images. It uses procedural gradients and decorative graphics.")
    st.markdown("---")
    st.markdown("**2 · Color palette**")
    palettes = {
        "Neon violet": ("#17143D", "#5D3FD3", "#A8F0FF"),
        "Ocean blue": ("#071D3A", "#126E9B", "#78E5FF"),
        "Sunset coral": ("#32132E", "#D34F73", "#FFD18B"),
        "Emerald night": ("#071F20", "#117C70", "#9DF3C4"),
        "Rose Gold": ("#301821", "#A64D79", "#F6C6A8"),
        "Golden Festival": ("#3B170D", "#C85A18", "#FFD166"),
        "Monochrome": ("#101116", "#343844", "#F2F2F2"),
        "Arctic Mint": ("#062D35", "#167D8D", "#9CFFE3"),
        "Custom": ("#17143D", "#5D3FD3", "#A8F0FF"),
    }

    def apply_quick_palette():
        selected = st.session_state.get("palette_choice", "Neon violet")
        if selected != "Custom":
            p1, p2, pa = palettes[selected]
            st.session_state["c1"] = p1
            st.session_state["c2"] = p2
            st.session_state["ca"] = pa

    if "c1" not in st.session_state:
        st.session_state["c1"] = palettes["Neon violet"][0]
    if "c2" not in st.session_state:
        st.session_state["c2"] = palettes["Neon violet"][1]
    if "ca" not in st.session_state:
        st.session_state["ca"] = palettes["Neon violet"][2]

    palette = st.selectbox(
        "Quick palette",
        list(palettes.keys()),
        index=0,
        key="palette_choice",
        on_change=apply_quick_palette,
    )
    color1 = st.color_picker("Background color 1", key="c1")
    color2 = st.color_picker("Background color 2", key="c2")
    accent = st.color_picker("Accent color", key="ca")

    # Local backgrounds are regenerated when their design inputs change,
    # so color pickers update both the preview and the downloaded PNG.
    background_signature = (color1, color2, visual_style, description, category)
    previous_signature = st.session_state.get("background_signature")
    if previous_signature is not None and previous_signature != background_signature:
        if st.session_state.get("bg_image_mode", "local") == "local":
            st.session_state.bg_image = None
    st.session_state.background_signature = background_signature
    st.markdown("---")
    st.markdown("**3 · Poster format**")
    fmt = st.selectbox("Canvas size", ["Instagram post · 1080 × 1350", "Instagram story · 1080 × 1920", "A4 portrait · 1240 × 1754", "Square · 1080 × 1080"], index=0)
    dimensions = {"Instagram post · 1080 × 1350":(1080,1350),"Instagram story · 1080 × 1920":(1080,1920),"A4 portrait · 1240 × 1754":(1240,1754),"Square · 1080 × 1080":(1080,1080)}[fmt]

# ---------- Main header ----------
st.markdown("""
<div class="hero">
  <div class="eyebrow">Generative design workspace</div>
  <h1>Make your next event<br/>impossible to miss.</h1>
  <p>Turn a simple event brief into a polished poster concept. Generate the copy, tune the look, edit every key detail, and export when it feels right.</p>
  <div style="margin-top:1rem"><span class="badge">✦ Text ideas</span>&nbsp; <span class="badge">✦ Poster backgrounds</span>&nbsp; <span class="badge">✦ Editable design</span>&nbsp; <span class="badge">✦ Free local mode</span></div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([0.9,1.1], gap="large")
with col_left:
    st.markdown("### 01 / Generate content")
    st.caption("Start with a short brief. You can edit every generated field below.")
    if st.button("✨ Generate event copy", use_container_width=True, key="gen_copy"):
        st.session_state.copy_data.update(generate_copy(description, category, audience, visual_style))
        st.toast("Fresh event copy is ready.", icon="✨")
    with st.container(border=True):
        st.markdown("**Edit your content**")
        data = st.session_state.copy_data
        data["title"] = st.text_input("Event title", value=data.get("title",""), max_chars=80)
        data["tagline"] = st.text_input("Tagline", value=data.get("tagline",""), max_chars=120)
        data["description"] = st.text_area("Short description", value=data.get("description",""), height=95, max_chars=320)
        data["cta"] = st.text_input("Call to action", value=data.get("cta","REGISTER NOW"), max_chars=35)
        dcol1,dcol2 = st.columns(2)
        data["date"] = dcol1.text_input("Event date", value=data.get("date",""), max_chars=32)
        data["time"] = dcol2.text_input("Event time", value=data.get("time",""), max_chars=32)
        data["venue"] = st.text_input("Venue", value=data.get("venue",""), max_chars=70)
    st.markdown("### 02 / Advanced text & layout")
    with st.container(border=True):
        with st.expander("🔠 Typography", expanded=True):
            font_family = st.selectbox("Font family", ["Sans", "Serif", "Mono", "Display"], index=0, help="Uses fonts installed with Windows or common local fallbacks.")
            title_size = st.slider("Title size", 5, 11, 8, help="Adjusts title size relative to the poster width.")
            tagline_size = st.slider("Tagline size", 2, 6, 4)
            description_size = st.slider("Description size", 1, 4, 2)
            text_effect = st.selectbox("Headline effect", ["None", "Shadow", "Outline"], index=1)
        with st.expander("↔️ Position & alignment", expanded=True):
            title_y = st.slider("Title vertical position", 4, 28, 11, help="Move the headline higher or lower.")
            title_align = st.selectbox("Title alignment", ["Left", "Center", "Right"], index=0)
            tagline_y = st.slider("Tagline vertical position", 18, 48, 25)
            tagline_align = st.selectbox("Tagline alignment", ["Left", "Center", "Right"], index=0)
            description_y = st.slider("Description vertical position", 28, 58, 37)
            description_align = st.selectbox("Description alignment", ["Left", "Center", "Right"], index=0)
        with st.expander("🎨 Individual text colors", expanded=False):
            title_color = st.color_picker("Title color", "#FFFFFF")
            tagline_color = st.color_picker("Tagline color", "#FFFFFF")
            description_color = st.color_picker("Description color", "#EBEFFF")
        logo_file = st.file_uploader("Upload a logo (optional)", type=["png","jpg","jpeg","webp"])
        if logo_file is not None:
            try: st.session_state.logo_image = Image.open(logo_file).convert("RGBA")
            except Exception: st.warning("That logo could not be opened. Try a PNG or JPG file.")
        qr_value = st.text_input("Registration URL or QR text (optional)", placeholder="https://example.com/register")
        st.caption("These controls affect the exported poster too. Text is flattened into the final image when you download it.")
    st.caption("Content suggestions run locally from built-in templates; no API key is needed.")

with col_right:
    st.markdown("### 03 / Poster preview")
    st.caption("A live preview of your current settings. Local backgrounds update when you change colors and design options.")
    with st.expander("✨ Explore 3 design variations", expanded=False):
        st.caption("Compare three design directions for the same event. These are locally drawn graphic designs, not AI-generated diffusion images.")
        if st.button("Generate 3 variations", use_container_width=True, key="make_variations"):
            variation_specs = [
                ("Festival Celebration", ("#3B170D", "#C85A18", "#FFD166"), "Sunset"),
                ("Neon Circuit", ("#071D3A", "#126E9B", "#78E5FF"), "Diagonal glow"),
                ("Elegant Luxe", ("#101116", "#343844", "#F2F2F2"), "Midnight radial"),
            ]
            thumbs = []
            for v_template, v_colors, v_style in variation_specs:
                v_bg = draw_background((360, 450), v_colors[0], v_colors[1], v_style,
                                       description + v_template, category)
                v_settings = {
                    "dimensions": (360, 450), "accent": v_colors[2], "text_color": "#FFFFFF",
                    "title_size": 8, "title_y": 11, "style": v_style, "template": v_template,
                    "seed": description + v_template,
                }
                v_poster = compose_poster(v_bg, st.session_state.copy_data, v_settings, None, "")
                thumbs.append((v_template, v_colors, v_poster))
            st.session_state.design_variations = thumbs
        if st.session_state.design_variations:
            variation_cols = st.columns(3)
            for i, (v_name, v_colors, v_image) in enumerate(st.session_state.design_variations):
                with variation_cols[i]:
                    st.image(v_image, caption=v_name, use_container_width=True)
                    st.caption(f"{v_colors[0]} → {v_colors[1]}")
            st.info("To use a variation in the main poster, select its matching design template and palette in the sidebar.")
    b1,b2 = st.columns(2)
    if b1.button("🎨 Refresh local background", use_container_width=True, key="gen_bg"):
        st.session_state.bg_image = draw_background((900,1125), color1, color2, visual_style, description, category)
        st.toast("A fresh local background is ready.", icon="🎨")
    if b2.button("🔄 Reset background", use_container_width=True, key="reset_bg"):
        st.session_state.bg_image = None
        st.rerun()
    st.caption("Background source: free local procedural artwork · no image model or API key used")
    if st.session_state.bg_image is None:
        bg = draw_background((900,1125), color1, color2, visual_style, description, category)
    else:
        bg = st.session_state.bg_image
    settings = {
        "dimensions": dimensions, "accent": accent, "text_color": "#FFFFFF",
        "title_size": title_size, "title_y": title_y, "style": visual_style,
        "template": template, "seed": description, "font_family": font_family,
        "title_align": title_align, "tagline_align": tagline_align,
        "description_align": description_align, "tagline_y": tagline_y,
        "description_y": description_y, "tagline_size": tagline_size,
        "description_size": description_size, "title_color": title_color,
        "tagline_color": tagline_color, "description_color": description_color,
        "text_effect": text_effect,
    }
    try:
        poster = compose_poster(bg, st.session_state.copy_data, settings, st.session_state.logo_image, qr_value)
        st.session_state.last_poster = poster
        st.image(poster, use_container_width=True)
    except Exception as exc:
        st.error(f"Could not render the poster: {exc}")
        poster = None
    if poster is not None:
        buf = io.BytesIO(); poster.save(buf, format="PNG")
        filename = "event_poster_" + "_".join((st.session_state.copy_data.get("title", "poster").lower().split()))[:45] + ".png"
        dload1, dload2 = st.columns(2)
        dload1.download_button("⬇️ Download PNG", data=buf.getvalue(), file_name=filename, mime="image/png", use_container_width=True)
        jpg_buf = io.BytesIO()
        poster.convert("RGB").save(jpg_buf, format="JPEG", quality=95, optimize=True)
        jpg_filename = filename.rsplit(".", 1)[0] + ".jpg"
        dload2.download_button("⬇️ Download JPG", data=jpg_buf.getvalue(), file_name=jpg_filename, mime="image/jpeg", use_container_width=True)
        st.caption(f"Export size: {dimensions[0]} × {dimensions[1]} px · PNG and JPG formats")

st.markdown("---")
metric1,metric2,metric3 = st.columns(3)
metric1.metric("Design workflow", "3 steps", "Brief → Edit → Export")
metric2.metric("Design templates", "10", "Multiple visual directions")
metric3.metric("Generation mode", "Local", "No API key or account required")
with st.expander("How generation works in this version"):
    st.write("This project is designed for free local use. Event-copy suggestions come from built-in templates, and backgrounds are drawn locally using gradients and decorative graphics. No API key, account, online image model, or paid credits are needed. The backgrounds are generated graphics, not diffusion-model AI images.")
