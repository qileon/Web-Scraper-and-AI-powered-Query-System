import requests # allows sending https requests to websites
import warnings # helps manage and suppress warning messages that might clutter the output
from bs4 import BeautifulSoup # for parsing and extracting information from html and xml documents
import google.generativeai as genai # google's generative ai library for accessing ai models like gemini
import os # provides ways to interact with the operating system, useful for environment settings
import tkinter as tk # standard python library for creating graphical user interfaces (gui)
from tkinter import scrolledtext, messagebox, ttk # additional tkinter modules for creating scrollable text areas, message boxes, and styled widgets
from typing import List, Tuple # helps define the types of variables and function inputs/outputs for better code clarity and error checking

class WebsiteScraper:
    def __init__(self, api_key: str):
        # ignore warning messages to keep the output clean
        warnings.filterwarnings("ignore", category=UserWarning)
        # reduce unnecessary logging messages
        os.environ["GRPC_VERBOSITY"] = "ERROR"
        os.environ["GLOG_minloglevel"] = "2"
        
        # set up google's gemini ai model using the provided api key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def scrape_website(self, url: str) -> str:
        try:
            # send a request to the website and get its content
            response = requests.get(url, timeout=10)
            # make sure the request was successful
            response.raise_for_status()
            
            # use beautiful soup to parse the html content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # extract all paragraph texts from the webpage
            paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
            
            # extract all headings (h1, h2, h3) from the webpage
            headings = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3']) if h.get_text(strip=True)]
            
            # combine headings and paragraphs into one text
            return "\n".join(headings + paragraphs)
        except requests.RequestException as e:
            # print an error message if something goes wrong while scraping
            print(f"Error scraping {url}: {e}")
            return ""

    def search_with_gemini(self, query: str, extracted_information: str) -> str:
        # check if we have any information to process
        if not extracted_information:
            return "No information available to process the query."
        
        try:
            # use gemini ai to analyze the scraped content and answer the query
            response = self.model.generate_content(
                f"Given the following context: {extracted_information}\n\n"
                f"Carefully answer this query: {query}"
            )
            return response.text
        except Exception as e:
            # print an error message if the ai processing fails
            print(f"Gemini API error: {e}")
            return "Unable to process the query."

    def rank_results(self, results: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        # sort results based on the length of the response, longest first
        return sorted(results, key=lambda x: len(x[1]), reverse=True)

class ScraperApp:
    def __init__(self, master: tk.Tk, scraper: WebsiteScraper):
        # set up the main window for the application
        self.master = master
        self.scraper = scraper
        
        # set window title, size, and background color
        master.title("📡 Web Scraper")
        master.geometry("800x600")
        master.configure(bg='#f0f0f0')
        master.resizable(True, True)
        
        # create and style the app widgets
        self._create_widgets()
        self._style_widgets()

    def _create_widgets(self):
        # create a frame for entering website urls
        url_frame = ttk.LabelFrame(self.master, text="Website URLs", padding=(10, 5))
        url_frame.pack(padx=15, pady=10, fill='x')
        
        # create a scrollable text area for entering multiple urls
        self.url_input = scrolledtext.ScrolledText(
            url_frame, 
            width=80, 
            height=6, 
            wrap=tk.WORD,
            font=('Consolas', 10)
        )
        self.url_input.pack(fill='x', expand=True, padx=5, pady=5)

        # create a frame for entering search query
        query_frame = ttk.LabelFrame(self.master, text="Search Query", padding=(10, 5))
        query_frame.pack(padx=15, pady=5, fill='x')
        
        # create an entry field for the search query
        self.query_input = ttk.Entry(
            query_frame, 
            width=80, 
            font=('Consolas', 12)
        )
        self.query_input.pack(fill='x', expand=True, padx=5, pady=5)

        # create a search button to trigger the query
        self.search_button = ttk.Button(
            self.master, 
            text="🔍 Search Websites", 
            command=self._run_query
        )
        self.search_button.pack(pady=10)

        # create a frame to display search results
        results_frame = ttk.LabelFrame(self.master, text="Search Results", padding=(10, 5))
        results_frame.pack(padx=15, pady=5, fill='both', expand=True)
        
        # create a scrollable text area to show search results
        self.result_text = scrolledtext.ScrolledText(
            results_frame, 
            width=80, 
            height=15, 
            wrap=tk.WORD,
            font=('Consolas', 10)
        )
        self.result_text.pack(fill='both', expand=True, padx=5, pady=5)

    def _style_widgets(self):
        # set up styling for widgets to make them look nice
        style = ttk.Style()
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10, 'bold'))
        style.configure('TLabelframe.Label', font=('Arial', 11, 'bold'))

    def _run_query(self):
        # get list of urls from the input area
        urls = self.url_input.get("1.0", tk.END).strip().split('\n')
        # get the search query
        query = self.query_input.get().strip()

        # show a warning if urls or query are missing
        if not urls or not query:
            messagebox.showwarning("Input Error", "Please enter both URLs and a query.")
            return

        # clear previous search results
        self.result_text.delete("1.0", tk.END)

        # store search results
        results = []
        # loop through each url
        for url in urls:
            if url.strip():
                # scrape the website
                extracted_info = self.scraper.scrape_website(url.strip())
                if extracted_info:
                    # use ai to search and get results
                    search_result = self.scraper.search_with_gemini(query, extracted_info)
                    results.append((url.strip(), search_result))

        # rank results by length
        ranked_results = self.scraper.rank_results(results)
        # display results
        for rank, (url, result) in enumerate(ranked_results, start=1):
            self.result_text.insert(
                tk.END, 
                f"🌐 Result {rank}: {url}\n{result}\n\n", 
                'result'
            )
        
        # style the results text
        self.result_text.tag_configure('result', font=('Consolas', 10), spacing1=5, spacing3=5)

def main():
    # create the main window
    root = tk.Tk()
    
    # create a scraper with google ai api key
    scraper = WebsiteScraper(api_key='writeyourapikeyhere:)')
    
    # create the app and start the main event loop
    app = ScraperApp(root, scraper)
    root.mainloop()

if __name__ == "__main__":
    # run the main function only if the script is run directly
    main()