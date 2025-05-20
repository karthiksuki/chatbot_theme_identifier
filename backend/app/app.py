import streamlit as st
import requests
import os
import json
import pandas as pd
from io import BytesIO
import base64
from dotenv import load_dotenv
import time
from PIL import Image
import matplotlib.pyplot as plt
import networkx as nx
from streamlit_lottie import st_lottie
import requests

# Load environment variables
load_dotenv()

# Constants
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
UPLOAD_ENDPOINT = f"{API_BASE_URL}/upload"
QUERY_ENDPOINT = f"{API_BASE_URL}/api/query"
THEMES_ENDPOINT = f"{API_BASE_URL}/themes"
ANALYZE_ENDPOINT = f"{API_BASE_URL}/analyze"

# Initialize session states
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'current_themes' not in st.session_state:
    st.session_state.current_themes = {}
if 'document_filter' not in st.session_state:
    st.session_state.document_filter = []

# App layout configuration
st.set_page_config(
    page_title="Document Research & Theme Bot",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': 'https://www.example.com/bug',
        'About': 'Document Research & Theme Bot'
    }
)

# Set theme to dark mode
st.markdown("""
    <script>
        var elements = window.parent.document.querySelectorAll('.stApp');
        elements[0].classList.add('dark');
    </script>
    """, unsafe_allow_html=True)

# Custom CSS for styling with dark theme
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .st-emotion-cache-18ni7ap {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #263145;
        border-left: 5px solid #4c8bf5;
    }
    .chat-message.assistant {
        background-color: #1e2936;
        border-left: 5px solid #28a745;
    }
    .chat-message .message-content {
        margin-left: 10px;
    }
    .citation {
        font-size: 0.8em;
        color: #a3a8b8;
        margin-top: 5px;
    }
    .theme-card {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        margin-bottom: 15px;
    }
    .theme-title {
        font-weight: bold;
        color: #e0e0e0;
        margin-bottom: 10px;
    }
    .theme-docs {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
    }
    .doc-chip {
        background-color: #203040;
        padding: 2px 8px;
        border-radius: 15px;
        font-size: 0.8em;
        color: #4caf9e;
    }
    .file-upload-area {
        border: 2px dashed #444;
        padding: 30px;
        text-align: center;
        border-radius: 10px;
        background-color: #1a1d24;
        cursor: pointer;
        transition: all 0.3s;
    }
    .file-upload-area:hover {
        border-color: #4c8bf5;
        background-color: #182035;
    }
    .doc-table {
        margin-top: 20px;
    }
    .custom-tab {
        border-bottom: 2px solid transparent;
    }
    .custom-tab.selected {
        border-bottom: 2px solid #4c8bf5;
        font-weight: bold;
    }
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #333;
        margin-bottom: 20px;
    }
    .logo-title {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .btn-primary {
        background-color: #4c8bf5;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 5px;
        cursor: pointer;
    }
    .btn-primary:hover {
        background-color: #3a70d0;
    }
    /* Adjust dataframe styling for dark mode */
    div[data-testid="stDataFrame"] table {
        background-color: #1e2130;
        color: #e0e0e0;
    }
    div[data-testid="stDataFrame"] th {
        background-color: #273046;
        color: #ffffff;
    }
    div[data-testid="stDataFrame"] td {
        background-color: #1e2130;
        color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)


# Helper Functions
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


def create_citation_network(themes):
    """Create a network graph of themes and documents"""
    G = nx.Graph()

    # Check if themes is a dictionary
    if not isinstance(themes, dict):
        st.error("Expected themes to be a dictionary but got a different type")
        return G

    # Add theme nodes
    for theme_name, theme_data in themes.items():
        G.add_node(theme_name, kind='theme')

        # Add doc nodes and connections
        # Handle both string and dictionary values
        if isinstance(theme_data, dict):
            docs = theme_data.get('docs', [])
        elif isinstance(theme_data, str):
            # If theme_data is a string, we can't get docs from it
            continue
        else:
            # Try to handle lists or other types
            docs = []
            try:
                if hasattr(theme_data, '__iter__') and not isinstance(theme_data, str):
                    docs = list(theme_data)
            except:
                continue

        for doc in docs:
            if not G.has_node(doc):
                G.add_node(doc, kind='document')
            G.add_edge(theme_name, doc)

    return G


def plot_citation_network(themes):
    """Plot the citation network using matplotlib"""
    if not themes:
        return None

    # Add error handling when creating network
    try:
        G = create_citation_network(themes)

        # Check if we have nodes
        if G.number_of_nodes() == 0:
            st.warning("No nodes available to create visualization. Check theme data format.")
            return None

        # Create positions
        pos = nx.spring_layout(G, k=0.5)

        # Create the figure with dark background
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')

        # Identify node types
        theme_nodes = [node for node, attr in G.nodes(data=True) if attr.get('kind') == 'theme']
        doc_nodes = [node for node, attr in G.nodes(data=True) if attr.get('kind') == 'document']

        # Draw nodes with vibrant colors for dark theme
        if theme_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=theme_nodes, node_color='#4c8bf5', node_size=800, alpha=0.8)
        if doc_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=doc_nodes, node_color='#28a745', node_size=500, alpha=0.8)

        # Draw edges
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, edge_color='#999')

        # Draw labels with white text
        theme_labels = {node: node for node in theme_nodes}
        doc_labels = {node: node for node in doc_nodes}

        nx.draw_networkx_labels(G, pos, labels=theme_labels, font_size=12, font_color='white')
        nx.draw_networkx_labels(G, pos, labels=doc_labels, font_size=10, font_color='white')

        plt.axis('off')
        plt.tight_layout()

        return fig
    except Exception as e:
        st.error(f"Error creating citation network visualization: {str(e)}")
        return None


def upload_files(files):
    """Upload files to the API server"""
    file_objects = [('files', (file.name, file.getvalue(), file.type)) for file in files]
    try:
        response = requests.post(UPLOAD_ENDPOINT, files=file_objects)
        return response.json()
    except Exception as e:
        st.error(f"Error uploading files: {str(e)}")
        return None


def analyze_document(file):
    """Analyze a single document for themes"""
    try:
        files = {'file': (file.name, file.getvalue(), file.type)}
        response = requests.post(ANALYZE_ENDPOINT, files=files)
        return response.json()
    except Exception as e:
        st.error(f"Error analyzing document: {str(e)}")
        return None


def query_documents(query_text, top_k=5):
    """Query the document database"""
    try:
        response = requests.post(
            QUERY_ENDPOINT,
            json={"q": query_text, "top_k": top_k}
        )
        return response.json()
    except Exception as e:
        st.error(f"Error querying documents: {str(e)}")
        return None


def get_themes(query=None, top_k=100):
    """Get themes from the document database"""
    try:
        response = requests.post(
            THEMES_ENDPOINT,
            json={"query": query, "top_k": top_k}
        )
        result = response.json()

        # Validate result is a dictionary
        if not isinstance(result, dict):
            st.warning(f"Unexpected theme data format: got {type(result).__name__} instead of dict")
            # Try to convert to dict if it's a list of items
            if isinstance(result, list):
                converted = {}
                for i, item in enumerate(result):
                    if isinstance(item, dict) and 'name' in item:
                        converted[item['name']] = item
                    else:
                        converted[f"Theme {i + 1}"] = item
                return converted

        return result
    except Exception as e:
        st.error(f"Error getting themes: {str(e)}")
        return {}


def format_answer_with_citations(answer, citations):
    """Format answer text with citation highlights"""
    if not citations:
        return answer

    formatted_answer = answer
    citation_text = "\n\n**Citations:**\n"

    for doc_id, refs in citations.items():
        citation_text += f"- **{doc_id}**: {', '.join(refs)}\n"

    return formatted_answer + citation_text


# Header with Logo
def render_header():
    st.markdown("""
    <div class="header-container">
        <div class="logo-title">
            <h1>Document Research & Theme Bot</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Main Application
def main():
    render_header()

    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "Upload Documents",
        "Chat & Query",
        "Theme Analysis",
        "Visualization"
    ])

    # Tab 1: Document Upload
    with tab1:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### Upload Your Documents")

            uploaded_files = st.file_uploader(
                "Choose PDF, DOCX, TXT, or image files",
                accept_multiple_files=True,
                type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "tiff"],
                label_visibility="collapsed"
            )

            if uploaded_files:
                if st.button("Process Documents", type="primary"):
                    with st.spinner("Processing your documents..."):
                        result = upload_files(uploaded_files)
                        if result:
                            st.success(f"Successfully processed {result.get('message', '')}")
                            # Add to session state
                            for file in uploaded_files:
                                if file.name not in [f["name"] for f in st.session_state.uploaded_files]:
                                    st.session_state.uploaded_files.append({
                                        "name": file.name,
                                        "size": file.size,
                                        "type": file.type
                                    })
                            # Update themes
                            themes = get_themes()
                            if themes and not isinstance(themes, dict) or "error" not in themes:
                                st.session_state.current_themes = themes

        with col2:
            lottie_url = "https://assets5.lottiefiles.com/packages/lf20_qp1q7mct.json"
            lottie_json = load_lottie_url(lottie_url)
            if lottie_json:
                st_lottie(lottie_json, height=200, key="upload_animation")

        # Show uploaded files
        if st.session_state.uploaded_files:
            st.markdown("### Uploaded Documents")

            df = pd.DataFrame(st.session_state.uploaded_files)
            df['size'] = df['size'].apply(lambda x: f"{x / 1024:.1f} KB")

            st.dataframe(
                df,
                column_config={
                    "name": "Document Name",
                    "size": "Size",
                    "type": "Format"
                },
                hide_index=True,
                use_container_width=True
            )

            if st.button("Clear Documents"):
                st.session_state.uploaded_files = []
                st.experimental_rerun()

    # Tab 2: Chat Interface
    with tab2:
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown("### Ask About Your Documents")

            # Query input
            query = st.text_input("Enter your question:", placeholder="What themes emerge from these documents?")

            col_btn1, col_btn2 = st.columns([1, 5])
            with col_btn1:
                send_btn = st.button("Send", type="primary", use_container_width=True)

            # Process query
            if send_btn and query:
                with st.spinner("Searching documents..."):
                    # Add user message to chat
                    st.session_state.chat_history.append({"role": "user", "content": query})

                    # Get response from API
                    response = query_documents(query)

                    if response:
                        # Format answer with citations
                        formatted_answer = format_answer_with_citations(
                            response.get("answer", "Sorry, I couldn't find an answer."),
                            response.get("citations", {})
                        )

                        # Add assistant response to chat
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": formatted_answer,
                            "citations": response.get("citations", {})
                        })

                        # Update themes based on this query
                        new_themes = get_themes(query=query)
                        if new_themes and not isinstance(new_themes, dict) or "error" not in new_themes:
                            st.session_state.current_themes = new_themes

            # Display chat history
            st.markdown("### Conversation")
            chat_container = st.container(height=500)

            with chat_container:
                for message in st.session_state.chat_history:
                    role = message["role"]
                    content = message["content"]

                    if role == "user":
                        st.markdown(f"""
                        <div class="chat-message user">
                            <div class="message-content">
                                <strong>You:</strong><br>
                                {content}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:  # assistant
                        st.markdown(f"""
                        <div class="chat-message assistant">
                            <div class="message-content">
                                <strong>Assistant:</strong><br>
                                {content}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            if st.button("Clear Conversation"):
                st.session_state.chat_history = []
                st.experimental_rerun()

        # Document filters sidebar
        with col2:
            st.markdown("### Document Filters")

            if st.session_state.uploaded_files:
                all_docs = [doc["name"] for doc in st.session_state.uploaded_files]
                selected_docs = st.multiselect(
                    "Select documents to query",
                    options=all_docs,
                    default=all_docs
                )

                st.session_state.document_filter = selected_docs

                # Show filter info
                if len(selected_docs) != len(all_docs):
                    st.info(f"Querying {len(selected_docs)} of {len(all_docs)} documents")
                else:
                    st.info("Querying all documents")

    # Tab 3: Theme Analysis
    with tab3:
        st.markdown("### Document Themes")

        # Theme search/filter
        theme_query = st.text_input("Search for specific themes:", placeholder="Type to find specific themes...")

        if st.button("Analyze Themes", type="primary"):
            with st.spinner("Analyzing themes across documents..."):
                # Get themes based on filter if provided
                themes = get_themes(query=theme_query if theme_query else None)
                if themes:  # Just check if it exists, not the type
                    st.session_state.current_themes = themes

        # Display themes
        if st.session_state.current_themes:
            themes = st.session_state.current_themes

            # Filter themes if search term provided
            if theme_query and isinstance(themes, dict):
                themes = {
                    theme: data for theme, data in themes.items()
                    if theme_query.lower() in theme.lower()
                }

            if isinstance(themes, dict):
                for theme_name, theme_data in themes.items():
                    # Extract summary and docs safely
                    if isinstance(theme_data, dict):
                        summary = theme_data.get('summary', 'No summary available')
                        docs = theme_data.get('docs', [])
                    else:
                        summary = str(theme_data) if theme_data else 'No summary available'
                        docs = []

                    st.markdown(f"""
                    <div class="theme-card">
                        <div class="theme-title">{theme_name}</div>
                        <p>{summary}</p>
                        <div class="theme-docs">
                            {"".join([f'<span class="doc-chip">{doc}</span>' for doc in docs])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info(
                    "No themes identified yet or theme data in unexpected format. Upload documents and ask questions to generate themes.")
        else:
            st.info("No themes identified yet. Upload documents and ask questions to generate themes.")

    # Tab 4: Visualization
    with tab4:
        st.markdown("### Citation Network")

        if st.session_state.current_themes:
            themes = st.session_state.current_themes

            if isinstance(themes, dict) and len(themes) > 0:
                fig = plot_citation_network(themes)
                if fig:
                    st.pyplot(fig)

                    # Legend
                    st.markdown("""
                    **Legend:**
                    - 🔵 Theme nodes
                    - 🟢 Document nodes
                    - Lines represent citations/references
                    """)
                else:
                    st.info("Could not create visualization. Check theme data format.")
            else:
                st.info("No visualization available. Theme data is not in expected format.")
        else:
            st.info("No visualization available. Upload documents and analyze themes first.")

        # Additional visualizations could go here


# Run the app
if __name__ == "__main__":
    main()