"""
Website Brand Analyzer using OpenAI API
Analyzes any website URL and extracts comprehensive brand information including colors and typography
Automatically opens the moodboard in browser after analysis

Note: GPT-5 is not yet publicly available. Using GPT-4o (latest model).
When GPT-5 releases, change model="gpt-4o" to model="gpt-5"

Requirements:
pip install openai requests beautifulsoup4 python-dotenv
"""

import os
import json
import requests
import webbrowser
import http.server
import socketserver
import threading
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Dict
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BrandAnalyzer:
    """Analyzes websites using OpenAI to extract brand information"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize analyzer with OpenAI API key
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY environment variable)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        self.client = OpenAI(api_key=self.api_key)
        # Change to "gpt-5" when available
        self.model = "gpt-5.2"
    
    def get_root_domain(self, url: str) -> str:
        """Extract root domain from any URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def fetch_website(self, url: str) -> Dict[str, str]:
        """
        Fetch website content from both the provided URL and root domain
        
        Args:
            url: Any URL on the website
            
        Returns:
            Dictionary with page and root content
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        result = {
            'url': url,
            'root_url': self.get_root_domain(url),
            'page_content': '',
            'root_content': '',
            'raw_html': ''
        }
        
        try:
            # Fetch the provided URL
            print(f"📥 Fetching: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Store raw HTML for color/typography analysis
            result['raw_html'] = response.text[:20000]
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove scripts and styles
            for element in soup(["script", "style", "nav", "footer"]):
                element.decompose()
            
            result['page_content'] = soup.get_text(separator=' ', strip=True)[:12000]
            
            # Fetch root domain if different
            root_url = result['root_url']
            if root_url != url:
                print(f"📥 Fetching root: {root_url}")
                try:
                    root_response = requests.get(root_url, headers=headers, timeout=15)
                    root_response.raise_for_status()
                    root_soup = BeautifulSoup(root_response.text, 'html.parser')
                    
                    for element in root_soup(["script", "style", "nav", "footer"]):
                        element.decompose()
                    
                    result['root_content'] = root_soup.get_text(separator=' ', strip=True)[:12000]
                except Exception as e:
                    result['root_content'] = f"Could not fetch root: {str(e)}"
            else:
                result['root_content'] = "Same as provided URL"
            
            return result
            
        except Exception as e:
            raise Exception(f"Failed to fetch website: {str(e)}")
    
    def analyze(self, url: str) -> Dict:
        """
        Analyze website and extract brand information
        
        Args:
            url: Website URL (can be any page, not just homepage)
            
        Returns:
            Dictionary with comprehensive brand analysis
        """
        print(f"\n{'='*60}")
        print(f"🎯 Starting Brand Analysis")
        print(f"{'='*60}")
        print(f"🌐 URL: {url}")
        print(f"🤖 Model: {self.model}")
        print(f"{'='*60}\n")
        
        # Fetch website content
        content = self.fetch_website(url)
        
        # Create analysis prompt
        prompt = f"""
You are a professional brand analyst. Analyze this website to extract comprehensive brand information.

**CRITICAL**: Even if the URL is an internal page (e.g., /about, /products/item), analyze the ENTIRE WEBSITE and BRAND, not just this specific page.

**Website Data:**
- Provided URL: {content['url']}
- Root Domain: {content['root_url']}

**Content from provided page:**
{content['page_content'][:8000]}

**Content from homepage/root:**
{content['root_content'][:8000]}

**HTML Sample (for color/typography analysis):**
{content['raw_html'][:3000]}

---

**Extract the following about the OVERALL BRAND (not just this page):**

1. **Business Overview & Positioning**
   - What does this company/brand do?
   - Market positioning statement
   - Industry sector

2. **Direct Competitors**
   - Local competitors (in their primary market/country)
   - International competitors
   - List 3-5 competitors in each category

3. **Competitive Advantages**
   - List up to 5 key advantages that set them apart
   - What makes them unique?

4. **Customer Demographics**
   - Target age range
   - Income level
   - Geographic markets
   - Lifestyle/interests
   - Psychographic profile

5. **Most Popular Products & Services**
   - Main products/services
   - Best sellers or featured offerings
   - Product categories

6. **Emerging Growth Area**
   - New initiatives
   - Expanding product lines
   - Strategic focus areas

7. **Why Customers Choose This Brand**
   - Rational benefits (practical reasons)
   - Emotional benefits (feelings/emotional value)

8. **The Brand Story**
   - Origin/founding (if mentioned)
   - Mission and values
   - Brand evolution

9. **Brand Personality**
   - Key personality traits
   - Brand voice/tone
   - How they communicate

10. **Typography (Font Styles) - REQUIRED**
   - **CRITICAL**: Extract the typography information from the website's HTML/CSS
   - Primary font: The main font family used for headings/titles you find in the website, which they use for headings (don't fetch multiple variants, just the main one) 
   - Secondary font: The font used for body text/paragraphs you find in the website, which they use for main content (don't fetch multiple variants, just the main one)
   - Tertiary font: Additional font if used for accents or special sections (don't fetch multiple variants, just the main one)
   - Analyze CSS styles, font-family declarations, or deduce from visual appearance in the HTML sample
   - Use web-safe fallbacks if exact font unknown
   - **MUST be included in the JSON response**

11. **Color Palette (Brand Colors) - REQUIRED**
   - **CRITICAL**: Extract the color palette from the website's HTML/CSS
   - Primary color: Main brand color in HEX format (e.g., "#FF5733") - MUST be a valid hex code
   - Secondary color: Secondary accent color in HEX (e.g., "#3498DB") - MUST be a valid hex code
   - Tertiary color: Third color or accent in HEX (e.g., "#2ECC71") - MUST be a valid hex code
   - Extract from CSS color values, background colors, headers, buttons, or prominent visual elements in the HTML
   - Look for hex codes (#RRGGBB), rgb() values, or named colors in the HTML/CSS
   - If exact colors unclear, estimate based on visual dominance and convert to hex format
   - **MUST be included in the JSON response with valid hex codes**

---

**IMPORTANT**: Return ONLY a valid JSON object. No markdown formatting, no code blocks, no extra text.

Use this exact structure:

{{
  "brand_name": "Brand/Company Name",
  "industry": "Industry/sector",
  "market_positioning": "How they position themselves in the market",
  "competitors": {{
    "local": ["Local Competitor 1", "Local Competitor 2", "Local Competitor 3"],
    "international": ["International Competitor 1", "International Competitor 2", "International Competitor 3"]
  }},
  "competitive_advantages": [
    "Advantage 1",
    "Advantage 2",
    "Advantage 3",
    "Advantage 4",
    "Advantage 5"
  ],
  "customer_demographics": {{
    "age_range": "Target age range",
    "income_level": "Target income level",
    "geographic_focus": "Primary geographic markets",
    "lifestyle": "Lifestyle characteristics",
    "psychographic": "Values, interests, attitudes"
  }},
  "popular_products_services": [
    "Product/Service 1",
    "Product/Service 2",
    "Product/Service 3"
  ],
  "emerging_growth_area": "Description of new/emerging focus areas",
  "why_customers_choose": {{
    "rational_benefits": [
      "Practical benefit 1",
      "Practical benefit 2",
      "Practical benefit 3"
    ],
    "emotional_benefits": [
      "Emotional benefit 1",
      "Emotional benefit 2",
      "Emotional benefit 3"
    ]
  }},
  "brand_story": "Origin, mission, evolution of the brand",
  "brand_personality": [
    "Personality trait 1",
    "Personality trait 2",
    "Personality trait 3"
  ],
  "typography": {{
    "primary": "Primary font family with fallbacks (e.g., 'Montserrat', sans-serif)",
    "secondary": "Secondary font family with fallbacks (e.g., 'Open Sans', sans-serif)",
    "tertiary": "Tertiary font family with fallbacks (e.g., 'Georgia', serif)"
  }},
  "color_palette": {{
    "primary": "#HEX color code for primary brand color",
    "secondary": "#HEX color code for secondary color",
    "tertiary": "#HEX color code for tertiary/accent color"
  }}
}}
"""
        
        # Call OpenAI API
        print("🤖 Sending to OpenAI for analysis...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert brand analyst with expertise in visual design and web development. You MUST extract comprehensive brand information from website content, with special attention to typography (primary, secondary, tertiary fonts) and color palette (primary, secondary, tertiary colors in HEX format). Analyze the HTML/CSS provided to identify exact font families and color hex codes. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                max_completion_tokens=4000
            )
            
            # Extract response
            result_text = response.choices[0].message.content.strip()
            
            # Clean up response (remove code blocks if present)
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            # Parse JSON
            analysis = json.loads(result_text)
            
            # Add metadata
            analysis['_metadata'] = {
                'analyzed_url': url,
                'root_domain': content['root_url'],
                'model_used': self.model,
                'timestamp': None  # Could add timestamp if needed
            }
            
            print("✅ Analysis complete!\n")
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response")
            print(f"Raw response: {result_text[:500]}...")
            raise Exception(f"Invalid JSON response from OpenAI: {str(e)}")
        
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def save_analysis(self, analysis_data: Dict, output_file: str = "brand_analysis.json") -> Path:
        """
        Save analysis to JSON file only (no browser). For use by web backend.
        
        Args:
            analysis_data: The brand analysis dictionary
            output_file: Name of the JSON file to save (default: brand_analysis.json)
            
        Returns:
            Path to the saved JSON file
        """
        script_dir = Path(__file__).parent
        json_path = script_dir / output_file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        return json_path
    
    def save_and_open_moodboard(self, analysis_data: Dict, output_file: str = "brand_analysis.json"):
        """
        Save analysis to JSON file and open moodboard in browser using local HTTP server
        
        Args:
            analysis_data: The brand analysis dictionary
            output_file: Name of the JSON file to save (default: brand_analysis.json)
        """
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        
        # Save JSON file
        json_path = script_dir / output_file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Analysis saved to: {json_path}")
        
        # Check if moodboard HTML exists
        moodboard_path = script_dir / "moodboard.html"
        
        if not moodboard_path.exists():
            print(f"⚠️  Warning: moodboard.html not found at {moodboard_path}")
            print("   Please make sure moodboard.html is in the same directory as this script.")
            return
        
        # Start a local HTTP server to avoid CORS issues
        PORT = 8000
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(script_dir), **kwargs)
            
            def log_message(self, format, *args):
                # Suppress server logs
                pass
        
        # Try to find an available port
        for port in range(8000, 8010):
            try:
                server = socketserver.TCPServer(("", port), Handler)
                PORT = port
                break
            except OSError:
                continue
        
        # Start server in a separate thread
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        # Open moodboard in default browser
        print(f"🌐 Starting local server and opening moodboard in browser...")
        
        url = f'http://localhost:{PORT}/moodboard.html'
        webbrowser.open(url)
        
        print(f"✅ Moodboard opened: {url}")
        print(f"💡 Server running on port {PORT}. Press Ctrl+C to stop the server.")
        print(f"   The moodboard will automatically load data from {output_file}\n")


# ============================================
# USAGE EXAMPLES
# ============================================

def example_basic_usage():
    """Basic usage example with automatic moodboard opening"""
    
    # Initialize analyzer
    analyzer = BrandAnalyzer()  # Uses OPENAI_API_KEY from environment
    
    # Analyze a website (can be any page on the site)
    result = analyzer.analyze("https://www.ndure.com/")
    
    # Save and open moodboard automatically
    analyzer.save_and_open_moodboard(result)
    
    return result


def example_with_custom_output():
    """Example with custom output filename"""
    
    analyzer = BrandAnalyzer()
    result = analyzer.analyze("https://www.nike.com")
    
    # Save with custom filename
    analyzer.save_and_open_moodboard(result, output_file="nike-brand-data.json")
    
    return result


def example_multiple_brands():
    """Example analyzing multiple brands and opening each"""
    
    analyzer = BrandAnalyzer()
    
    urls = [
        "https://www.rolex.com",
        "https://www.nike.com",
        "https://www.apple.com"
    ]
    
    for url in urls:
        try:
            print(f"\n{'='*60}")
            result = analyzer.analyze(url)
            
            # Create filename from brand name
            brand_slug = result['brand_name'].lower().replace(' ', '-')
            filename = f"{brand_slug}-brand-data.json"
            
            analyzer.save_and_open_moodboard(result, output_file=filename)
            print(f"✅ Completed: {result['brand_name']}")
            
            # Optional: wait for user before continuing to next
            input("\nPress Enter to analyze next brand...")
            
        except Exception as e:
            print(f"❌ Failed {url}: {str(e)}")


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         Website Brand Analyzer + Moodboard Generator       ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    try:
        # Initialize analyzer
        analyzer = BrandAnalyzer()
        
        # Get URL from user or use default
        url = input("🌐 Enter website URL (or press Enter for demo): ").strip()
        
        if not url:
            url = "https://en-pk.svestonwatches.com/"
            print(f"   Using demo URL: {url}")
        
        # Analyze the website
        result = analyzer.analyze(url)
        
        # Display key information
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULTS")
        print("="*60)
        print(f"\n🏢 Brand: {result['brand_name']}")
        print(f"🏭 Industry: {result['industry']}")
        print(f"\n📍 Market Positioning:")
        print(f"   {result['market_positioning']}")
        
        print(f"\n🎨 Color Palette:")
        colors = result.get('color_palette', {})
        print(f"   Primary: {colors.get('primary', 'N/A')}")
        print(f"   Secondary: {colors.get('secondary', 'N/A')}")
        print(f"   Tertiary: {colors.get('tertiary', 'N/A')}")
        
        print(f"\n🔤 Typography:")
        typography = result.get('typography', {})
        print(f"   Primary: {typography.get('primary', 'N/A')}")
        print(f"   Secondary: {typography.get('secondary', 'N/A')}")
        print(f"   Tertiary: {typography.get('tertiary', 'N/A')}")
        
        print(f"\n🏆 Competitive Advantages:")
        for i, adv in enumerate(result['competitive_advantages'][:3], 1):
            print(f"   {i}. {adv}")
        
        print(f"\n👥 Customer Demographics:")
        demo = result['customer_demographics']
        print(f"   Age: {demo['age_range']}")
        print(f"   Income: {demo['income_level']}")
        
        print(f"\n🎭 Brand Personality:")
        for trait in result['brand_personality']:
            print(f"   • {trait}")
        
        print("\n" + "="*60)
        
        # Save and open moodboard
        analyzer.save_and_open_moodboard(result)
        
        print("="*60)
        print("✨ Done! Check your browser for the moodboard.")
        print("="*60)
        print("\n💡 The local server is running. Keep this window open to view the moodboard.")
        print("   Press Ctrl+C to stop the server when you're done.\n")
        
        # Keep the script running so the server stays alive
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped. Goodbye!\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        print("Make sure you have:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Installed required packages: pip install openai requests beautifulsoup4 python-dotenv")
        print("3. moodboard.html in the same directory as this script")