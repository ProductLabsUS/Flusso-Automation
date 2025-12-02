"""
Freshdesk API Integration Service
Handles ticket fetching, note creation, and ticket updates
"""

import requests
import logging
import time
from typing import List, Dict, Optional, Any
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class FreshdeskService:
    """
    Service for interacting with Freshdesk API
    Implements ticket retrieval, note creation, and ticket updates
    """
    
    def __init__(self, 
                 domain: str,
                 api_key: str,
                 wait_after_note: int = 2,
                 wait_after_update: int = 2,
                 timeout: int = 30):
        """
        Initialize Freshdesk service
        
        Args:
            domain: Freshdesk domain (e.g., 'company.freshdesk.com')
            api_key: Freshdesk API key
            wait_after_note: Seconds to wait after adding note
            wait_after_update: Seconds to wait after updating ticket
            timeout: Request timeout in seconds
            
        Raises:
            ValueError: If domain or API key is invalid
        """
        if not domain or not isinstance(domain, str):
            raise ValueError("Invalid Freshdesk domain")
        if not api_key or not isinstance(api_key, str):
            raise ValueError("Invalid Freshdesk API key")
        
        self.domain = domain.replace('https://', '').replace('http://', '').strip()
        self.api_key = api_key.strip()
        self.base_url = f"https://{self.domain}/api/v2"
        self.auth = HTTPBasicAuth(self.api_key, 'X')
        self.wait_after_note = max(0, wait_after_note)
        self.wait_after_update = max(0, wait_after_update)
        self.timeout = max(5, min(timeout, 120))  # Between 5-120 seconds
        
        self.headers = {
            'Content-Type': 'application/json'
        }
        
        logger.info(f"✅ Initialized Freshdesk service for: {self.domain}")
    
    def fetch_open_tickets(self, 
                          status: int = 2,
                          max_tickets: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch open tickets from Freshdesk
        
        Args:
            status: Ticket status (2=Open, 3=Pending, 4=Resolved, 5=Closed)
            max_tickets: Maximum number of tickets to fetch (None = all)
            
        Returns:
            List of ticket dictionaries
        """
        logger.info(f"🔍 Fetching tickets with status={status}...")
        
        try:
            # Use Freshdesk search API
            search_url = f"{self.base_url}/search/tickets"
            query = f'"status:{status}"'
            
            params = {
                'query': query
            }
            
            response = requests.get(
                search_url,
                auth=self.auth,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract tickets from results
            tickets = data.get('results', [])
            
            # Limit if specified
            if max_tickets:
                tickets = tickets[:max_tickets]
            
            logger.info(f"✅ Fetched {len(tickets)} ticket(s)")
            
            return tickets
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching tickets: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"   Response: {e.response.text}")
            raise
    
    def extract_ticket_data(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize ticket data with validation
        
        Args:
            ticket: Raw ticket data from Freshdesk
            
        Returns:
            Normalized ticket dictionary
            
        Raises:
            ValueError: If ticket data is invalid or missing required fields
        """
        if not ticket:
            raise ValueError("Ticket data is empty")
        
        ticket_id = ticket.get('id')
        if not ticket_id:
            raise ValueError("Ticket ID is missing")
        
        # Sanitize and validate text fields
        subject = str(ticket.get('subject', ''))[:500]  # Limit length
        description = ticket.get('description_text') or ticket.get('description', '')
        description = str(description)[:10000]  # Limit description length
        
        # Validate requester data
        requester = ticket.get('requester', {})
        if not isinstance(requester, dict):
            requester = {}
        
        return {
            'ticket_id': ticket_id,
            'subject': subject.strip(),
            'description': description.strip(),
            'status': ticket.get('status'),
            'priority': ticket.get('priority'),
            'requester_name': str(requester.get('name', 'Customer'))[:100],
            'requester_email': str(requester.get('email', ''))[:100],
            'created_at': ticket.get('created_at'),
            'updated_at': ticket.get('updated_at'),
            'tags': ticket.get('tags', []) if isinstance(ticket.get('tags'), list) else [],
            'custom_fields': ticket.get('custom_fields', {}) if isinstance(ticket.get('custom_fields'), dict) else {}
        }
    
    def add_private_note(self, 
                        ticket_id: int,
                        note_body: str,
                        wait_after: bool = True) -> bool:
        """
        Add a private note to a ticket
        
        Args:
            ticket_id: Ticket ID
            note_body: Content of the note (HTML supported)
            wait_after: Whether to wait after adding note
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"📝 Adding private note to Ticket #{ticket_id}...")
        
        try:
            url = f"{self.base_url}/tickets/{ticket_id}/notes"
            
            payload = {
                'body': note_body,
                'private': True
            }
            
            response = requests.post(
                url,
                auth=self.auth,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            logger.info(f"✅ Note added to Ticket #{ticket_id}")
            
            # Rate limiting
            if wait_after:
                logger.debug(f"   Waiting {self.wait_after_note}s (rate limiting)...")
                time.sleep(self.wait_after_note)
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error adding note to Ticket #{ticket_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"   Response: {e.response.text}")
            return False
    
    def update_ticket(self,
                     ticket_id: int,
                     tags: Optional[List[str]] = None,
                     custom_fields: Optional[Dict[str, Any]] = None,
                     status: Optional[int] = None,
                     wait_after: bool = True) -> bool:
        """
        Update ticket properties
        
        Args:
            ticket_id: Ticket ID
            tags: List of tags to add
            custom_fields: Custom fields to update
            status: New status (optional)
            wait_after: Whether to wait after update
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"🔄 Updating Ticket #{ticket_id}...")
        
        try:
            url = f"{self.base_url}/tickets/{ticket_id}"
            
            payload = {}
            
            if tags is not None:
                payload['tags'] = tags
                logger.debug(f"   Adding tags: {tags}")
            
            if custom_fields is not None:
                payload['custom_fields'] = custom_fields
                logger.debug(f"   Updating custom fields: {custom_fields}")
            
            if status is not None:
                payload['status'] = status
                logger.debug(f"   Changing status to: {status}")
            
            if not payload:
                logger.warning(f"⚠️  No updates specified for Ticket #{ticket_id}")
                return True
            
            response = requests.put(
                url,
                auth=self.auth,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            logger.info(f"✅ Ticket #{ticket_id} updated")
            
            # Rate limiting
            if wait_after:
                logger.debug(f"   Waiting {self.wait_after_update}s (rate limiting)...")
                time.sleep(self.wait_after_update)
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error updating Ticket #{ticket_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"   Response: {e.response.text}")
            return False
    
    def format_ai_note(self,
                      ai_response: str,
                      has_grounding: bool,
                      ticket_id: int,
                      customer_name: str) -> str:
        """
        Format AI response as a Freshdesk note
        
        Args:
            ai_response: The AI-generated response
            has_grounding: Whether response is grounded in docs
            ticket_id: Ticket ID
            customer_name: Customer name
            
        Returns:
            Formatted note body (HTML)
        """
        grounding_note = (
            "📚 Response grounded in Product Labs documentation" 
            if has_grounding 
            else "ℹ️ General response (no specific documentation cited)"
        )
        
        note = f"""🤖 <strong>AI-GENERATED SUGGESTED RESPONSE</strong><br><br>

{ai_response}<br><br>

<hr>
{grounding_note}<br><br>

<hr>
<em>This response was generated by Google Gemini 2.5 Flash AI with File Search. Please review before sending to customer.</em>"""
        
        return note
    
    def check_if_already_processed(self, ticket: Dict[str, Any], 
                                   ai_tag: str = "ai-reviewed") -> bool:
        """
        Check if ticket has already been processed by AI
        
        Args:
            ticket: Ticket data
            ai_tag: Tag that indicates AI processing
            
        Returns:
            True if already processed, False otherwise
        """
        tags = ticket.get('tags', [])
        return ai_tag in tags
    
    def get_ticket_by_id(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific ticket by ID
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket data or None if not found
        """
        try:
            url = f"{self.base_url}/tickets/{ticket_id}"
            
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching Ticket #{ticket_id}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'domain': self.domain,
            'base_url': self.base_url,
            'wait_after_note': self.wait_after_note,
            'wait_after_update': self.wait_after_update
        }


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    import sys
    import os
    from dotenv import load_dotenv
    
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    load_dotenv()
    
    # Test configuration
    domain = os.getenv("FRESHDESK_DOMAIN", "productlabs-support.freshdesk.com")
    api_key = os.getenv("FRESHDESK_API_KEY")
    
    if not api_key:
        print("❌ FRESHDESK_API_KEY not set in environment")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("Testing Freshdesk Service")
    print("="*70 + "\n")
    
    try:
        # Initialize service
        freshdesk = FreshdeskService(
            domain=domain,
            api_key=api_key,
            wait_after_note=1,
            wait_after_update=1
        )
        
        print("✅ Service initialized successfully\n")
        print("Stats:", freshdesk.get_stats())
        print("\n" + "="*70 + "\n")
        
        # Test: Fetch open tickets
        print("Testing: Fetch Open Tickets")
        print("-" * 70)
        tickets = freshdesk.fetch_open_tickets(status=2, max_tickets=3)
        
        if tickets:
            print(f"✅ Found {len(tickets)} ticket(s)\n")
            
            for ticket in tickets:
                ticket_data = freshdesk.extract_ticket_data(ticket)
                print(f"Ticket #{ticket_data['ticket_id']}")
                print(f"  Subject: {ticket_data['subject'][:50]}...")
                print(f"  Requester: {ticket_data['requester_name']}")
                print(f"  Status: {ticket_data['status']}")
                print(f"  Tags: {ticket_data['tags']}")
                print()
        else:
            print("ℹ️  No open tickets found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
