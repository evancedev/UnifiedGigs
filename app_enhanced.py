import streamlit as st
import pandas as pd
from __init__ import scrape_jobs
from freelance_gig_search import search_mern_freelance_gigs, get_mern_stack_search_queries
from util import strip_markdown_formatting
import datetime
import csv

# Set page configuration
st.set_page_config(
    page_title="UnifiedGigs - MERN Stack Developer Job & Freelance Search",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with enhanced styling for freelance gigs
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .job-title, .gig-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .gig-title {
        color: #FF6B35;
    }
    .job-company, .gig-client {
        font-size: 1rem;
        color: #333;
        font-weight: 600;
    }
    .gig-client {
        color: #2E7D32;
    }
    .job-location, .gig-platform {
        font-size: 0.9rem;
        color: #555;
    }
    .gig-platform {
        color: #7B1FA2;
        font-weight: 600;
    }
    .job-details, .gig-details {
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }
    .job-card, .gig-card {
        background-color: #f9f9f9;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #1E88E5;
        position: relative;
    }
    .gig-card {
        border-left: 4px solid #FF6B35;
        background-color: #fff8f6;
    }
    .job-platform, .gig-platform-badge {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background-color: #1E88E5;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
        color: white;
        font-weight: 500;
        text-transform: capitalize;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        letter-spacing: 0.5px;
    }
    .gig-platform-badge {
        background-color: #FF6B35;
    }
    .badge {
        background-color: #f0f2f6;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        margin-right: 0.5rem;
        font-size: 0.8rem;
        color: #1E88E5;
        display: inline-block;
    }
    .gig-badge {
        background-color: #fff3e0;
        color: #FF6B35;
    }
    .salary-range, .budget-range {
        background-color: #e3f2fd;
        padding: 0.5rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .budget-range {
        background-color: #fff3e0;
        border-left: 3px solid #FF6B35;
    }
    .job-description, .gig-description {
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #666;
        line-height: 1.4;
    }
    .job-actions, .gig-actions {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
    }
    .view-job-btn, .save-job-btn, .view-gig-btn, .save-gig-btn {
        padding: 0.8rem 1.5rem;
        border-radius: 6px;
        text-decoration: none;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 120px;
        font-size: 0.95rem;
        border: none;
    }
    .view-job-btn, .view-gig-btn {
        background-color: #1E88E5;
        color: white !important;
        box-shadow: 0 2px 4px rgba(30, 136, 229, 0.2);
    }
    .view-gig-btn {
        background-color: #FF6B35;
        box-shadow: 0 2px 4px rgba(255, 107, 53, 0.2);
    }
    .save-job-btn, .save-gig-btn {
        background-color: #ffffff;
        color: #1E88E5 !important;
        border: 2px solid #1E88E5;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .save-gig-btn {
        color: #FF6B35 !important;
        border: 2px solid #FF6B35;
    }
    .view-job-btn:hover, .save-job-btn:hover, .view-gig-btn:hover, .save-gig-btn:hover {
        opacity: 1;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .view-job-btn:hover {
        background-color: #1976D2;
    }
    .view-gig-btn:hover {
        background-color: #E55A2B;
    }
    .save-job-btn:hover {
        background-color: #f8f9fa;
    }
    .save-gig-btn:hover {
        background-color: #fff8f6;
    }
    .stButton>button {
        width: 100%;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        border-radius: 6px;
    }
    .search-type-selector {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .mern-highlight {
        background-color: #e8f5e8;
        border-left: 4px solid #4CAF50;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# App title with MERN stack focus
st.title("💻 UnifiedGigs - MERN Stack Developer Hub")
st.subheader("Find your next job or freelance gig across multiple platforms")

# Search type selector
st.markdown("""
<div class="search-type-selector">
    <h3>🎯 What are you looking for?</h3>
</div>
""", unsafe_allow_html=True)

search_type = st.radio(
    "Search Type",
    ["🏢 Traditional Jobs", "💼 Freelance Gigs", "🔍 Both"],
    horizontal=True
)

# Sidebar for filters
st.sidebar.header("Search Filters")

# Job boards selection (for traditional jobs)
if search_type in ["🏢 Traditional Jobs", "🔍 Both"]:
    st.sidebar.subheader("Traditional Job Boards")
    job_boards = st.sidebar.multiselect(
        "Select Job Boards",
        ["linkedin", "indeed"],
        default=["linkedin", "indeed"]
    )

# Freelance platforms selection
if search_type in ["💼 Freelance Gigs", "🔍 Both"]:
    st.sidebar.subheader("Freelance Platforms")
    
    # Show platform recommendations
    with st.sidebar.expander("💡 Platform Recommendations"):
        st.markdown("""
        **Less Competitive Options:**
        - **Reddit Communities** - Lower competition, direct contact
        - **Discord Servers** - Community-based, networking
        - **Local Platforms** - Personal connections, higher rates
        
        **Traditional Platforms:**
        - **Upwork** - High competition, platform fees
        - **Fiverr** - Saturated market, lower rates
        - **Freelancer** - Competitive bidding
        """)
    
    freelance_platforms = st.sidebar.multiselect(
        "Select Freelance Platforms",
        ["reddit", "discord", "local", "upwork", "fiverr", "freelancer"],
        default=["reddit", "discord", "local"]
    )

# MERN Stack specific categories
mern_categories = {
    "MERN Stack Development": "MERN stack OR React Node.js MongoDB OR full stack JavaScript",
    "React Frontend": "React developer OR React.js OR React frontend",
    "Node.js Backend": "Node.js developer OR Express.js OR Node.js backend",
    "MongoDB Database": "MongoDB developer OR MongoDB database OR NoSQL",
    "Full Stack JavaScript": "full stack JavaScript OR JavaScript full stack OR MEAN stack",
    "Web Development": "web developer OR web development OR JavaScript developer",
    "API Development": "API developer OR REST API OR API development",
    "E-commerce Development": "e-commerce developer OR online store OR shopping cart",
    "Real-time Applications": "real-time OR Socket.io OR WebSocket OR chat application",
    "Progressive Web Apps": "PWA OR progressive web app OR mobile web app"
}

# Traditional job categories (enhanced for web development with MERN stack focus)
traditional_categories = {
    # MERN Stack Specific Categories (highlighted for developers)
    "MERN Stack Development": "MERN stack OR React Node.js MongoDB OR full stack JavaScript",
    "React Frontend Development": "React developer OR React.js OR React frontend OR React.js developer",
    "Node.js Backend Development": "Node.js developer OR Express.js OR Node.js backend OR Express developer",
    "MongoDB Database Development": "MongoDB developer OR MongoDB database OR NoSQL developer",
    "Full Stack JavaScript": "full stack JavaScript OR JavaScript full stack OR MEAN stack OR MERN stack developer",
    "API Development": "API developer OR REST API OR API development OR GraphQL developer",
    "E-commerce Development": "e-commerce developer OR online store OR shopping cart OR ecommerce",
    "Real-time Applications": "real-time OR Socket.io OR WebSocket OR chat application developer",
    "Progressive Web Apps": "PWA OR progressive web app OR mobile web app developer",
    
    # General Web Development Categories
    "Software Development": "software developer OR software engineer OR programmer OR full stack developer OR backend developer OR frontend developer",
    "Web Development": "web developer OR web development OR frontend developer OR backend developer",
    "JavaScript Development": "JavaScript developer OR JS developer OR Node.js developer OR React developer",
    "Full Stack Development": "full stack developer OR full stack engineer OR MEAN stack OR MERN stack",
    "Frontend Development": "frontend developer OR front end developer OR UI developer OR React developer",
    "Backend Development": "backend developer OR back end developer OR API developer OR server developer",
    "DevOps": "devops OR site reliability engineer OR platform engineer OR cloud engineer",
    "Data Science": "data scientist OR data analyst OR machine learning engineer OR AI OR data engineer",
    "Product Management": "product manager OR product owner OR scrum master OR agile coach OR project manager",
    "UI/UX Design": "UI designer OR UX designer OR user interface designer OR user experience designer",
}

# Category selection based on search type
if search_type == "🏢 Traditional Jobs":
    st.sidebar.markdown("**💻 MERN Stack Categories (Recommended for Developers):**")
    selected_category = st.sidebar.selectbox("Job Category", list(traditional_categories.keys()), index=0)
elif search_type == "💼 Freelance Gigs":
    selected_category = st.sidebar.selectbox("Freelance Category", list(mern_categories.keys()))
else:  # Both
    st.sidebar.subheader("Categories")
    st.sidebar.markdown("**💻 Traditional Job Categories:**")
    traditional_category = st.sidebar.selectbox("Traditional Job Category", list(traditional_categories.keys()), index=0)
    st.sidebar.markdown("**💼 Freelance Categories:**")
    freelance_category = st.sidebar.selectbox("Freelance Category", list(mern_categories.keys()))

# Location
location = st.sidebar.text_input("Location", "Remote")

# Country for Indeed
countries = ["USA", "UK", "Canada", "Australia", "India", "Germany", "France", "Spain", "Italy", "Singapore", 
             "Japan", "Brazil", "South Africa", "Mexico", "Netherlands", "Belgium", "Switzerland", "Hong Kong"]
country_indeed = st.sidebar.selectbox("Country (for Indeed)", countries)

# Work Type
work_type = st.sidebar.radio(
    "Work Type",
    ["All", "Remote", "On-site", "Hybrid"]
)

# Job Type (for traditional jobs)
if search_type in ["🏢 Traditional Jobs", "🔍 Both"]:
    job_type_options = st.sidebar.selectbox(
        "Job Type",
        ["fulltime", "parttime", "internship", "contract"]
    )

# Budget/Salary filters
st.sidebar.subheader("Budget/Salary Range")
min_budget = st.sidebar.number_input("Minimum Budget/Salary", min_value=0, value=0, step=100)
max_budget = st.sidebar.number_input("Maximum Budget/Salary", min_value=0, value=10000, step=100)

# Experience level
experience_level = st.sidebar.selectbox(
    "Experience Level",
    ["Any", "Entry Level", "Intermediate", "Expert"]
)

# Number of results
results_wanted = st.sidebar.slider("Number of results per platform", 10, 100, 20)

# Advanced options
with st.sidebar.expander("Advanced Options"):
    hours_old = st.number_input("Maximum age of postings (hours)", min_value=1, max_value=168, value=24)
    fetch_description = st.checkbox("Fetch full descriptions (slower)", value=False)
    easy_apply = st.checkbox("Easy Apply jobs only", value=False)

# Search button
search_button = st.sidebar.button("🔍 Search Opportunities", type="primary")

# Main content
if search_button:
    all_results = []
    
    # Search traditional jobs
    if search_type in ["🏢 Traditional Jobs", "🔍 Both"]:
        with st.spinner("Searching traditional job boards..."):
            try:
                # Create search term from the selected category
                if search_type == "🔍 Both":
                    search_term = traditional_categories[traditional_category]
                else:
                    search_term = traditional_categories[selected_category]
                
                # Generate a google_search_term
                google_search_term = f"{selected_category if search_type != '🔍 Both' else traditional_category} jobs near {location} since yesterday"

                # Set up parameters for scraping
                params = {
                    "site_name": job_boards,
                    "search_term": search_term,
                    "google_search_term": google_search_term,
                    "location": location,
                    "results_wanted": results_wanted,
                    "country_indeed": country_indeed,
                    "hours_old": hours_old,
                    "linkedin_fetch_description": fetch_description,
                }

                # Determine the is_remote parameter based on work type
                if work_type == "Remote":
                    params["is_remote"] = True
                    google_search_term = f"remote {selected_category if search_type != '🔍 Both' else traditional_category} jobs since yesterday"
                    search_term = f"remote {search_term}"
                elif work_type == "On-site":
                    params["is_remote"] = False
                elif work_type == "Hybrid":
                    search_term += " hybrid"
                
                # Update the search terms in params after modifications
                params["search_term"] = search_term
                params["google_search_term"] = google_search_term
                params["job_type"] = job_type_options
                
                if easy_apply:
                    params["easy_apply"] = True

                # Perform the search
                jobs = scrape_jobs(**params)
                
                # Post-process to ensure remote filter is strictly applied
                if work_type == "Remote":
                    jobs = jobs[jobs['is_remote'] == True]
                elif work_type == "On-site":
                    jobs = jobs[jobs['is_remote'] != True]
                
                # Filter by salary range
                if min_budget > 0 or max_budget < 10000:
                    jobs = jobs[
                        (jobs['min_amount'].fillna(0) >= min_budget) &
                        (jobs['max_amount'].fillna(float('inf')) <= max_budget)
                    ]
                
                if not jobs.empty:
                    jobs['search_type'] = 'Traditional Job'
                    all_results.append(jobs)
                    st.success(f"Found {len(jobs)} traditional jobs!")
                
            except Exception as e:
                st.error(f"Error searching traditional jobs: {str(e)}")
    
    # Search freelance gigs
    if search_type in ["💼 Freelance Gigs", "🔍 Both"]:
        with st.spinner("Searching freelance platforms..."):
            try:
                # Get the appropriate category
                if search_type == "🔍 Both":
                    freelance_category_to_use = freelance_category
                else:
                    freelance_category_to_use = selected_category
                
                # Convert experience level
                exp_level = None
                if experience_level != "Any":
                    exp_level = experience_level.lower()
                
                gigs = search_mern_freelance_gigs(
                    query_category=freelance_category_to_use,
                    platforms=freelance_platforms,
                    max_results_per_platform=results_wanted,
                    min_budget=min_budget,
                    max_budget=max_budget,
                    experience_level=exp_level
                )
                
                if not gigs.empty:
                    gigs['search_type'] = 'Freelance Gig'
                    all_results.append(gigs)
                    st.success(f"Found {len(gigs)} freelance gigs!")
                
            except Exception as e:
                st.error(f"Error searching freelance gigs: {str(e)}")
    
    # Display results
    if all_results:
        # Combine all results
        combined_results = pd.concat(all_results, ignore_index=True)
        
        # Save to CSV
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"mern_opportunities_{timestamp}.csv"
        combined_results.to_csv(csv_file, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
        
        # Create download button
        with open(csv_file, "rb") as file:
            btn = st.download_button(
                label="📥 Download All Results as CSV",
                data=file,
                file_name=csv_file,
                mime="text/csv"
            )
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["🎯 All Opportunities", "🏢 Traditional Jobs", "💼 Freelance Gigs"])
        
        with tab1:
            st.subheader(f"All Opportunities ({len(combined_results)} total)")
            
            # Filter by search type if needed
            if search_type == "🔍 Both":
                filter_type = st.selectbox("Filter by type:", ["All", "Traditional Job", "Freelance Gig"])
                if filter_type != "All":
                    combined_results = combined_results[combined_results['search_type'] == filter_type]
            
            # Display all opportunities
            for i, opportunity in combined_results.iterrows():
                if opportunity.get('search_type') == 'Freelance Gig':
                    # Display as freelance gig
                    st.markdown(f"""
                    <div class="gig-card">
                        <div class="gig-platform-badge">{opportunity.get('platform', 'Unknown')}</div>
                        <div class="gig-title">{opportunity.get('title', 'No Title')}</div>
                        <div class="gig-client">👤 Client Rating: {opportunity.get('client_rating', 'N/A')} ({opportunity.get('client_reviews', 0)} reviews)</div>
                        <div class="gig-platform">📱 Platform: {opportunity.get('platform', 'Unknown')}</div>
                        <div class="gig-details">
                            <span class="badge gig-badge">💰 {opportunity.get('budget_min', 'N/A')} - {opportunity.get('budget_max', 'N/A')} {opportunity.get('currency', 'USD')}</span>
                            <span class="badge gig-badge">📅 {opportunity.get('posted_date', 'Date not available')}</span>
                            <span class="badge gig-badge">🎯 {opportunity.get('experience_level', 'Not specified')}</span>
                            <span class="badge gig-badge">⏱️ {opportunity.get('duration', 'Not specified')}</span>
                        </div>
                        <div class="gig-details budget-range">
                            💰 Budget: {opportunity.get('budget_min', 'Not specified')} - {opportunity.get('budget_max', 'Not specified')} 
                            {opportunity.get('currency', 'USD')} | Type: {opportunity.get('project_type', 'Not specified')}
                        </div>
                        <div class="gig-description">
                            {strip_markdown_formatting(opportunity.get('description', '')[:300] + '...' if opportunity.get('description') else 'No description available')}
                        </div>
                        <div class="gig-actions">
                            <a href="{opportunity.get('url', '#')}" target="_blank" class="view-gig-btn">View Gig 👉</a>
                            <button onclick="saveGig('{i}')" class="save-gig-btn">Save Gig ⭐</button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Display as traditional job
                    st.markdown(f"""
                    <div class="job-card">
                        <div class="job-platform">{opportunity.get('site', 'Unknown')}</div>
                        <div class="job-title">{opportunity.get('title', 'No Title')}</div>
                        <div class="job-company">{opportunity.get('company', 'Unknown Company')}</div>
                        <div class="job-location">📍 {opportunity.get('location', 'Location not specified')}</div>
                        <div class="job-details">
                            <span class="badge">💼 {opportunity.get('job_type', 'Not specified')}</span>
                            <span class="badge">📅 {opportunity.get('date_posted', 'Date not available')}</span>
                            <span class="badge">🏠 {'Remote' if opportunity.get('is_remote') else 'On-site'}</span>
                        </div>
                        <div class="job-details salary-range">
                            💰 {opportunity.get('min_amount', 'Not specified')} - {opportunity.get('max_amount', 'Not specified')} 
                            {opportunity.get('currency', '')} {opportunity.get('interval', 'per year') if opportunity.get('interval') else 'per year'}
                        </div>
                        <div class="job-description">
                            {strip_markdown_formatting(opportunity.get('description', '')[:300] + '...' if opportunity.get('description') else 'No description available')}
                        </div>
                        <div class="job-actions">
                            <a href="{opportunity.get('job_url', '#')}" target="_blank" class="view-job-btn">View Job 👉</a>
                            <button onclick="saveJob('{i}')" class="save-job-btn">Save Job ⭐</button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab2:
            traditional_jobs = combined_results[combined_results['search_type'] == 'Traditional Job']
            if not traditional_jobs.empty:
                st.subheader(f"Traditional Jobs ({len(traditional_jobs)} found)")
                st.dataframe(traditional_jobs[['title', 'company', 'location', 'job_type', 'min_amount', 'max_amount', 'site']])
            else:
                st.info("No traditional jobs found")
        
        with tab3:
            freelance_gigs = combined_results[combined_results['search_type'] == 'Freelance Gig']
            if not freelance_gigs.empty:
                st.subheader(f"Freelance Gigs ({len(freelance_gigs)} found)")
                st.dataframe(freelance_gigs[['title', 'platform', 'budget_min', 'budget_max', 'experience_level', 'project_type']])
            else:
                st.info("No freelance gigs found")
    
    else:
        st.warning("No opportunities found matching your criteria. Try adjusting your filters.")

else:
    # Default welcome message with MERN stack focus
    st.markdown("""
    <div class="mern-highlight">
        <h3>🚀 Welcome, MERN Stack Developer!</h3>
        <p>This platform helps you find both traditional employment and freelance opportunities specifically tailored for your skills.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show MERN stack categories prominently
    st.markdown("### 💻 MERN Stack Categories Now Available!")
    st.markdown("""
    **In the sidebar, you'll now see these MERN stack specific categories:**
    
    🎯 **MERN Stack Development** - Full-stack MERN projects  
    ⚛️ **React Frontend Development** - React.js focused work  
    🟢 **Node.js Backend Development** - Backend/API development  
    🍃 **MongoDB Database Development** - Database and NoSQL work  
    🔗 **API Development** - REST/GraphQL API projects  
    🛒 **E-commerce Development** - Online store projects  
    ⚡ **Real-time Applications** - Chat, live features  
    📱 **Progressive Web Apps** - PWA development  
    
    *These categories work for both traditional jobs and freelance gigs!*
    """)
    
    # Add note about data sources and competition
    st.markdown("### ⚠️ Important Note About Data Sources")
    st.markdown("""
    **Current Implementation:**
    - Traditional job search uses **real-time data** from job boards
    - Freelance gig search uses **sample data** for demonstration
    - Real freelance platforms require API access and authentication
    
    **Better Alternatives for MERN Stack Developers:**
    - **Reddit Communities** (r/forhire, r/hireaprogrammer) - Lower competition
    - **Discord Servers** (Reactiflux, Node.js Community) - Community networking
    - **Local Platforms** (Facebook Groups, LinkedIn) - Personal connections
    - **Direct Outreach** - No competition, higher rates
    
    *See `LESS_COMPETITIVE_GUIDE.md` for detailed strategies!*
    """)
    
    st.info("👈 Set your search criteria in the sidebar and click 'Search Opportunities' to begin")
    
    # Show MERN stack specific tips
    with st.expander("💡 MERN Stack Developer Tips"):
        st.markdown("""
        ### Optimize Your Search for MERN Stack Opportunities:
        
        **For Traditional Jobs:**
        - Use "Full Stack Development" or "JavaScript Development" categories
        - Look for "React", "Node.js", "MongoDB" in job descriptions
        - Focus on remote opportunities for better flexibility
        
        **For Freelance Gigs:**
        - Start with "MERN Stack Development" category
        - Consider "React Frontend" and "Node.js Backend" for specialized work
        - Look for "API Development" for backend-focused projects
        - "E-commerce Development" often requires full-stack skills
        
        **Pro Tips:**
        - Set budget filters to match your experience level
        - Use "Remote" work type for maximum flexibility
        - Check "Easy Apply" for faster application process
        - Focus on recent postings (24-48 hours) for better response rates
        """)
    
    # Show platform comparison
    with st.expander("📊 Platform Comparison"):
        st.markdown("""
        ### Traditional Job Boards vs Freelance Platforms
        
        **Traditional Job Boards:**
        - LinkedIn: Professional networking, full-time positions
        - Indeed: Large job database, various contract types
        
        **Freelance Platforms:**
        - Upwork: Large marketplace, diverse project types
        - Fiverr: Service-based gigs, quick projects
        - Freelancer.com: Competitive bidding, various project sizes
        
        **Best for MERN Stack:**
        - Traditional: Full-time roles, long-term contracts
        - Freelance: Project-based work, portfolio building, flexible hours
        """)

    # Show About information
    with st.expander("About This Tool", expanded=False):
        st.markdown("""
        ## About UnifiedGigs for MERN Stack Developers
        
        This enhanced interface combines traditional job search with specialized freelance gig search,
        specifically optimized for MERN stack developers looking for both employment and freelance opportunities.
        
        **Key Features:**
        - Multi-platform job and gig search
        - MERN stack specific categories
        - Budget and experience level filtering
        - Remote work focus
        - Export capabilities for tracking opportunities
        """) 