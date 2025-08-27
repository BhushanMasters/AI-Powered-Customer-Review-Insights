import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from data_ingester import DataIngester
from review_analyzer import ReviewAnalyzer

# Page configuration
st.set_page_config(
    page_title="AI Review Insights Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1f77b4; margin-bottom: 1rem;}
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px;}
    .positive {color: green; font-weight: bold;}
    .negative {color: red; font-weight: bold;}
    .neutral {color: orange; font-weight: bold;}
    .upload-section {background-color: #e8f4f8; padding: 20px; border-radius: 10px; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

class ReviewDashboard:
    def __init__(self):
        self.ingester = DataIngester()
        self.analyzer = ReviewAnalyzer()
        self.analyzed_df = pd.DataFrame()
    
    def render_upload_section(self):
        """Render file upload section"""
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.subheader("📁 Upload Your Customer Reviews")
        
        uploaded_file = st.file_uploader(
            "Choose a JSON or CSV file",
            type=['json', 'csv'],
            help="Upload a file containing customer reviews. Supported formats: JSON, CSV"
        )
        
        st.markdown("""
        **Expected JSON Format:**
        ```json
        [
            {
                "review_id": "R12345",
                "date": "2025-01-01",
                "rating": "★★★☆☆ (3 stars)",
                "text": "Your review text here..."
            }
        ]
        ```
        
        **Or any structure with review text content**
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
        return uploaded_file
    
    def process_uploaded_file(self, uploaded_file):
        """Process the uploaded file and analyze reviews"""
        if uploaded_file is None:
            return None
        
        with st.spinner("📥 Reading uploaded file..."):
            raw_reviews = self.ingester.ingest_file(uploaded_file)
        
        if not raw_reviews:
            st.error("No valid reviews found in the uploaded file.")
            return None
        
        st.success(f"✅ Successfully loaded {len(raw_reviews)} reviews from {uploaded_file.name}")
        
        # Show raw data preview
        with st.expander("📋 Preview Raw Data"):
            if raw_reviews:
                preview_data = []
                for review in raw_reviews[:5]:  # Show first 5 reviews
                    if isinstance(review, dict):
                        preview_data.append({
                            'review_id': review.get('review_id', 'N/A'),
                            'date': review.get('date', 'N/A'),
                            'rating': review.get('rating', 'N/A'),
                            'text_preview': str(review.get('text', 'N/A'))[:100] + '...' if review.get('text') else 'N/A'
                        })
                if preview_data:
                    st.dataframe(pd.DataFrame(preview_data))
        
        # Analyze reviews
        with st.spinner("🤖 Analyzing reviews with AI..."):
            self.analyzed_df = self.analyzer.analyze_batch(raw_reviews)
        
        if not self.analyzed_df.empty:
            st.success("✅ Analysis complete! Displaying insights...")
            return self.analyzed_df
        else:
            st.error("❌ Analysis failed. Please check your file format.")
            return None
    
    def create_dashboard(self, df):
        """Create the main dashboard with analysis results"""
        
        # Header
        st.markdown('<h1 class="main-header">📊 AI-Powered Customer Review Insights</h1>', 
                   unsafe_allow_html=True)
        
        # Key Metrics
        st.subheader("📈 Key Metrics")
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
            avg_rating = df['numeric_rating'].mean()
            st.metric("Avg Rating", f"{avg_rating:.1f}/5")
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", "🧠 Sentiment Analysis", "🔍 Topics & Insights", 
            "⭐ Rating Analysis", "📋 Raw Data"
        ])
        
        with tab1:
            self.render_overview_tab(df)
        
        with tab2:
            self.render_sentiment_tab(df)
        
        with tab3:
            self.render_insights_tab(df)
        
        with tab4:
            self.render_rating_tab(df)
        
        with tab5:
            self.render_raw_data_tab(df)
    
    def render_overview_tab(self, df):
        """Render overview tab"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment distribution
            sentiment_counts = df['sentiment'].value_counts()
            fig = px.pie(
                values=sentiment_counts.values, 
                names=sentiment_counts.index,
                title="Sentiment Distribution",
                color=sentiment_counts.index,
                color_discrete_map={'positive': 'green', 'negative': 'red', 'neutral': 'orange'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Rating distribution
            fig = px.histogram(df, x='numeric_rating', nbins=5,
                             title="Rating Distribution",
                             labels={'numeric_rating': 'Rating'})
            fig.update_xaxes(dtick=1)
            st.plotly_chart(fig, use_container_width=True)
        
        # Success rate
        success_rate = (df['analysis_success'].sum() / len(df)) * 100
        st.metric("Analysis Success Rate", f"{success_rate:.1f}%")
    
    def render_sentiment_tab(self, df):
        """Render sentiment analysis tab"""
        st.subheader("Detailed Sentiment Analysis")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            sentiment_filter = st.selectbox("Filter by Sentiment", 
                                          ["All", "Positive", "Negative", "Neutral"])
        with col2:
            min_rating = st.slider("Minimum Rating", 1.0, 5.0, 1.0, 0.5)
        
        # Apply filters
        filtered_df = df[df['numeric_rating'] >= min_rating]
        if sentiment_filter != "All":
            filtered_df = filtered_df[filtered_df['sentiment'] == sentiment_filter.lower()]
        
        # Display filtered reviews
        for _, row in filtered_df.iterrows():
            sentiment_color = row['sentiment']
            
            with st.expander(f"📝 {row['review_id']} - {row['date']} - Rating: {row['numeric_rating']}/5"):
                col_a, col_b = st.columns([1, 2])
                
                with col_a:
                    st.markdown(f"**Sentiment:** <span class='{sentiment_color}'>{row['sentiment'].upper()}</span>", 
                               unsafe_allow_html=True)
                    st.write(f"**Original Rating:** {row['original_rating']}")
                    st.write(f"**Words:** {row['word_count']}")
                
                with col_b:
                    st.write("**Review Text:**")
                    st.write(row['text'])
                    
                    if row['problems']:
                        st.write("**⚠️ Problems:**")
                        for problem in row['problems']:
                            st.write(f"- {problem}")
                    
                    if row['suggestions']:
                        st.write("**💡 Suggestions:**")
                        for suggestion in row['suggestions']:
                            st.write(f"- {suggestion}")
    
    def render_insights_tab(self, df):
        """Render insights tab"""
        st.subheader("Aggregated Business Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Topics word cloud
            st.subheader("📌 Most Discussed Topics")
            all_topics = []
            for topics in df['topics']:
                if isinstance(topics, list):
                    all_topics.extend(topics)
            
            if all_topics:
                topic_counts = pd.Series(all_topics).value_counts().head(15)
                fig = px.bar(
                    x=topic_counts.values, 
                    y=topic_counts.index,
                    orientation='h',
                    title="Top 15 Topics",
                    labels={'x': 'Frequency', 'y': 'Topic'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No topics identified in the reviews")
        
        with col2:
            # Problems analysis
            st.subheader("⚠️ Critical Issues")
            all_problems = []
            for problems in df['problems']:
                if isinstance(problems, list):
                    all_problems.extend(problems)
            
            if all_problems:
                problem_counts = pd.Series(all_problems).value_counts().head(10)
                fig = px.bar(
                    x=problem_counts.values,
                    y=problem_counts.index,
                    orientation='h',
                    title="Top 10 Problems",
                    labels={'x': 'Frequency', 'y': 'Problem'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No problems identified")
        
        # Suggestions section
        st.subheader("💡 Customer Suggestions & Feature Requests")
        all_suggestions = []
        for suggestions in df['suggestions']:
            if isinstance(suggestions, list):
                all_suggestions.extend(suggestions)
        
        if all_suggestions:
            unique_suggestions = list(set(all_suggestions))
            for i, suggestion in enumerate(unique_suggestions, 1):
                st.write(f"{i}. **{suggestion}**")
        else:
            st.info("No suggestions found in reviews")
    
    def render_rating_tab(self, df):
        """Render rating analysis tab"""
        st.subheader("⭐ Detailed Rating Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Rating vs Sentiment
            rating_sentiment = df.groupby(['numeric_rating', 'sentiment']).size().unstack(fill_value=0)
            fig = px.bar(rating_sentiment, title="Rating vs Sentiment",
                        labels={'value': 'Count', 'numeric_rating': 'Rating'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Rating distribution by sentiment
            fig = px.box(df, x='sentiment', y='numeric_rating',
                        title="Rating Distribution by Sentiment")
            st.plotly_chart(fig, use_container_width=True)
        
        # Correlation analysis
        st.subheader("📊 Review Length vs Rating")
        fig = px.scatter(df, x='word_count', y='numeric_rating', color='sentiment',
                        title="Does Review Length Correlate with Rating?",
                        labels={'word_count': 'Number of Words', 'numeric_rating': 'Rating'})
        st.plotly_chart(fig, use_container_width=True)
    
    def render_raw_data_tab(self, df):
        """Render raw data tab"""
        st.subheader("📊 Complete Analyzed Data")
        
        # Show dataframe with important columns
        display_cols = ['review_id', 'date', 'original_rating', 'numeric_rating', 
                       'sentiment', 'word_count', 'analysis_success']
        st.dataframe(df[display_cols], use_container_width=True, height=400)
        
        # Download options
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Full Data (CSV)",
                data=csv,
                file_name="complete_analysis.csv",
                mime="text/csv"
            )
        
        with col2:
            summary_csv = df[display_cols].to_csv(index=False)
            st.download_button(
                label="📥 Download Summary (CSV)",
                data=summary_csv,
                file_name="analysis_summary.csv",
                mime="text/csv"
            )
        
        # Statistics
        st.subheader("📈 Dataset Statistics")
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        
        with stats_col1:
            st.metric("Total Characters", f"{df['character_count'].sum():,}")
        with stats_col2:
            st.metric("Total Words", f"{df['word_count'].sum():,}")
        with stats_col3:
            avg_words = df['word_count'].mean()
            st.metric("Avg Words/Review", f"{avg_words:.1f}")

def main():
    """Main application function"""
    st.sidebar.title("⚙️ Dashboard Settings")
    
    st.sidebar.info("""
    **Upload Requirements:**
    - JSON or CSV file format
    - Should contain review text data
    - Any structure is accepted
    - Minimum 1 review required
    """)
    
    # Initialize dashboard
    dashboard = ReviewDashboard()
    
    # File upload section
    uploaded_file = dashboard.render_upload_section()
    
    # Process file if uploaded
    if uploaded_file is not None:
        df = dashboard.process_uploaded_file(uploaded_file)
        
        if df is not None and not df.empty:
            dashboard.create_dashboard(df)
        else:
            st.warning("Please upload a valid file with customer reviews.")
    else:
        st.info("👆 Please upload a JSON or CSV file containing customer reviews to begin analysis.")

if __name__ == "__main__":
    main()