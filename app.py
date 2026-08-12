import os
import streamlit as st
from app.github_service import get_issues
from app.ai_service import generate_code

st.set_page_config(page_title='AI Code Generator', page_icon='🤖', layout='wide')

st.title('🤖 AI Code Generation System')
st.caption('Convert GitHub issues into AI-generated Python code using Amazon Bedrock.')

with st.sidebar:
    st.header('Configuration')
    repo = st.text_input('GitHub repository', value=os.getenv('GITHUB_REPO', 'owner/repository'))
    use_demo = st.toggle('Demo mode', value=True, help='Uses sample issues and local generation so the UI can be demonstrated without AWS credentials.')
    st.divider()
    st.info('Production flow: GitHub API → Python → Amazon Bedrock / Claude → generated code → S3')

if use_demo:
    issues = [
        {'number': 15, 'title': 'Create Fibonacci function', 'body': 'Create a Python function that returns the first n Fibonacci numbers.'},
        {'number': 16, 'title': 'Validate email address', 'body': 'Create a Python helper that validates an email address using a regular expression.'},
        {'number': 17, 'title': 'Calculate factorial', 'body': 'Create a Python function that calculates the factorial of a non-negative integer.'},
    ]
else:
    try:
        issues = get_issues(repo)
    except Exception as exc:
        st.error(f'Could not load GitHub issues: {exc}')
        st.stop()

st.subheader('Open GitHub Issues')
for issue in issues:
    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f'**#{issue["number"]} — {issue["title"]}**')
            st.write(issue.get('body') or 'No description provided.')
        with c2:
            if st.button('Generate', key=f'gen_{issue["number"]}', use_container_width=True):
                st.session_state['selected_issue'] = issue

selected = st.session_state.get('selected_issue')
if selected:
    st.divider()
    st.subheader(f'Generated Code for #{selected["number"]}')
    st.write(f'**Requirement:** {selected["title"]}')
    with st.spinner('Generating code with AI...'):
        try:
            code, source = generate_code(selected['title'], selected.get('body') or '', demo=use_demo)
            st.success(f'Generated using {source}')
            st.code(code, language='python')
            st.download_button('Download Python file', code, file_name=f'issue_{selected["number"]}.py', mime='text/x-python')
        except Exception as exc:
            st.error(f'Generation failed: {exc}')
