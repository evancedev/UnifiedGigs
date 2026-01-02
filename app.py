import streamlit as st
import pandas as pd
from __init__ import scrape_jobs
from util import strip_markdown_formatting
import datetime
import csv

# Set page configuration
st.set_page_config(
    page_title="UnifiedGigs - Comprehensive Job & Freelance Search Interface",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to improve the appearance
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .job-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .job-company {
        font-size: 1rem;
        color: #333;
        font-weight: 600;
    }
    .job-location {
        font-size: 0.9rem;
        color: #555;
    }
    .job-details {
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }
    .job-card {
        background-color: #f9f9f9;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #1E88E5;
        position: relative;
    }
    .job-platform {
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
    .badge {
        background-color: #f0f2f6;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        margin-right: 0.5rem;
        font-size: 0.8rem;
        color: #1E88E5;
        display: inline-block;
    }
    .salary-range {
        background-color: #e3f2fd;
        padding: 0.5rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .job-description {
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #666;
        line-height: 1.4;
    }
    .job-actions {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
    }
    .view-job-btn, .save-job-btn {
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
    .view-job-btn {
        background-color: #1E88E5;
        color: white !important;
        box-shadow: 0 2px 4px rgba(30, 136, 229, 0.2);
    }
    .save-job-btn {
        background-color: #ffffff;
        color: #1E88E5 !important;
        border: 2px solid #1E88E5;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .view-job-btn:hover, .save-job-btn:hover {
        opacity: 1;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .view-job-btn:hover {
        background-color: #1976D2;
    }
    .save-job-btn:hover {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# App title
st.title("UnifiedGigs - Advanced Job & Freelance Search")
st.subheader("Find your dream job or freelance opportunity across multiple platforms")

# Sidebar for filters
st.sidebar.header("Search Filters")

# Job boards selection
job_boards = st.sidebar.multiselect(
    "Select Job Boards",
    ["linkedin", "indeed"],
    default=["linkedin", "indeed"]
)

# Job Categories
job_categories = {
    "Software Development": "software developer OR software engineer OR programmer OR full stack developer OR backend developer OR frontend developer",
    "Data Science": "data scientist OR data analyst OR machine learning engineer OR AI OR data engineer",
    "Graphic Design": "graphic designer OR UI designer OR UX designer OR visual designer OR creative designer",
    "Marketing": "marketing OR digital marketing OR content marketing OR SEO specialist OR social media manager",
    "Product Management": "product manager OR product owner OR scrum master OR agile coach OR project manager",
    "Customer Support": "customer support OR customer service OR help desk OR technical support OR customer success",
    "Sales": "sales OR account executive OR business development OR sales representative OR account manager",
    "Human Resources": "HR OR human resources OR recruiter OR talent acquisition OR HR manager",
    "Finance": "finance OR accountant OR financial analyst OR controller OR CFO OR bookkeeper",
    "Administrative": "administrative OR executive assistant OR office manager OR receptionist OR coordinator",
    "Data Entry": "data entry OR data entry clerk OR data entry operator OR data entry specialist OR data processor OR transcriptionist",
    "Cybersecurity": "cybersecurity OR security engineer OR security analyst OR penetration tester OR information security OR security architect",
    "DevOps": "devops OR site reliability engineer OR platform engineer OR cloud engineer OR infrastructure engineer OR kubernetes",
    "Healthcare": "nurse OR doctor OR healthcare administrator OR medical assistant OR physician OR healthcare manager",
    "Education": "teacher OR instructor OR professor OR tutor OR educational consultant OR curriculum developer",
    "Project Management": "project manager OR program manager OR project coordinator OR project lead OR delivery manager",
    # New Freelance Categories
    "Virtual Assistance": "virtual assistant OR VA OR remote assistant OR personal assistant OR executive VA OR administrative assistant",
    "Social Media Management": "social media manager OR social media strategist OR community manager OR social media specialist OR content scheduler OR social media coordinator",
    "Content Creation": "content creator OR content writer OR blogger OR copywriter OR content strategist OR ghostwriter OR article writer OR creative writer",
    "Freelance Writing": "freelance writer OR freelance content writer OR copywriter OR editor OR proofreader OR technical writer OR SEO writer",
    "Freelance Design": "freelance designer OR graphic design freelancer OR logo designer OR illustrator OR brand identity designer OR web designer"
}

selected_category = st.sidebar.selectbox("Job Category", list(job_categories.keys()))

# Location
location = st.sidebar.text_input("Location", "New York, NY")

# Country for Indeed
countries = ["USA", "UK", "Canada", "Australia", "India", "Germany", "France", "Spain", "Italy", "Singapore", 
             "Japan", "Brazil", "South Africa", "Mexico", "Netherlands", "Belgium", "Switzerland", "Hong Kong"]
country_indeed = st.sidebar.selectbox("Country (for Indeed)", countries)

# Work Type
work_type = st.sidebar.radio(
    "Work Type",
    ["All", "Remote", "On-site", "Hybrid"]
)

# Job Type
job_type_options = st.sidebar.selectbox(
    "Job Type",
    ["fulltime", "parttime", "internship", "contract"]
)

# Number of results
results_wanted = st.sidebar.slider("Number of results per platform", 10, 100, 20)

# Advanced options
with st.sidebar.expander("Advanced Options"):
    hours_old = st.number_input("Maximum age of job postings (hours)", min_value=1, max_value=168, value=24)
    fetch_description = st.checkbox("Fetch full job descriptions (slower)", value=False)
    easy_apply = st.checkbox("Easy Apply jobs only", value=False)
    
    # New salary range filter
    st.write("Salary Range (Annual)")
    min_salary = st.number_input("Minimum Salary", min_value=0, value=0, step=5000)
    max_salary = st.number_input("Maximum Salary", min_value=0, value=500000, step=5000)
    
    # Experience level filter
    experience_level = st.multiselect(
        "Experience Level",
        ["Entry Level", "Mid Level", "Senior Level", "Executive"],
        default=["Entry Level", "Mid Level"]
    )

# Search button
search_button = st.sidebar.button("Search Jobs", type="primary")

# Main content
if search_button:
    # Show spinner during search
    with st.spinner("Searching for jobs across multiple platforms..."):
        # Create search term from the selected category
        search_term = job_categories[selected_category]
        
        # Generate a google_search_term that includes job category, location, and time filter
        google_search_term = f"{selected_category} jobs near {location} since yesterday"

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
        is_remote = None
        if work_type == "Remote":
            is_remote = True
            params["is_remote"] = True
            google_search_term = f"remote {selected_category} jobs since yesterday"
            search_term = f"remote {search_term}"
        elif work_type == "On-site":
            is_remote = False
            params["is_remote"] = False
        elif work_type == "Hybrid":
            is_remote = None
            search_term += " hybrid"
            
        # Update the search terms in params after modifications
        params["search_term"] = search_term
        params["google_search_term"] = google_search_term
        
        # Add job type parameter
        params["job_type"] = job_type_options
        
        # Add easy apply parameter if selected
        if easy_apply:
            params["easy_apply"] = True

        try:
            # Perform the search
            jobs = scrape_jobs(**params)
            
            # Post-process to ensure remote filter is strictly applied
            if work_type == "Remote":
                jobs = jobs[jobs['is_remote'] == True]
            elif work_type == "On-site":
                jobs = jobs[jobs['is_remote'] != True]
            
            # Display the results
            if len(jobs) > 0:
                st.success(f"Found {len(jobs)} jobs matching your criteria!")
            else:
                st.warning("No jobs found matching your criteria. Try adjusting your filters.")
            
            # Save to CSV for download
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = f"job_search_results_{timestamp}.csv"
            jobs.to_csv(csv_file, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
            
            # Create a download button
            with open(csv_file, "rb") as file:
                btn = st.download_button(
                    label="Download Results as CSV",
                    data=file,
                    file_name=csv_file,
                    mime="text/csv"
                )
            
            # Display the jobs in a nice format
            if not jobs.empty:
                # Filter jobs based on salary range if specified
                if min_salary > 0 or max_salary < 500000:
                    jobs = jobs[
                        (jobs['min_amount'].fillna(0) >= min_salary) &
                        (jobs['max_amount'].fillna(float('inf')) <= max_salary)
                    ]
                
                # Create tabs for different views
                tab1, tab2, tab3 = st.tabs(["Card View", "Table View", "Analytics"])
                
                with tab1:
                    # Enhanced card view of jobs
                    for i, job in jobs.iterrows():
                        with st.container():
                            st.markdown(f"""
                            <div class="job-card">
                                <div class="job-platform">{job.get('site', 'Unknown')}</div>
                                <div class="job-title">{job.get('title', 'No Title')}</div>
                                <div class="job-company">{job.get('company', 'Unknown Company')}</div>
                                <div class="job-location">📍 {job.get('location', 'Location not specified')}</div>
                                <div class="job-details">
                                    <span class="badge">💼 {job.get('job_type', 'Not specified')}</span>
                                    <span class="badge">📅 {job.get('date_posted', 'Date not available')}</span>
                                    <span class="badge">🏠 {'Remote' if job.get('is_remote') else 'On-site'}</span>
                                </div>
                                <div class="job-details salary-range">
                                    💰 {job.get('min_amount', 'Not specified')} - {job.get('max_amount', 'Not specified')} 
                                    {job.get('currency', '')} {job.get('interval', 'per year') if job.get('interval') else 'per year'}
                                </div>
                                <div class="job-description">
                                    {strip_markdown_formatting(job.get('description', '')[:300] + '...' if job.get('description') else 'No description available')}
                                </div>
                                <div class="job-actions">
                                    <a href="{job.get('job_url', '#')}" target="_blank" class="view-job-btn">View Job 👉</a>
                                    <button onclick="saveJob('{i}')" class="save-job-btn">Save Job ⭐</button>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                with tab2:
                    # Table view of jobs
                    columns_to_display = [
                        'title', 'company', 'location', 'job_type', 
                        'is_remote', 'date_posted', 'min_amount', 
                        'max_amount', 'currency', 'interval', 'job_url'
                    ]
                    
                    # Only include columns that exist in the dataframe
                    valid_columns = [col for col in columns_to_display if col in jobs.columns]
                    
                    # Create a clean display dataframe
                    display_df = jobs[valid_columns].copy()
                    
                    # Rename columns for better display
                    column_names = {
                        'title': 'Title',
                        'company': 'Company',
                        'location': 'Location',
                        'job_type': 'Job Type',
                        'is_remote': 'Remote',
                        'date_posted': 'Posted Date',
                        'min_amount': 'Min Salary',
                        'max_amount': 'Max Salary',
                        'currency': 'Currency',
                        'interval': 'Payment Interval',
                        'job_url': 'Job URL'
                    }
                    
                    display_df.rename(columns={col: column_names.get(col, col) for col in valid_columns}, inplace=True)
                    
                    # Make URLs clickable
                    if 'Job URL' in display_df.columns:
                        display_df['Job URL'] = display_df['Job URL'].apply(
                            lambda x: f'<a href="{x}" target="_blank">View Job</a>' if pd.notna(x) else 'No URL'
                        )
                    
                    # Display the table with clickable links
                    st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
                
                with tab3:
                    # Analytics tab
                    st.subheader("Job Search Analytics")
                    
                    try:
                        # Job distribution by platform
                        st.write("### Distribution by Platform")
                        if 'site' in jobs.columns:
                            platform_dist = jobs['site'].value_counts()
                            if not platform_dist.empty:
                                st.bar_chart(platform_dist)
                            else:
                                st.info("No platform distribution data available")
                        
                        # Salary distribution
                        st.write("### Salary Distribution")
                        if 'min_amount' in jobs.columns and 'max_amount' in jobs.columns:
                            # Convert salary columns to numeric, replacing non-numeric values with NaN
                            jobs['min_amount'] = pd.to_numeric(jobs['min_amount'], errors='coerce')
                            jobs['max_amount'] = pd.to_numeric(jobs['max_amount'], errors='coerce')
                            
                            # Calculate mean salary only for rows where both min and max are numeric
                            salary_data = jobs[['min_amount', 'max_amount']].mean(axis=1)
                            salary_data = salary_data.dropna()
                            
                            if not salary_data.empty:
                                # Create histogram using Streamlit's native chart
                                st.bar_chart(salary_data.value_counts(bins=20).sort_index())
                            else:
                                st.info("No salary data available")
                        else:
                            st.info("Salary information not available in the search results")
                        
                        # Remote vs On-site distribution
                        st.write("### Remote vs On-site Distribution")
                        if 'is_remote' in jobs.columns:
                            remote_dist = jobs['is_remote'].value_counts()
                            if not remote_dist.empty:
                                # Convert boolean values to more readable labels
                                remote_dist.index = remote_dist.index.map({True: 'Remote', False: 'On-site', None: 'Not Specified'})
                                st.bar_chart(remote_dist)
                            else:
                                st.info("No remote work distribution data available")
                        else:
                            st.info("Remote work information not available in the search results")
                            
                    except Exception as analytics_error:
                        st.error(f"Error generating analytics: {str(analytics_error)}")
                        st.info("Some analytics may not be available for the current search results")
            
        except Exception as e:
            st.error(f"An error occurred during the job search: {str(e)}")
            st.info("Try adjusting your search parameters or selecting different job boards.")

else:
    # Default welcome message
    st.info("👈 Set your job search criteria in the sidebar and click 'Search Jobs' to begin")
    
    # Show some tips and instructions
    with st.expander("📝 How to use this tool"):
        st.markdown("""
        ### Tips for effective job searching:
        
        1. **Select relevant job boards** - Different platforms may have different jobs
        2. **Choose a job category** - This helps narrow down the results
        3. **Be specific with location** - Enter city and state/country for better results
        4. **Filter by work type** - Choose between remote, on-site, or hybrid positions
        5. **Limit results age** - Fresh postings (24-48 hours) often yield better response rates
        
        ### About this tool:
        
        This interface uses JobSpy to scrape job postings from multiple job boards simultaneously.
        Results are presented in both card and table formats, and can be downloaded as a CSV file.
        
        ### Troubleshooting:
        
        - If you're not getting results, try broadening your search criteria
        - Some job boards may be rate-limited, so try selecting fewer boards if you encounter errors
        - For LinkedIn jobs, consider enabling "Fetch full job descriptions" for more detailed information
        """)

    # Show About information
    with st.expander("About This Tool", expanded=False):
        st.markdown("""
        ## About UnifiedGigs
        
        This interface uses UnifiedGigs to scrape job postings from multiple job boards simultaneously.
        """) 