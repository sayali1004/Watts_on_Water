"""
SCEIN Fellowship Permit/Incentive/Regulation Scraper
Specialized scraper for the uploaded Excel file structure
"""

import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SCEINScraper:
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize scraper with Supabase credentials"""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def read_excel_data(self, excel_path: str) -> List[Dict]:
        """Read all three sheets (Permits, Incentives, Regulations)"""
        all_records = []
        
        for sheet_name in ['Permits', 'Incentives', 'Regulations']:
            logger.info(f"Reading sheet: {sheet_name}")
            
            # Read sheet - skip first 3 rows (empty row, headers, example row)
            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None, skiprows=3)
            
            # Map columns based on actual Excel structure:
            # Column 0 (A): Empty
            # Column 1 (B): Description (long text)
            # Column 5 (F): Parameter name (e.g., "Alameda County — Building permits portal")
            # Column 8 (I): Source URL
            
            for idx, row in df.iterrows():
                def cell(col):
                    v = row.iloc[col] if len(row) > col else None
                    return None if v is None or (isinstance(v, float) and pd.isna(v)) else v

                url = cell(8)
                if not url or not isinstance(url, str) or '[BLANK]' in url:
                    continue
                url = url.strip()
                if not url.startswith('http'):
                    continue

                parameter_name  = cell(5)   # Dataset Name
                description     = cell(1)   # Description
                source_accreditation = cell(7)   # Source Accredidation
                data_age        = cell(9)   # Data Age
                owner_class     = cell(11)  # Owner Class
                item_type       = cell(19)  # Permit/Incentive/Regulation Type
                applicable_system_types = cell(20)  # Applicable System Types
                min_system_size_mw = cell(22)  # Min Applicable System Size [MW]
                max_system_size_mw = cell(23)  # Max Applicable System Size [MW]
                excel_cost      = cell(24)  # Permit/Incentive/Regulation Cost [$]
                # type_ii: update col index below once added to Excel
                type_ii         = None  # placeholder — set to cell(N) when column is added

                county = self._extract_county_from_name(str(parameter_name) if parameter_name else None)

                def to_str(v):
                    return str(v).strip() if v is not None else None

                def to_float(v):
                    try:
                        return float(v) if v is not None else None
                    except (ValueError, TypeError):
                        return None

                record = {
                    'url': url,
                    'data_type': sheet_name.lower().rstrip('s'),
                    'parameter_name': to_str(parameter_name),
                    'description': to_str(description),
                    'source_accreditation': to_str(source_accreditation),
                    'data_age': to_str(data_age),
                    'owner_class': to_str(owner_class),
                    'item_type': to_str(item_type),
                    'applicable_system_types': to_str(applicable_system_types),
                    'type_ii': to_str(type_ii),
                    'min_system_size_mw': to_float(min_system_size_mw),
                    'max_system_size_mw': to_float(max_system_size_mw),
                    'cost': to_float(excel_cost),
                    'county': county,
                    'state': self._extract_state_from_name(str(parameter_name) if parameter_name else None),
                    'excel_row': idx + 4,
                    'excel_sheet': sheet_name,
                }

                all_records.append(record)
        
        logger.info(f"Total records to scrape: {len(all_records)}")
        return all_records
    
    def _extract_county_from_name(self, name: str) -> Optional[str]:
        """Extract county name from parameter name"""
        if not name or pd.isna(name):
            return None
        
        # Pattern: "Alameda County — ..." or "Contra Costa County —"
        match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+County', str(name))
        if match:
            return match.group(1)
        
        return None
    
    def _extract_state_from_name(self, name: str) -> Optional[str]:
        """Extract state from parameter name or description"""
        if not name or pd.isna(name):
            return None
        
        # Look for state codes or "California"
        state_patterns = {
            'CA': ['California', ' CA ', ', CA'],
            'AL': ['Alabama', ' AL ', ', AL'],
            'AR': ['Arkansas', ' AR ', ', AR'],
            'CT': ['Connecticut', ' CT ', ', CT'],
            'US': ['US-Federal', 'United States', 'Federal']
        }
        
        name_str = str(name)
        for code, patterns in state_patterns.items():
            if any(p in name_str for p in patterns):
                return code
        
        return None
    
    def scrape_url(self, url: str, record: Dict) -> Optional[Dict]:
        """
        Scrape a single URL and extract permit/incentive/regulation data
        """
        try:
            logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Base data from Excel
            scraped_data = {
                **record,  # Include all original Excel data
                'scraped_at': datetime.utcnow().isoformat(),
                'status': 'active',  # Default status
                'source_html_title': None,
                'effective_date': None,
                'expiry_date': None,
                'last_updated': None,
                'full_text': None,
                'requirements': None,
                'cost': None,
                'timeframe_days': None
            }
            
            # Extract page title
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                scraped_data['source_html_title'] = title_elem.get_text(strip=True)[:500]
            
            # Extract main content
            page_text = soup.get_text(separator=' ', strip=True)
            scraped_data['full_text'] = page_text[:10000]  # Limit to 10k chars
            
            # Extract dates
            scraped_data['effective_date'] = self._extract_date(page_text, [
                'effective', 'enacted', 'passed', 'signed', 'implemented', 'started'
            ])
            scraped_data['expiry_date'] = self._extract_date(page_text, [
                'expires', 'expiration', 'sunset', 'ends', 'valid until', 'deadline'
            ])
            scraped_data['last_updated'] = self._extract_date(page_text, [
                'updated', 'revised', 'amended', 'modified', 'last modified'
            ])
            
            # Extract requirements (common keywords)
            scraped_data['requirements'] = self._extract_requirements(soup)
            
            # Extract costs/fees
            scraped_data['cost'] = self._extract_cost(page_text)
            
            # Extract timeframe
            scraped_data['timeframe_days'] = self._extract_timeframe(page_text)
            
            # Determine status based on content
            scraped_data['status'] = self._determine_status(page_text, scraped_data['expiry_date'])
            
            return scraped_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                **record,
                'scraped_at': datetime.utcnow().isoformat(),
                'status': 'error',
                'error_message': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {str(e)}")
            return {
                **record,
                'scraped_at': datetime.utcnow().isoformat(),
                'status': 'error',
                'error_message': str(e)
            }
    
    def _extract_date(self, text: str, keywords: List[str]) -> Optional[str]:
        """Extract date from text based on keywords"""
        text_lower = text.lower()
        
        for keyword in keywords:
            # Look for: "keyword: Jan 1, 2024" or "keyword 01/01/2024"
            patterns = [
                rf'{keyword}[:\s]+([A-Z][a-z]+ \d{{1,2}},?\s+\d{{4}})',
                rf'{keyword}[:\s]+(\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}})',
                rf'{keyword}[:\s]+(\d{{4}}-\d{{1,2}}-\d{{1,2}})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        return None
    
    def _extract_requirements(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract key requirements from the page"""
        requirement_keywords = [
            'requirement', 'must', 'shall', 'application', 'document',
            'inspection', 'review', 'approval', 'permit fee', 'timeline'
        ]
        
        # Find paragraphs with requirement keywords
        requirements = []
        for p in soup.find_all(['p', 'li']):
            text = p.get_text(strip=True).lower()
            if any(kw in text for kw in requirement_keywords):
                requirements.append(p.get_text(strip=True))
        
        if requirements:
            # Return first 5 requirements, limited length
            return ' | '.join(requirements[:5])[:2000]
        
        return None
    
    def _extract_cost(self, text: str) -> Optional[float]:
        """Extract cost/fee information"""
        # Look for: $XXX, $X,XXX, fee of $XXX, cost: $XXX
        patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'fee[:\s]+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'cost[:\s]+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Remove commas and convert to float
                    return float(match.group(1).replace(',', ''))
                except:
                    continue
        
        return None
    
    def _extract_timeframe(self, text: str) -> Optional[int]:
        """Extract processing timeframe in days"""
        # Look for: "X days", "X weeks", "X months", "timeline: X days"
        patterns = [
            r'(\d+)\s*days?',
            r'(\d+)\s*weeks?',
            r'(\d+)\s*months?',
            r'timeline[:\s]+(\d+)\s*days?',
            r'processing time[:\s]+(\d+)\s*days?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                
                # Convert to days
                if 'week' in pattern:
                    return value * 7
                elif 'month' in pattern:
                    return value * 30
                else:
                    return value
        
        return None
    
    def _determine_status(self, text: str, expiry_date: Optional[str]) -> str:
        """Determine status based on content"""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ['expired', 'no longer', 'terminated', 'ended']):
            return 'expired'
        elif any(kw in text_lower for kw in ['pending', 'proposed', 'under review', 'draft']):
            return 'pending'
        elif any(kw in text_lower for kw in ['amended', 'revised', 'updated']):
            return 'amended'
        elif expiry_date:
            # Check if expiry date is in the past (simple check)
            if '2020' in expiry_date or '2021' in expiry_date or '2022' in expiry_date:
                return 'expired'
        
        return 'active'
    
    def save_to_supabase(self, data: List[Dict]):
        """Save scraped data to Supabase"""
        if not data:
            logger.warning("No data to save")
            return
        
        logger.info(f"Saving {len(data)} records to Supabase")
        
        # Clean null bytes from all string fields
        def clean_null_bytes(obj):
            """Remove null bytes from strings in dict"""
            if isinstance(obj, dict):
                return {k: clean_null_bytes(v) for k, v in obj.items()}
            elif isinstance(obj, str):
                return obj.replace('\x00', '').replace('\u0000', '')
            elif isinstance(obj, list):
                return [clean_null_bytes(item) for item in obj]
            else:
                return obj
        
        cleaned_data = [clean_null_bytes(record) for record in data]
        
        try:
            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(cleaned_data), batch_size):
                batch = cleaned_data[i:i+batch_size]
                
                # Use the composite unique index for conflict resolution
                result = self.supabase.table('permits_data').upsert(
                    batch,
                    on_conflict='url,data_type,excel_sheet,excel_row'
                ).execute()
                
                logger.info(f"Saved batch {i//batch_size + 1}: {len(batch)} records")
            
            logger.info(f"Successfully saved all {len(cleaned_data)} records")
            
        except Exception as e:
            logger.error(f"Error saving to Supabase: {str(e)}")
            raise
    
    def run(self, excel_path: str, max_urls: Optional[int] = None):
        """Main execution flow"""
        logger.info("=== Starting SCEIN scraper run ===")
        
        # Read Excel
        records = self.read_excel_data(excel_path)
        
        # Limit for testing
        if max_urls:
            records = records[:max_urls]
            logger.info(f"Limited to first {max_urls} URLs for testing")
        
        # Scrape each URL
        all_data = []
        for idx, record in enumerate(records, 1):
            logger.info(f"Processing {idx}/{len(records)}: {record['data_type']} - {record['parameter_name']}")
            
            scraped_data = self.scrape_url(record['url'], record)
            
            if scraped_data:
                all_data.append(scraped_data)
            
            # Rate limiting - be polite
            if idx % 10 == 0:
                logger.info(f"Progress: {idx}/{len(records)} completed")
                time.sleep(2)
            else:
                time.sleep(0.5)
        
        # Save to Supabase
        self.save_to_supabase(all_data)
        
        logger.info(f"=== Scraper run complete: {len(all_data)}/{len(records)} records processed ===")
        return all_data


def main():
    """Main entry point"""
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    EXCEL_PATH = os.getenv('EXCEL_PATH', 'SCEIN Fellowship_Data Tracker Google Sheets_1.xlsx')
    MAX_URLS = os.getenv('MAX_URLS')  # Optional limit for testing
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
    
    max_urls = int(MAX_URLS) if MAX_URLS else None
    
    scraper = SCEINScraper(SUPABASE_URL, SUPABASE_KEY)
    scraper.run(EXCEL_PATH, max_urls=max_urls)


if __name__ == '__main__':
    main()
