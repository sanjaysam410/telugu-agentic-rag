import streamlit as st
import json
import os
import sys
from datetime import datetime
import pandas as pd

from agents.keyword_agent import KeywordAgent

# Page config
st.set_page_config(
    page_title="Keyword Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize agent
@st.cache_resource
def get_agent():
    return KeywordAgent()

agent = get_agent()

# Title and description
st.title("📊 Keyword Intelligence Dashboard")
st.markdown("TF-IDF based keyword analytics with trend tracking and co-occurrence analysis")

# Sidebar
with st.sidebar:
    st.header("⚙️ Controls")
    
    if st.button("🔄 Refresh Stats", type="primary"):
        st.cache_resource.clear()
        st.rerun()
    
    if st.button("⚡ Run Incremental Update"):
        with st.spinner("Running incremental update..."):
            agent.incremental_update()
            st.success("Incremental update complete!")
            st.cache_resource.clear()
            st.rerun()
    
    if st.button("🌙 Run Nightly Recalculation"):
        with st.spinner("Running full recalculation..."):
            agent.nightly_full_recalculation()
            st.success("Nightly recalculation complete!")
            st.cache_resource.clear()
            st.rerun()
    
    st.divider()
    
    st.subheader("📝 Test Data")
    if st.button("Generate Sample Data"):
        # Generate sample stories
        sample_stories = [
            {
                "keywords": ["రాజు", "వినయం", "గర్వం", "పాఠం"],
                "characters": ["రాజు", "మంత్రి", "సైనికుడు"],
                "locations": ["రాజ్యం", "అడవి", "కోట"],
                "normalized_genre_code": "MORAL_STORY",
                "author": "విశ్వం"
            },
            {
                "keywords": ["బంగారు లేడి", "అడవి", "జింక", "వేటగాడు"],
                "characters": ["వేటగాడు", "జింక"],
                "locations": ["అడవి", "గుహ"],
                "normalized_genre_code": "FOLK_TALE",
                "author": "శ్రీనివాస్"
            },
            {
                "keywords": ["చంద్రుడు", "నక్షత్రాలు", "రాత్రి", "కలలు"],
                "characters": ["చిన్నారి", "తల్లి"],
                "locations": ["ఇల్లు", "పైకప్పు"],
                "normalized_genre_code": "BEDTIME_STORY",
                "author": "రమణ"
            },
            {
                "keywords": ["రాజు", "కోట", "యుద్ధం", "విజయం"],
                "characters": ["రాజు", "శత్రువు", "సైన్యం"],
                "locations": ["కోట", "యుద్ధభూమి", "రాజ్యం"],
                "normalized_genre_code": "ADVENTURE",
                "author": "విశ్వం"
            },
            {
                "keywords": ["పాఠం", "విద్య", "గురువు", "శిష్యుడు"],
                "characters": ["గురువు", "శిష్యుడు"],
                "locations": ["పాఠశాల", "ఆశ్రమం"],
                "normalized_genre_code": "MORAL_STORY",
                "author": "రమణ"
            }
        ]
        
        for story in sample_stories:
            agent.on_story_ingested(story)
        
        agent.incremental_update()
        agent.nightly_full_recalculation()
        
        st.success(f"Generated {len(sample_stories)} sample stories!")
        st.cache_resource.clear()
        st.rerun()

# Load stats
try:
    stats = agent.get_stats()
except Exception as e:
    st.error(f"Error loading stats: {e}")
    st.stop()

# Main dashboard
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview", 
    "🔥 Trending", 
    "🔍 Search", 
    "🔗 Co-occurrence",
    "📊 Analytics"
])

# Tab 1: Overview
with tab1:
    st.header("Corpus Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Stories",
            f"{stats['corpus_stats']['total_stories']:,}"
        )
    
    with col2:
        st.metric(
            "Total Keywords",
            f"{len(stats['keywords']):,}"
        )
    
    with col3:
        st.metric(
            "Total Words",
            f"{stats['corpus_stats']['total_words']:,}"
        )
    
    with col4:
        st.metric(
            "Unique Authors",
            f"{len(stats['authors']):,}"
        )
    
    st.divider()
    
    # Top keywords by TF-IDF
    st.subheader("🏆 Top Keywords by TF-IDF Score")
    
    if stats['keywords']:
        top_keywords = sorted(
            stats['keywords'].items(),
            key=lambda x: x[1].get('tfidf_score', 0),
            reverse=True
        )[:20]
        
        df = pd.DataFrame([
            {
                'Rank': i + 1,
                'Keyword': kw,
                'TF-IDF': data.get('tfidf_score', 0),
                'Count': data.get('count', 0),
                'Doc Freq': data.get('document_frequency', 0),
                'Percentile': f"{data.get('percentile', 0)}%",
                'Trend': data.get('trend', 'stable')
            }
            for i, (kw, data) in enumerate(top_keywords)
        ])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No keywords yet. Generate sample data to get started!")
    
    st.divider()
    
    # Top keywords by frequency
    st.subheader("📊 Top Keywords by Frequency")
    
    if stats['keywords']:
        top_by_count = sorted(
            stats['keywords'].items(),
            key=lambda x: x[1].get('count', 0),
            reverse=True
        )[:20]
        
        df_count = pd.DataFrame([
            {
                'Keyword': kw,
                'Count': data.get('count', 0),
                'TF-IDF': data.get('tfidf_score', 0),
                'Rank': data.get('rank', 0)
            }
            for kw, data in top_by_count
        ])
        
        st.bar_chart(df_count.set_index('Keyword')['Count'])

# Tab 2: Trending
with tab2:
    st.header("🔥 Trending Keywords")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Rising Keywords")
        rising = stats.get('trending', {}).get('rising', [])
        
        if rising:
            for item in rising:
                keyword = item['keyword']
                delta = item['delta']
                kw_data = stats['keywords'].get(keyword, {})
                
                st.metric(
                    keyword,
                    f"Rank #{kw_data.get('rank', 'N/A')}",
                    delta=f"+{delta} positions",
                    delta_color="normal"
                )
        else:
            st.info("No rising keywords yet")
    
    with col2:
        st.subheader("📉 Falling Keywords")
        falling = stats.get('trending', {}).get('falling', [])
        
        if falling:
            for item in falling:
                keyword = item['keyword']
                delta = item['delta']
                kw_data = stats['keywords'].get(keyword, {})
                
                st.metric(
                    keyword,
                    f"Rank #{kw_data.get('rank', 'N/A')}",
                    delta=f"{delta} positions",
                    delta_color="inverse"
                )
        else:
            st.info("No falling keywords yet")

# Tab 3: Search
with tab3:
    st.header("🔍 Keyword Search")
    
    search_term = st.text_input("Search for a keyword:", placeholder="Type a keyword in Telugu or English")
    
    if search_term:
        # Search in keywords
        matches = {k: v for k, v in stats['keywords'].items() if search_term.lower() in k.lower()}
        
        if matches:
            st.success(f"Found {len(matches)} matching keyword(s)")
            
            for keyword, data in sorted(matches.items(), key=lambda x: x[1].get('tfidf_score', 0), reverse=True):
                with st.expander(f"**{keyword}** (Rank #{data.get('rank', 'N/A')})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("TF-IDF Score", f"{data.get('tfidf_score', 0):.4f}")
                        st.metric("Count", data.get('count', 0))
                    
                    with col2:
                        st.metric("Document Frequency", data.get('document_frequency', 0))
                        st.metric("Percentile", f"{data.get('percentile', 0)}%")
                    
                    with col3:
                        trend = data.get('trend', 'stable')
                        trend_emoji = {"up": "📈", "down": "📉", "stable": "➡️", "new": "🆕"}.get(trend, "➡️")
                        st.metric("Trend", f"{trend_emoji} {trend.title()}")
                        st.metric("Trend Delta", data.get('trend_delta', 0))
                    
                    st.caption(f"Last seen: {data.get('last_seen', 'Unknown')}")
        else:
            st.warning(f"No keywords found matching '{search_term}'")

# Tab 4: Co-occurrence
with tab4:
    st.header("🔗 Keyword Co-occurrence")
    
    st.info("Co-occurrence matrix shows keywords that frequently appear together in stories.")
    
    co_occur = stats.get('co_occurrence_matrix', {}).get('keywords', {})
    
    if co_occur:
        # Select a keyword to see co-occurrences
        keyword_list = sorted(co_occur.keys())
        selected_keyword = st.selectbox("Select a keyword:", keyword_list)
        
        if selected_keyword:
            related = co_occur.get(selected_keyword, [])
            
            if related:
                st.subheader(f"Keywords that appear with '{selected_keyword}':")
                
                for related_kw in related:
                    kw_data = stats['keywords'].get(related_kw, {})
                    st.write(f"- **{related_kw}** (TF-IDF: {kw_data.get('tfidf_score', 0):.4f}, Count: {kw_data.get('count', 0)})")
            else:
                st.info(f"No co-occurring keywords found for '{selected_keyword}'")
    else:
        st.info("Co-occurrence matrix not yet generated. Run nightly recalculation to build it.")

# Tab 5: Analytics
with tab5:
    st.header("📊 Advanced Analytics")
    
    # Genre distribution
    st.subheader("Genre Distribution")
    if stats.get('genres'):
        genre_df = pd.DataFrame([
            {'Genre': k, 'Count': v.get('count', 0)}
            for k, v in stats['genres'].items()
        ]).sort_values('Count', ascending=False)
        
        st.bar_chart(genre_df.set_index('Genre')['Count'])
    else:
        st.info("No genre data available")
    
    st.divider()
    
    # Author distribution
    st.subheader("Top Authors")
    if stats.get('authors'):
        author_df = pd.DataFrame([
            {'Author': k, 'Stories': v.get('count', 0)}
            for k, v in stats['authors'].items()
        ]).sort_values('Stories', ascending=False).head(10)
        
        st.dataframe(author_df, use_container_width=True, hide_index=True)
    else:
        st.info("No author data available")
    
    st.divider()
    
    # Characters and Locations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Characters")
        if stats.get('characters'):
            char_df = pd.DataFrame([
                {'Character': k, 'Count': v.get('count', 0)}
                for k, v in sorted(stats['characters'].items(), key=lambda x: x[1].get('count', 0), reverse=True)[:10]
            ])
            st.dataframe(char_df, use_container_width=True, hide_index=True)
        else:
            st.info("No character data")
    
    with col2:
        st.subheader("Top Locations")
        if stats.get('locations'):
            loc_df = pd.DataFrame([
                {'Location': k, 'Count': v.get('count', 0)}
                for k, v in sorted(stats['locations'].items(), key=lambda x: x[1].get('count', 0), reverse=True)[:10]
            ])
            st.dataframe(loc_df, use_container_width=True, hide_index=True)
        else:
            st.info("No location data")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    last_update = stats.get('last_incremental_update', 'Never')
    st.caption(f"Last incremental update: {last_update}")

with col2:
    generated_at = stats.get('generated_at', 'Unknown')
    st.caption(f"Stats generated: {generated_at}")

with col3:
    st.caption(f"Total entities tracked: {len(stats['keywords']) + len(stats['characters']) + len(stats['locations']):,}")
