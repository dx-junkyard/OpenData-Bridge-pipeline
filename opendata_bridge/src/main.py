import argparse
import sys
import os
import json
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from src.utils import LLMHtmlConverter

# Add the project root to python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_crawl(target, settings_overrides=None):
    """
    Runs the Scrapy spider for the given target.
    Enables JOBDIR for resume capability.
    """
    logger.info(f"Starting crawl for target: {target}")

    # Get standard project settings
    settings = get_project_settings()

    # Configure Job Directory for resuming
    job_dir = f"crawls/{target}"
    settings.set('JOBDIR', job_dir, priority='cmdline')

    # Configure Output
    output_file = f"output/{target}.jsonl"
    settings.set('FEEDS', {
        output_file: {
            'format': 'jsonl',
            'encoding': 'utf-8',
            'overwrite': False # Append to existing file if resuming
        }
    }, priority='cmdline')

    # Apply any additional overrides
    if settings_overrides:
        for key, value in settings_overrides.items():
            settings.set(key, value, priority='cmdline')

    process = CrawlerProcess(settings)
    process.crawl(target)
    process.start()

def run_enrich(target):
    """
    Reads the scraped JSONL file and applies LLM enrichment.
    Currently specifically implemented for Kokubunji (13214).
    """
    logger.info(f"Starting enrichment for target: {target}")

    input_file = f"output/{target}.jsonl"
    output_file = f"output/{target}_enriched.jsonl"

    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}. Run 'crawl' step first.")
        return

    # Initialize LLM Converter
    # We load config from env vars here to keep it simple, mirroring settings.py
    llm_url = os.getenv('OPENAI_BASE_URL')
    llm_api_key = os.getenv('OPENAI_API_KEY')
    llm_model = os.getenv('LLM_MODEL', 'gpt-4-turbo-preview')

    # Load prompt for Kokubunji
    prompt_path = os.path.join(os.path.dirname(__file__), 'spiders', 'kokubunji_prompt.txt')
    if target == 'kokubunji' and os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            llm_prompt = f.read()
    else:
        llm_prompt = "" # Fallback or other targets might not need it

    converter = LLMHtmlConverter(llm_url, llm_api_key, llm_model, llm_prompt)

    processed_count = 0
    with open(input_file, 'r', encoding='utf-8') as fin, \
         open(output_file, 'w', encoding='utf-8') as fout:

        for line in fin:
            try:
                item = json.loads(line)

                # Logic for Kokubunji Enrichment
                if target == 'kokubunji' and 'extended_attributes' not in item:
                    # The spider stored raw HTML in 'body'
                    raw_html = item.get('body', '')
                    if raw_html:
                        logger.info(f"Enriching item: {item.get('url')}")
                        structured_data = converter.convert_html_to_json(raw_html)

                        if structured_data:
                            # The LLM returns a list of services found in the HTML
                            # Since we have one source item, we might need to explode it or just store the list
                            # For simplicity and schema compliance, we store the list in extended_attributes
                            item['extended_attributes'] = structured_data
                            # Optionally, update title/body from the first extracted service if desired
                            # item['title'] = structured_data[0].get('タイトル', item['title'])
                        else:
                             logger.warning(f"LLM returned no data for {item.get('url')}")

                # Write the (possibly enriched) item to output
                fout.write(json.dumps(item, ensure_ascii=False) + '\n')
                processed_count += 1

            except json.JSONDecodeError:
                logger.error(f"Skipping invalid JSON line")
                continue

    logger.info(f"Enrichment complete. Processed {processed_count} items. Saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Opendata Bridge Pipeline Runner")
    parser.add_argument('--target', required=True, help="Target municipality spider name (e.g., edogawa, kokubunji)")
    parser.add_argument('--step', choices=['crawl', 'enrich', 'all'], default='all', help="Step to execute")

    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)

    # Check for CLOSESPIDER_PAGECOUNT env var for testing
    settings_overrides = {}
    page_count = os.getenv('CLOSESPIDER_PAGECOUNT')
    if page_count:
        settings_overrides['CLOSESPIDER_PAGECOUNT'] = page_count

    if args.step in ['crawl', 'all']:
        run_crawl(args.target, settings_overrides)

    if args.step in ['enrich', 'all']:
        run_enrich(args.target)

if __name__ == "__main__":
    main()
