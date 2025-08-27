# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from data_ingester import DataIngester
from review_analyzer import ReviewAnalyzer
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

st.sidebar.image('customer-review-4396641_1280.png')

# Page configuration
st.set_page_config(
    page_title="AI-Powered Review Insights",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2rem; color: #1f77b4; margin-bottom: 1rem;}
    .positive {color: green; font-weight: bold;}
    .negative {color: red; font-weight: bold;}
    .neutral {color: orange; font-weight: bold;}
    .metric-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 color: white; padding: 15px; border-radius: 10px; margin: 5px;}
</style>
""", unsafe_allow_html=True)

class ReviewDashboard:
    def __init__(self):
        self.ingester = DataIngester()
        self.analyzer = ReviewAnalyzer()
    
    def render_upload_section(self):
        """File upload + JSON paste"""
        st.sidebar.title("Upload or Paste Reviews")
        
        uploaded_file = st.sidebar.file_uploader(
            "Choose review file",
            type=['json', 'csv'],
            help="Upload JSON or CSV file with customer reviews"
        )

        st.sidebar.markdown("---")
        st.sidebar.write("Or paste raw JSON data:")
        pasted_json = st.sidebar.text_area("Paste JSON here", height=150)
        
        return uploaded_file, pasted_json
    
    def process_input(self, uploaded_file, pasted_json):
        """Process uploaded file or pasted JSON"""
        if uploaded_file:
            raw_reviews = self.ingester.ingest_file(uploaded_file)
        elif pasted_json.strip():
            raw_reviews = self.ingester.ingest_file(io.StringIO(pasted_json))
        else:
            return None
        
        if not raw_reviews:
            st.error("No valid reviews found.")
            return None
        
        with st.spinner("Analyzing reviews..."):
            df = self.analyzer.analyze_batch(raw_reviews)
            return df
    
    def create_dashboard(self, df):
        """Main dashboard layout"""
        st.title("AI-Powered Customer Review Insights")
        
        # Key metrics
        self.render_metrics(df)
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Overview", "Sentiment Analysis", "Topics & Problems",
            "Review Browser", "Export Data"
        ])
        
        with tab1:
            self.render_overview(df)
        with tab2:
            self.render_sentiment_analysis(df)
        with tab3:
            self.render_topics_problems(df)
        with tab4:
            self.render_review_browser(df)
        with tab5:
            self.render_export(df)
    
    def render_metrics(self, df):
        """Display key metrics"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Reviews", len(df))
        with col2:
            positive = len(df[df['sentiment'] == 'positive'])
            st.metric("Positive", positive)
        with col3:
            negative = len(df[df['sentiment'] == 'negative'])
            st.metric("Negative", negative)
        with col4:
            neutral = len(df[df['sentiment'] == 'neutral'])
            st.metric("Neutral", neutral)
        with col5:
            avg_rating = df['rating_num'].dropna().mean()
            st.metric("Avg Rating", f"{avg_rating:.1f}/5" if not pd.isna(avg_rating) else "N/A")
    
    def render_overview(self, df):
        """Overview tab with charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            sentiment_counts = df['sentiment'].value_counts()
            fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index,
                         title="Sentiment Distribution", hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.histogram(df, x='rating_num', nbins=5,
                               title="Rating Distribution", labels={'rating_num': 'Rating'})
            fig.update_xaxes(dtick=1)
            st.plotly_chart(fig, use_container_width=True)
    
    def render_sentiment_analysis(self, df):
        """Sentiment analysis details"""
        st.subheader("Sentiment Analysis")
        
        sentiment_filter = st.selectbox("Filter by Sentiment", ["All", "Positive", "Negative", "Neutral"])
        rating_filter = st.slider("Minimum Rating", 1, 5, 1)
        
        filtered_df = df[df['rating_num'].fillna(1) >= rating_filter]
        if sentiment_filter != "All":
            filtered_df = filtered_df[filtered_df['sentiment'] == sentiment_filter.lower()]
        
        for _, row in filtered_df.iterrows():
            with st.expander(f"{row['review_id']} - {row.get('date', 'No date')} - Rating: {row['rating_num']}/5"):
                self.render_review_detail(row)
    
    def render_topics_problems(self, df):
        """Topics, Problems (with charts) + Suggestions (list)"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Most Discussed Topics")
            all_topics = []
            for topics in df['topics']:
                all_topics.extend(topics)
            if all_topics:
                topic_counts = pd.Series(all_topics).value_counts().head(10)
                fig = px.bar(
                    x=topic_counts.values,
                    y=topic_counts.index,
                    orientation='h',
                    text=topic_counts.values,
                    title="Top Topics"
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No topics extracted.")
        
        with col2:
            st.subheader("Top Problems Identified")
            all_problems = []
            for problems in df['problems']:
                all_problems.extend(problems)
            if all_problems:
                problem_counts = pd.Series(all_problems).value_counts().head(10)
                fig = px.bar(
                    x=problem_counts.values,
                    y=problem_counts.index,
                    orientation='h',
                    text=problem_counts.values,
                    title="Top Problems"
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No problems detected.")
        
        st.subheader("Customer Suggestions")
        all_suggestions = []
        for suggestions in df['suggestions']:
            all_suggestions.extend(suggestions)
        if all_suggestions:
            for i, suggestion in enumerate(set(all_suggestions), 1):
                st.write(f"{i}. {suggestion}")
        else:
            st.info("No suggestions found.")

    
    def render_review_browser(self, df):
        """Review browser tab"""
        st.subheader("Review Browser")
        search_term = st.text_input("Search reviews")
        
        if search_term:
            filtered_df = df[df['text'].str.contains(search_term, case=False, na=False)]
        else:
            filtered_df = df
        
        for _, row in filtered_df.iterrows():
            with st.expander(f"Review {row['review_id']} - Rating: {row['rating_num']}/5"):
                self.render_review_detail(row)
    
    def render_review_detail(self, row):
        """Render individual review details"""
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Date:** {row.get('date', 'N/A')}")
            st.write(f"**Rating:** {row.get('rating_text', 'N/A')} ({row['rating_num']}/5)")
            st.write(f"**Sentiment:** <span class='{row['sentiment']}'>{row['sentiment'].upper()}</span>",
                     unsafe_allow_html=True)
        with col2:
            st.write(f"**Words:** {row['word_count']} ({row['length_category']})")
            st.write(f"**Characters:** {row['char_count']}")
            st.write(f"**Has Rating:** {'Yes' if row['has_rating'] else 'No'}")
        
        st.write("**Review Text:**")
        st.write(row['text'])
        
        if row['topics']:
            st.write("**Topics Mentioned:**")
            st.write(", ".join(row['topics']))
        
        if row['problems']:
            st.write("**Identified Problems:**")
            for problem in row['problems']:
                st.write(f"- {problem}")
        
        if row['suggestions']:
            st.write("**Customer Suggestions:**")
            for suggestion in row['suggestions']:
                st.write(f"- {suggestion}")
    
    def render_export(self, df):
        """Data export tab"""
        st.subheader("Export Analyzed Data")
        st.dataframe(df[['review_id', 'date', 'rating_text', 'rating_num',
                         'sentiment', 'word_count', 'length_category']].head(), use_container_width=True)
        
        # CSV export
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Full Data (CSV)", csv, "review_analysis.csv", "text/csv")
        
        # PDF export
        if st.button("Download Summary Report (PDF)"):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer)
            styles = getSampleStyleSheet()
            story = []
            story.append(Paragraph("Customer Review Analysis Report", styles['Title']))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"Total Reviews: {len(df)}", styles['Normal']))
            story.append(Paragraph(f"Average Rating: {df['rating_num'].mean():.1f}/5", styles['Normal']))
            story.append(Paragraph(f"Positive: {len(df[df['sentiment']=='positive'])}", styles['Normal']))
            story.append(Paragraph(f"Negative: {len(df[df['sentiment']=='negative'])}", styles['Normal']))
            story.append(Paragraph(f"Neutral: {len(df[df['sentiment']=='neutral'])}", styles['Normal']))
            story.append(Spacer(1, 12))
            story.append(Paragraph("Top Problems:", styles['Heading2']))
            all_problems = []
            for problems in df['problems']:
                all_problems.extend(problems)
            if all_problems:
                problem_counts = pd.Series(all_problems).value_counts().head(5)
                for prob, count in problem_counts.items():
                    story.append(Paragraph(f"- {prob} ({count})", styles['Normal']))
            else:
                story.append(Paragraph("No problems detected.", styles['Normal']))
            doc.build(story)
            buffer.seek(0)
            st.download_button("Download PDF", buffer, "review_summary.pdf", "application/pdf")

def main():
    dashboard = ReviewDashboard()
    uploaded_file, pasted_json = dashboard.render_upload_section()
    
    df = dashboard.process_input(uploaded_file, pasted_json)
    if df is not None:
        dashboard.create_dashboard(df)
    else:
        st.info("Please upload a file or paste JSON data to begin analysis.")

if __name__ == "__main__":
    main()
