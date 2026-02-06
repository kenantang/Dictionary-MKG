import streamlit as st
import pandas as pd
import re
import sys
import os

# Configure page settings
st.set_page_config(page_title="Dictionary", layout="centered")

json_file_path = "ko_dict_in_ko_ja_es.json"

if not os.path.exists(json_file_path):
    st.error(f"Error: File not found at {json_file_path}")
    st.stop()

# Custom CSS for styling
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7f9;
    }
    
    .dict-card {
        background-color: white;
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #e1e4e8;
        font-family: "Helvetica Neue", Helvetica, Arial, 
                     "Hiragino Kaku Gothic ProN", "Hiragino Sans", "Meiryo", 
                     "Malgun Gothic", "Apple SD Gothic Neo", 
                     sans-serif;
        line-height: 1.6;
        color: #333;
        margin-top: 20px;
        margin-bottom: 20px;
    }

    .dict-card h3 {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
        margin-bottom: 20px;
        font-size: 1.5em;
        font-weight: bold;
    }

    strong {
        color: #2980b9;
    }
    
    div.stButton > button {
        width: 100%;
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        color: #374151;
        border-radius: 8px;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        border-color: #3498db;
        color: #3498db;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(filepath):
    """Loads and sorts the JSON data."""
    try:
        df = pd.read_json(filepath)
        
        if 'day_index' not in df.columns:
            df['day_index'] = 1
        
        # Sort by day_index using a stable sort
        df = df.sort_values(by=['day_index'], kind='mergesort').reset_index(drop=True)
        return df
    except ValueError as e:
        st.error(f"Error reading JSON file: {e}")
        st.stop()

df = load_data(json_file_path)
unique_days = sorted(df['day_index'].unique())

# Initialize session state
if 'index' not in st.session_state:
    st.session_state.index = 0

def get_current_nav_values():
    """Helper to calculate Day and Word Num based on the current global index."""
    current_idx = st.session_state.index
    current_row = df.iloc[current_idx]
    
    day_val = current_row['day_index']
    
    # Find where this index sits relative to its day group
    day_indices = df[df['day_index'] == day_val].index.tolist()
    
    if current_idx in day_indices:
        word_num = day_indices.index(current_idx) + 1 
    else:
        word_num = 1
        
    return day_val, word_num

def sync_widgets():
    """Updates the widget keys in session_state to match the current index."""
    day_val, word_num = get_current_nav_values()
    st.session_state['nav_day_select'] = day_val
    st.session_state['nav_word_num'] = word_num

if 'nav_day_select' not in st.session_state:
    sync_widgets()

def go_prev():
    """Go to previous word, or wrap around to the last word if at the start."""
    if st.session_state.index > 0:
        st.session_state.index -= 1
    else:
        st.session_state.index = len(df) - 1
    sync_widgets()

def go_next():
    """Go to next word, or wrap around to the first word if at the end."""
    if st.session_state.index < len(df) - 1:
        st.session_state.index += 1
    else:
        st.session_state.index = 0
    sync_widgets()

def on_day_change():
    """Callback: User changed the Day dropdown."""
    selected_day = st.session_state.nav_day_select
    matching_indices = df[df['day_index'] == selected_day].index
    if not matching_indices.empty:
        st.session_state.index = int(matching_indices[0])
        st.session_state.nav_word_num = 1

def on_word_num_change():
    """Callback: User changed the Word Number input."""
    current_day = st.session_state.nav_day_select
    day_indices = df[df['day_index'] == current_day].index.tolist()
    desired_num = st.session_state.nav_word_num
    
    if day_indices:
        safe_num = max(1, min(desired_num, len(day_indices)))
        new_global_index = day_indices[safe_num - 1]
        st.session_state.index = new_global_index

# --- Main Layout ---

col1 = st.columns(1)[0]
with col1:
    st.button("← Prev", on_click=go_prev, use_container_width=True)

# Display content
current_row = df.iloc[st.session_state.index]
content = current_row['responses']

# Convert Markdown headers (###) to HTML (<h3>)
content_html = re.sub(r'^###\s+(.*)', r'<h3>\1</h3>', content, flags=re.MULTILINE)

st.markdown(f"""
<div class="dict-card">
{content_html}
</div>
""", unsafe_allow_html=True)

col2 = st.columns(1)[0]
with col2:
    st.button("Next →", on_click=go_next, use_container_width=True)

# Navigation Controls
cur_day, cur_num = get_current_nav_values()
total_in_day = len(df[df['day_index'] == cur_day])

b_col1, b_col2 = st.columns([1, 1])

with b_col1:
    st.selectbox(
        "Select Day",
        options=unique_days,
        key="nav_day_select",
        on_change=on_day_change
    )

with b_col2:
    st.number_input(
        f"Select Word (Total {total_in_day})",
        min_value=1,
        max_value=total_in_day,
        step=1,
        key="nav_word_num",
        on_change=on_word_num_change
    )