import os
import math
import pandas as pd
import json, io
import streamlit as st
from supabase import create_client, Client
from datetime import date
from pathlib import Path
import time

# =========================
# Config
# =========================
PARENT_TABLE = "Projekt_Data" 

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ugfsmunvwyddfkuvlxye.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnZnNtdW52d3lkZGZrdXZseHllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIxMzg3OTUsImV4cCI6MjA2NzcxNDc5NX0.FOMjr4gebKrxJ_zq_fgmSXA4cu4aefdKN0QUlxv_Ruo") 

EXCEL_PATH = Path(__file__).parent / "tracking_questions.xlsx"
WS_SHEETS = {1: "WS1", 2: "WS2", 3: "WS3", 4: "WS4", 5: "WS5"}

# =========================
# Supabase client
# =========================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
@st.cache_data

# Add this helper function near the top with your other utility functions
def parse_tracking_data(raw_data: list, workstream: str) -> pd.DataFrame:
    if not raw_data:
        return pd.DataFrame()
    
    parsed_records = []
    
    for record in raw_data:
        # Start with base fields
        flat_record = {
            'idx': record.get('idx'),
            'id': record.get('id'),
            'project_id': record.get('project_id'),
            'submitted_at': record.get('submitted_at'),
            'user_id': record.get('user_id'),
            'Form_title': record.get('Form_title', ''),
            'Workstream': record.get('Workstream', workstream)
        }
        
        # Parse the answers JSON
        answers = record.get('answers', {})
        if isinstance(answers, str):
            try:
                answers = json.loads(answers)
            except json.JSONDecodeError:
                answers = {}
        
        # Add all answer fields as separate columns
        if isinstance(answers, dict):
            for key, value in answers.items():
                flat_record[key] = value
        
        parsed_records.append(flat_record)
    
    return pd.DataFrame(parsed_records)

def download_tracking_data(workstream_num: int) -> pd.DataFrame:
    table_name = f"Tracking_WS{workstream_num}"
    ws_label = f"WS{workstream_num}"
    
    try:
        resp = supabase.table(table_name).select("*").order("submitted_at", desc=True).execute()
        raw_data = resp.data or []
        return parse_tracking_data(raw_data, ws_label)
    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {e}")
        return pd.DataFrame()

def create_excel_download(dataframes: dict) -> io.BytesIO:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in dataframes.items():
            if not df.empty:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    return output

def key_factory(prefix: str, project_id: str):
    return lambda label: f"{prefix}:{project_id}:{label}"

def load_questions(sheet_name: str) -> pd.DataFrame:
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Excel file not found at {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
    df.columns = [str(c).strip() for c in df.columns]
    # Ensure all expected columns exist
    cols = [
        "question_id","section","label","input_type","options","help_text",
        "required","condition_field","condition_value",
        "min_value","max_value","step",
        "required_if_field","required_if_value"
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df = df.fillna("")
    df["required"] = df["required"].astype(str).str.strip().str.upper().eq("TRUE")
    return df


    if val is None: return True
    if isinstance(val, str): return val.strip() == ""
    if isinstance(val, list): return len(val) == 0
    return False

def render_dynamic_form_reactive(sheet_name: str, key_prefix: str, header_html: str = None, excel_path: Path = None):
    excel_path = excel_path or EXCEL_PATH
    dfq = load_questions(sheet_name)  # reuse your cached loader
    if header_html:
        st.markdown(header_html, unsafe_allow_html=True)

    # Helpers from your existing utilities
    def _is_visible(row, answers):
        cond_f = str(row.get("condition_field","")).strip()
        cond_v = str(row.get("condition_value","")).strip()
        if not cond_f:
            return True
        return str(answers.get(cond_f, "")) == cond_v

    def _is_required_now(row, answers):
        if bool(row.get("required", False)):
            return True
        rif = str(row.get("required_if_field","")).strip()
        riv = str(row.get("required_if_value","")).strip()
        if rif:
            return str(answers.get(rif, "")) == riv
        return False

    def _is_empty(val):
        if val is None: return True
        if isinstance(val, str): return val.strip() == ""
        if isinstance(val, list): return len(val) == 0
        return False

    def _parse_float(x):
        try: return float(x)
        except: return None

    def _parse_int(x):
        try: return int(float(x))
        except: return None

    def render_widget(row, key):
        itype   = str(row["input_type"]).strip().lower()
        label   = str(row["label"]).strip()
        help_t  = (str(row["help_text"]).strip() or None)
        options = [o.strip() for o in str(row["options"]).split("|")] if row["options"] else []

        if itype == "selectbox":
            return st.selectbox(label, options, help=help_t, key=key)
        if itype == "radio":
            return st.radio(label, options, help=help_t, horizontal=True, key=key)
        if itype == "multiselect":
            return st.multiselect(label, options, help=help_t, key=key)
        if itype == "text_input":
            return st.text_input(label, help=help_t, key=key)
        if itype == "text_area":
            return st.text_area(label, help=help_t, key=key)
        if itype == "checkbox":
            # initialize default
            if key not in st.session_state:
                st.session_state[key] = False
            return st.checkbox(label, help=help_t, key=key)
        if itype == "number":
            vmin = _parse_int(row.get("min_value",""))
            vmax = _parse_int(row.get("max_value",""))
            vstep = _parse_int(row.get("step","")) or 1
            kwargs = {"step": vstep, "key": key, "help": help_t}
            if vmin is not None: kwargs["min_value"] = vmin
            if vmax is not None: kwargs["max_value"] = vmax
            return st.number_input(label, **kwargs)
        if itype == "number_float":
            vmin = _parse_float(row.get("min_value",""))
            vmax = _parse_float(row.get("max_value",""))
            try:
                vstep = float(row.get("step","")) if str(row.get("step","")) not in ("", "None") else 0.1
            except:
                vstep = 0.1
            kwargs = {"step": vstep, "key": key, "help": help_t}
            if vmin is not None: kwargs["min_value"] = vmin
            if vmax is not None: kwargs["max_value"] = vmax
            return st.number_input(label, **kwargs)
        if itype == "date":
            return st.date_input(label, help=help_t, key=key)

        st.caption(f"Unknown input_type '{itype}' for {row['question_id']} – skipped.")
        return None

    # Multi-pass reactive rendering to support chains of dependencies
    answers = {}
    rendered = set()
    current_section = None

    changed = True
    passes = 0
    while changed and passes < 6:
        changed = False
        passes += 1

        for _, row in dfq.iterrows():
            qid = str(row["question_id"]).strip()
            section = str(row.get("section","")).strip()

            if qid in rendered:
                continue

            if not _is_visible(row, answers):
                continue

            if section and section != current_section:
                st.markdown(f"## {section}")
                current_section = section

            key = f"{key_prefix}:{qid}"
            val = render_widget(row, key)
            answers[qid] = val
            rendered.add(qid)
            changed = True

    save = st.button("Save entry ✅")

    if not save:
        return False, None

    # Validate required fields that are visible
    errors = []
    for _, row in dfq.iterrows():
        qid = str(row["question_id"]).strip()
        if not _is_visible(row, answers):
            continue
        if _is_required_now(row, answers) and _is_empty(answers.get(qid)):
            errors.append(str(row["label"]).strip())

    if errors:
        st.error("Please fill in the required fields:\n" + "\n".join(f"- {e}" for e in errors))
        return False, None

    # Build payload from currently visible answers
    payload = {}
    for _, row in dfq.iterrows():
        qid = str(row["question_id"]).strip()
        if not _is_visible(row, answers):
            continue
        val = answers.get(qid)
        if isinstance(val, list):
            payload[qid] = ", ".join(map(str, val)) if val else None
        elif isinstance(val, str):
            payload[qid] = val.strip() or None
        else:
            payload[qid] = val

    return True, payload

def load_form_header(sheet_name: str, excel_path: Path = EXCEL_PATH) -> str | None:
    try:
        dfh = pd.read_excel(excel_path, sheet_name="Titles")
        dfh.columns = [str(c).strip().lower() for c in dfh.columns]
        row = dfh.loc[dfh["sheet"].astype(str).str.strip() == sheet_name]
        if not row.empty:
            title = str(row.iloc[0].get("title", "")).strip()
            subtitle = str(row.iloc[0].get("subtitle", "")).strip()
            if title or subtitle:
                t = f"<h1 style='text-align:center;'>{title}</h1>" if title else ""
                s = f"<h5 style='text-align:center;'>{subtitle}</h5>" if subtitle else ""
                return t + s
    except Exception:
        pass
    # Fallback: brug første række i spørgeskemaet med input_type == 'header' (hvis du vil støtte det)
    try:
        dfq = load_questions(sheet_name)
        if "input_type" in dfq.columns:
            hdr = dfq[dfq["input_type"].astype(str).str.lower().eq("header")]
            if not hdr.empty:
                title = str(hdr.iloc[0].get("label","")).strip()
                subtitle = str(hdr.iloc[0].get("help_text","")).strip()
                t = f"<h1 style='text-align:center;'>{title}</h1>" if title else ""
                s = f"<h5 style='text-align:center;'>{subtitle}</h5>" if subtitle else ""
                return t + s if (t or s) else None
    except Exception:
        pass
    return None


    sheet = WS_SHEETS[5]
    header = load_form_header(sheet)
    submitted, payload = render_dynamic_form_reactive(
        sheet_name=sheet,
        key_prefix=f"ws5:{selected_project_id}",
        header_html=header
    )
    if submitted and payload:
        try:
            row = {
                "project_id": str(selected_project_id),
                "submitted_at": pd.Timestamp.now().isoformat(), 
                "Workstream": WS_SHEETS[5],
                "answers": payload,
            }
            ins = supabase.table(table_name).insert(row).execute()
            if ins.data is not None:
                st.success("Tracking entry added, your answers have been saved and you can now close the page ✅")
                time.sleep(10)
                st.rerun()
            else:
                st.error("Insert returnerede ingen data.")
        except Exception as e:
            st.error(f"Kunne ikke indsætte tracking entry: {e}")
    return submitted, payload

def get_form_title(sheet_name: str, excel_path: Path = EXCEL_PATH) -> str:
    try:
        dfh = pd.read_excel(excel_path, sheet_name="Titles")
        dfh.columns = [str(c).strip().lower() for c in dfh.columns]
        row = dfh.loc[dfh["sheet"].astype(str).str.strip() == sheet_name]
        if not row.empty:
            title = str(row.iloc[0].get("title", "")).strip()
            if title:
                return title
    except Exception:
        pass
    
    # Fallback: try to get from question header
    try:
        dfq = load_questions(sheet_name)
        if "input_type" in dfq.columns:
            hdr = dfq[dfq["input_type"].astype(str).str.lower().eq("header")]
            if not hdr.empty:
                title = str(hdr.iloc[0].get("label", "")).strip()
                if title:
                    return title
    except Exception:
        pass
    
    return ""

def render_tracking_form(selected_project_id: str, workstream_num: int, table_name: str):
    sheet = WS_SHEETS[workstream_num]
    header = load_form_header(sheet)
    form_title = get_form_title(sheet)
    
    submitted, payload = render_dynamic_form_reactive(
        sheet_name=sheet,
        key_prefix=f"ws{workstream_num}:{selected_project_id}",
        header_html=header
    )
    if submitted and payload:
        try:
            row = {
                "project_id": str(selected_project_id),
                "Workstream": WS_SHEETS[workstream_num],
                "submitted_at": pd.Timestamp.now().isoformat(),
                "Form_title": form_title,
                "answers": payload,
            }
            ins = supabase.table(table_name).insert(row).execute()
            if ins.data is not None:
                st.success("Tracking entry added, your answers have been saved and you can now close the page ✅")
                time.sleep(10)
                st.rerun()
            else:
                st.error("Insert returnerede ingen data.")
        except Exception as e:
            st.error(f"Kunne ikke indsætte tracking entry: {e}")
    return submitted, payload

def current_user_is_admin() -> bool:
    try:
        u = supabase.auth.get_user()
        user = getattr(u, "user", None)
        meta = getattr(user, "app_metadata", {}) if user else {}
        is_sup = meta.get("is_super_admin")
        role = (meta.get("role") or "").lower()
        return (str(is_sup).lower() == "true") or (role == "admin")
    except Exception:
        return False

def hydrate_token_from_session():
    token = st.session_state.get("sb_token")
    refresh = st.session_state.get("sb_refresh")
    if token:
        try:
            supabase.postgrest.auth(token)
            supabase.auth.set_session(token, refresh or "")
        except Exception:
            pass
    # refresh admin flag on hydrate
    st.session_state["is_admin"] = st.session_state.get("is_admin", current_user_is_admin())

hydrate_token_from_session()

def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def do_login(email: str, password: str):
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if not res or not getattr(res, "session", None):
        raise RuntimeError("Login returned no session. Check credentials or email confirmation.")
    token = res.session.access_token
    refresh = res.session.refresh_token
    st.session_state["sb_token"] = token
    st.session_state["sb_refresh"] = refresh
    supabase.postgrest.auth(token)
    try:
        supabase.auth.set_session(token, refresh)
    except Exception:
        pass
    # set admin flag after login
    st.session_state["is_admin"] = current_user_is_admin()

def is_logged_in() -> bool:
    return bool(st.session_state.get("sb_token"))

def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.pop("sb_token", None)
    st.session_state.pop("sb_refresh", None)
    st.session_state.pop("is_admin", None)

st.set_page_config(page_title="CCUS Project Tracker", page_icon="🍃", layout="wide")

col1, col2 = st.columns([6, 1])
with col1:
    st.title("CCUS Project Tracker")
with col2:
    image = "INNO-CCUS-square-logo.png"
    st.image(image, width=400)

# =========================
# LOGIN
# =========================
if not is_logged_in():
    
    with st.form("login", clear_on_submit=False):
        st.subheader("Sign in")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        ok = st.form_submit_button("Sign in")
        st.markdown("If you have forgotten your login credentials contact antg@teknologisk.dk and you will receive an email with new credentials shortly")
        if ok:
            try:
                do_login(email, password)
                st.success("Signed in.")
                rerun()
            except Exception as e:
                st.error(f"Sign-in failed: {e}")
    st.stop()
    

IS_ADMIN = bool(st.session_state.get("is_admin"))

# --- Tabs (visualisations only for admins) ---
if IS_ADMIN:
    tab1, tab2, tab3 = st.tabs(["Your Projects", "Track your Project(s)", "Download data"])
else:
    tab1, tab2 = st.tabs(["Your Projects", "Track your Project(s)"])

with tab1:
    st.markdown("##### Switch to the tab 'Track your Project(s)' to add tracking entries ⬆️")
    st.markdown("---")
    try:
        resp = supabase.table(PARENT_TABLE).select("*").order("created_at", desc=True).execute()
        rows = resp.data or []
    except Exception as e:
        st.error(f"Could not load project data: {e}")
        rows = []

    if not rows:
        st.info("No projects assigned to your user.")
        st.markdown("---")
        if st.button("Sign out"):
            logout()
            st.query_params.clear()
            rerun()
        st.stop()

    # Convert to DataFrame; keep id for updates but HIDE it in the editor
    df = pd.DataFrame(rows)

    # Ensure 'id' exists and is unique to use as hidden index
    if "id" not in df.columns:
        st.error("Expected 'id' column not found in table.")
        st.stop()

    # Use 'id' as index for diff/update, but hide it in the UI
    df = df.set_index("id", drop=True)

    cols_hide = ["owner_id", "id", "created_at"]
    cols_display = [c for c in df.columns if c.lower() not in [x.lower() for x in cols_hide]]

    st.header("Your projects")
    edited = st.dataframe(
        df[cols_display],
        width="stretch",
        hide_index=True,
    )


with tab2:
    st.markdown("### Select project for reporting below ⬇️")

    # Forudsætning: df indeholder dine projekter og har index = projekt_id (uuid)
    # Hvis ikke, så hent dem her:
    if 'df' not in locals() or df is None or df.empty:
        try:
            proj = supabase.table("Projekt_Data").select("*").execute().data or []
            df = pd.DataFrame(proj)
            if "id" in df.columns:
                df = df.set_index("id")
        except Exception as e:
            st.error(f"Kunne ikke hente projekter: {e}")
            st.stop()

    # Simpel selector
    if df.empty:
        st.info("Ingen projekter fundet.")
        st.stop()

    # Vælg visningskolonne til label i selectbox (brug det du har)
    label_col = next((c for c in ["Projektakronym","Titel"] if c in df.columns), None)
    proj_options = df.index.tolist()
    proj_labels = [df.at[i,label_col] if label_col else str(i) for i in proj_options]
    selected_project_id = st.selectbox("select", proj_options, format_func=lambda x: proj_labels[proj_options.index(x)])


    # Find projektets workstream (kræver kolonne "Workstream")
    selected_row = df.loc[selected_project_id] if selected_project_id in df.index else None
    workstream = int(selected_row.get("Workstream")) if (selected_row is not None and pd.notna(selected_row.get("Workstream"))) else None
    st.markdown("---")

    # Map WS -> tabelnavn og form-funktion
    ws_map = {
        1: "Tracking_WS1",
        2: "Tracking_WS2",
        3: "Tracking_WS3",
        4: "Tracking_WS4",
        5: "Tracking_WS5",
    }

    table_name = ws_map[workstream]
    add, payload = render_tracking_form(str(selected_project_id), workstream, table_name)

# =========================
# Tab 3: Visualisations (ADMIN ONLY) — projekt status
# =========================
if IS_ADMIN:
    with tab3:
        st.header("📥 Download Tracking Data")
        st.markdown("---")
        
        # Create a row for each workstream
        for ws_num in range(1, 6):
            col1, col2, col3 = st.columns([4, 4, 4])
            with col1:
                st.markdown(f"### WS{ws_num}")
            
            with col2:
                # Show record count
                try:
                    table_name = f"Tracking_WS{ws_num}"
                    resp = supabase.table(table_name).select("id", count="exact").execute()
                    count = resp.count if hasattr(resp, 'count') else 0
                    st.markdown(f"**{count}** records")
                except Exception:
                    st.markdown("**-** records")
            
            with col3:
                # Load data once on page load (cached for performance)
                df_download = download_tracking_data(ws_num)
                
                if df_download.empty:
                    st.button(f"📊 No data available", disabled=True, key=f"disabled_ws{ws_num}")
                else:
                    excel_data = create_excel_download({f"WS{ws_num}": df_download})
                    st.download_button(
                        label=f"📊 Download data in excel",
                        data=excel_data,
                        file_name=f"WS{ws_num}_tracking_{date.today().isoformat()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_ws{ws_num}"
                    )
            st.markdown("---")

# =========================
# Sign out
# =========================
st.markdown("---")
if st.button("Sign out 👋"):
    logout()
    st.query_params.clear()
    rerun()
