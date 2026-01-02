from __future__ import annotations

import re
import json
import requests
import random
import time
from typing import Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from glassdoor.constant import fallback_token, query_template, headers
from glassdoor.util import (
    get_cursor_for_page,
    parse_compensation,
    parse_location,
)
from util import (
    extract_emails_from_text,
    create_logger,
    create_session,
    markdown_converter,
)
from exception import GlassdoorException
from model import (
    JobPost,
    JobResponse,
    DescriptionFormat,
    Scraper,
    ScraperInput,
    Site,
    Location,
    Country,
)

log = create_logger("Glassdoor")


class Glassdoor(Scraper):
    def __init__(
        self, proxies: list[str] | str | None = None, ca_cert: str | None = None
    ):
        """
        Initializes GlassdoorScraper with the Glassdoor job search url
        """
        site = Site(Site.GLASSDOOR)
        super().__init__(site, proxies=proxies, ca_cert=ca_cert)

        self.base_url = None
        self.country = None
        self.session = None
        self.scraper_input = None
        self.jobs_per_page = 30
        self.max_pages = 30
        self.seen_urls = set()
        # Add parameters for rate limiting
        self.min_delay = 10  # Minimum delay between requests in seconds
        self.max_delay = 15  # Maximum delay
        self.max_retries = 3  # Number of retries for failed requests
        self.retry_delay = 30  # Base delay before retry in seconds

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """
        Scrapes Glassdoor for jobs with scraper_input criteria.
        :param scraper_input: Information about job search criteria.
        :return: JobResponse containing a list of jobs.
        """
        self.scraper_input = scraper_input
        # Limit the number of results to avoid excessive requests
        self.scraper_input.results_wanted = min(60, scraper_input.results_wanted)
        
        # Handle None country - default to USA
        if self.scraper_input.country is None:
            log.warning("Glassdoor: country is None, defaulting to USA")
            self.scraper_input.country = Country.USA
        
        try:
            self.base_url = self.scraper_input.country.get_glassdoor_url()
        except (AttributeError, Exception) as e:
            log.error(f"Glassdoor: Error getting base URL: {str(e)}. Defaulting to USA.")
            self.scraper_input.country = Country.USA
            self.base_url = self.scraper_input.country.get_glassdoor_url()

        self.session = create_session(
            proxies=self.proxies, ca_cert=self.ca_cert, has_retry=True
        )
        
        # Try to get CSRF token with retries
        token = self._get_csrf_token_with_retry()
        if token:
            headers["gd-csrf-token"] = token
        else:
            headers["gd-csrf-token"] = fallback_token
            
        self.session.headers.update(headers)

        # Add random user agent to appear more like a real browser
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        self.session.headers.update({"User-Agent": random.choice(user_agents)})

        location_id, location_type = self._get_location(
            scraper_input.location, scraper_input.is_remote
        )
        if location_id is None or location_type is None:
            log.error("Glassdoor: location not parsed, using default values")
            # Set default values instead of returning empty
            location_id = 0
            location_type = "C"  # City type
        
        job_list: list[JobPost] = []
        cursor = None

        range_start = 1 + (scraper_input.offset // self.jobs_per_page)
        tot_pages = (scraper_input.results_wanted // self.jobs_per_page) + 2
        range_end = min(tot_pages, self.max_pages + 1)
        
        for page in range(range_start, range_end):
            log.info(f"search page: {page} / {range_end - 1}")
            
            # Add random delay between requests
            if page > range_start:
                delay = random.uniform(self.min_delay, self.max_delay)
                log.info(f"Waiting {delay:.2f} seconds before next request")
                time.sleep(delay)
                
            try:
                jobs, cursor = self._fetch_jobs_page(
                    scraper_input, location_id, location_type, page, cursor
                )
                job_list.extend(jobs)
                if not jobs or len(job_list) >= scraper_input.results_wanted:
                    job_list = job_list[: scraper_input.results_wanted]
                    break
            except Exception as e:
                log.error(f"Glassdoor: {str(e)}")
                # Don't break immediately, try to continue with next page
                continue
        return JobResponse(jobs=job_list)

    def _fetch_jobs_page(
        self,
        scraper_input: ScraperInput,
        location_id: int,
        location_type: str,
        page_num: int,
        cursor: str | None,
    ) -> Tuple[list[JobPost], str | None]:
        """
        Scrapes a page of Glassdoor for jobs with scraper_input criteria
        """
        jobs = []
        self.scraper_input = scraper_input
        
        for retry in range(self.max_retries):
            try:
                payload = self._add_payload(location_id, location_type, page_num, cursor)
                response = self.session.post(
                    f"{self.base_url}/graph",
                    timeout_seconds=15,
                    data=payload,
                )
                
                if response.status_code == 200:
                    break
                elif response.status_code == 403:
                    log.warning(f"Glassdoor 403 Forbidden response (attempt {retry+1}/{self.max_retries})")
                    if retry < self.max_retries - 1:
                        wait_time = self.retry_delay * (retry + 1)
                        log.info(f"Waiting {wait_time} seconds before retry")
                        time.sleep(wait_time)
                        
                        # Refresh the session on retry
                        self.session = create_session(
                            proxies=self.proxies, ca_cert=self.ca_cert, has_retry=True
                        )
                        token = self._get_csrf_token_with_retry()
                        if token:
                            headers["gd-csrf-token"] = token
                        self.session.headers.update(headers)
                        self.session.headers.update({"User-Agent": random.choice(user_agents)})
                    else:
                        log.error(f"Glassdoor: bad response status code: {response.status_code}")
                        return jobs, None
                else:
                    log.error(f"Glassdoor: bad response status code: {response.status_code}")
                    if retry < self.max_retries - 1:
                        wait_time = self.retry_delay * (retry + 1)
                        log.info(f"Waiting {wait_time} seconds before retry")
                        time.sleep(wait_time)
                    else:
                        return jobs, None
            except Exception as e:
                log.error(f"Glassdoor request error: {str(e)}")
                if retry < self.max_retries - 1:
                    wait_time = self.retry_delay * (retry + 1)
                    log.info(f"Waiting {wait_time} seconds before retry")
                    time.sleep(wait_time)
                else:
                    return jobs, None
        
        try:
            res_json = response.json()[0]
            if "errors" in res_json:
                log.error(f"Error in Glassdoor API response: {res_json['errors']}")
                return jobs, None
        except (ValueError, Exception) as e:
            log.error(f"Error parsing Glassdoor response: {str(e)}")
            return jobs, None

        try:
            jobs_data = res_json["data"]["jobListings"]["jobListings"]
        except KeyError:
            log.error("Unexpected Glassdoor response format")
            return jobs, None

        # Limit concurrent workers to reduce load
        max_workers = min(5, self.jobs_per_page)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_job_data = {
                executor.submit(self._process_job, job): job for job in jobs_data
            }
            for future in as_completed(future_to_job_data):
                try:
                    job_post = future.result()
                    if job_post:
                        jobs.append(job_post)
                except Exception as exc:
                    log.error(f"Glassdoor job processing error: {exc}")

        return jobs, get_cursor_for_page(
            res_json["data"]["jobListings"]["paginationCursors"], page_num + 1
        )

    def _get_csrf_token_with_retry(self):
        """
        Fetches csrf token with retries
        """
        for retry in range(self.max_retries):
            try:
                token = self._get_csrf_token()
                if token:
                    return token
            except Exception as e:
                log.warning(f"Error getting CSRF token (attempt {retry+1}/{self.max_retries}): {str(e)}")
            
            if retry < self.max_retries - 1:
                wait_time = self.retry_delay * (retry + 1)
                log.info(f"Waiting {wait_time} seconds before retry")
                time.sleep(wait_time)
        
        log.warning("Could not get CSRF token, using fallback")
        return None

    def _get_csrf_token(self):
        """
        Fetches csrf token needed for API by visiting a generic page
        """
        res = self.session.get(f"{self.base_url}/Job/computer-science-jobs.htm")
        pattern = r'"token":\s*"([^"]+)"'
        matches = re.findall(pattern, res.text)
        token = None
        if matches:
            token = matches[0]
        return token

    def _process_job(self, job_data):
        """
        Processes a single job and fetches its description.
        """
        try:
            job_id = job_data["jobview"]["job"]["listingId"]
            job_url = f"{self.base_url}job-listing/j?jl={job_id}"
            if job_url in self.seen_urls:
                return None
            self.seen_urls.add(job_url)
            job = job_data["jobview"]
            title = job["job"]["jobTitleText"]
            company_name = job["header"]["employerNameFromSearch"]
            company_id = job_data["jobview"]["header"]["employer"]["id"]
            location_name = job["header"].get("locationName", "")
            location_type = job["header"].get("locationType", "")
            age_in_days = job["header"].get("ageInDays")
            is_remote = False
            location = None
            date_diff = (datetime.now() - timedelta(days=age_in_days)).date() if age_in_days is not None else None
            date_posted = date_diff

            if location_type == "S":
                is_remote = True
            else:
                try:
                    location = parse_location(location_name)
                    if location is None:
                        # Fallback if parsing fails
                        city = location_name.split(',')[0].strip() if ',' in location_name else location_name
                        state = location_name.split(',')[1].strip() if ',' in location_name and len(location_name.split(',')) > 1 else None
                        location = Location(city=city, state=state, country=self.scraper_input.country)
                except Exception as e:
                    log.warning(f"Location parsing error: {str(e)} for location '{location_name}'")
                    # Create a basic location from the raw string
                    location = Location(city=location_name, country=self.scraper_input.country)

            compensation = parse_compensation(job["header"])
            try:
                description = self._fetch_job_description(job_id)
            except Exception as e:
                log.warning(f"Error fetching job description: {str(e)}")
                description = None
                
            company_url = f"{self.base_url}Overview/W-EI_IE{company_id}.htm" if company_id else None
            company_logo = job_data["jobview"].get("overview", {}).get("squareLogoUrl", None)
            listing_type = job_data["jobview"].get("header", {}).get("adOrderSponsorshipLevel", "").lower()
            
            return JobPost(
                id=f"gd-{job_id}",
                title=title,
                company_url=company_url,
                company_name=company_name,
                date_posted=date_posted,
                job_url=job_url,
                location=location,
                compensation=compensation,
                is_remote=is_remote,
                description=description,
                emails=extract_emails_from_text(description) if description else None,
                company_logo=company_logo,
                listing_type=listing_type,
            )
        except Exception as e:
            log.error(f"Error processing Glassdoor job: {str(e)}")
            return None

    def _fetch_job_description(self, job_id):
        """
        Fetches the job description for a single job ID.
        """
        url = f"{self.base_url}/graph"
        body = [
            {
                "operationName": "JobDetailQuery",
                "variables": {
                    "jl": job_id,
                    "queryString": "q",
                    "pageTypeEnum": "SERP",
                },
                "query": """
                query JobDetailQuery($jl: Long!, $queryString: String, $pageTypeEnum: PageTypeEnum) {
                    jobview: jobView(
                        listingId: $jl
                        contextHolder: {queryString: $queryString, pageTypeEnum: $pageTypeEnum}
                    ) {
                        job {
                            description
                            __typename
                        }
                        __typename
                    }
                }
                """,
            }
        ]
        res = requests.post(url, json=body, headers=headers)
        if res.status_code != 200:
            return None
        data = res.json()[0]
        desc = data["data"]["jobview"]["job"]["description"]
        if self.scraper_input.description_format == DescriptionFormat.MARKDOWN:
            desc = markdown_converter(desc)
        return desc

    def _get_location(self, location: str, is_remote: bool) -> (int, str):
        if not location or is_remote:
            return "11047", "STATE"  # remote options
        url = f"{self.base_url}/findPopularLocationAjax.htm?maxLocationsToReturn=10&term={location}"
        res = self.session.get(url)
        if res.status_code != 200:
            if res.status_code == 429:
                err = f"429 Response - Blocked by Glassdoor for too many requests"
                log.error(err)
                return None, None
            else:
                err = f"Glassdoor response status code {res.status_code}"
                err += f" - {res.text}"
                log.error(f"Glassdoor response status code {res.status_code}")
                return None, None
        items = res.json()

        if not items:
            raise ValueError(f"Location '{location}' not found on Glassdoor")
        location_type = items[0]["locationType"]
        if location_type == "C":
            location_type = "CITY"
        elif location_type == "S":
            location_type = "STATE"
        elif location_type == "N":
            location_type = "COUNTRY"
        return int(items[0]["locationId"]), location_type

    def _add_payload(
        self,
        location_id: int,
        location_type: str,
        page_num: int,
        cursor: str | None = None,
    ) -> str:
        fromage = None
        if self.scraper_input.hours_old:
            fromage = max(self.scraper_input.hours_old // 24, 1)
        filter_params = []
        if self.scraper_input.easy_apply:
            filter_params.append({"filterKey": "applicationType", "values": "1"})
        if fromage:
            filter_params.append({"filterKey": "fromAge", "values": str(fromage)})
        payload = {
            "operationName": "JobSearchResultsQuery",
            "variables": {
                "excludeJobListingIds": [],
                "filterParams": filter_params,
                "keyword": self.scraper_input.search_term,
                "numJobsToShow": 30,
                "locationType": location_type,
                "locationId": int(location_id),
                "parameterUrlInput": f"IL.0,12_I{location_type}{location_id}",
                "pageNumber": page_num,
                "pageCursor": cursor,
                "fromage": fromage,
                "sort": "date",
            },
            "query": query_template,
        }
        if self.scraper_input.job_type:
            payload["variables"]["filterParams"].append(
                {"filterKey": "jobType", "values": self.scraper_input.job_type.value[0]}
            )
        return json.dumps([payload])
