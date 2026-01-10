// Storage key for saved articles
const STORAGE_KEY = 'turnbackhoax_articles';

// Get saved articles from storage
async function getStoredArticles() {
  const result = await chrome.storage.local.get([STORAGE_KEY]);
  return result[STORAGE_KEY] || [];
}

// Save articles to storage
async function saveArticles(articles) {
  await chrome.storage.local.set({ [STORAGE_KEY]: articles });
}

// Update the UI with current counts
async function updateUI() {
  const articles = await getStoredArticles();
  document.getElementById('totalCount').textContent = articles.length;
  
  // Check if we're on a valid page
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  if (tab.url && tab.url.includes('turnbackhoax.id/articles')) {
    // Extract page info from URL
    const url = new URL(tab.url);
    const dateRange = url.searchParams.get('dateRange') || 'All';
    const page = url.searchParams.get('page') || '1';
    
    document.getElementById('pageInfo').textContent = `${dateRange.replace('+', ' ')} - Page ${page}`;
    document.getElementById('scrapeBtn').disabled = false;
    
    // Get count of articles on current page
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const articles = document.querySelectorAll('div.news-card-h-alt');
          return articles.length;
        }
      });
      document.getElementById('pageCount').textContent = results[0].result || 0;
    } catch (e) {
      document.getElementById('pageCount').textContent = '?';
    }
  } else {
    document.getElementById('pageInfo').textContent = 'Not on TurnBackHoax articles page';
    document.getElementById('scrapeBtn').disabled = true;
    document.getElementById('pageCount').textContent = '-';
  }
}

// Scrape articles from current page
async function scrapeCurrentPage() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  if (!tab.url || !tab.url.includes('turnbackhoax.id/articles')) {
    showMessage('Not on a TurnBackHoax articles page', 'error');
    return;
  }
  
  // Extract date range and page from URL
  const url = new URL(tab.url);
  const dateRange = url.searchParams.get('dateRange') || 'Unknown';
  const pageNum = url.searchParams.get('page') || '1';
  
  try {
    // Execute script to extract articles
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const articles = [];
        const cards = document.querySelectorAll('div.news-card-h-alt');
        
        cards.forEach(card => {
          const titleEl = card.querySelector('h2');
          const linkEl = card.querySelector('a[href]');
          const previewEl = card.querySelector('p');
          const imgEl = card.querySelector('img');
          const dateEl = card.querySelector('span.text-light-black');
          const categoryEl = card.querySelector('a[href*="category="]');
          
          // Get full title from hidden span or visible text
          let title = '';
          if (titleEl) {
            const hiddenSpan = titleEl.querySelector('span.hidden');
            title = hiddenSpan ? hiddenSpan.textContent.trim() : titleEl.textContent.trim();
          }
          
          // Get full preview from hidden span or visible text
          let preview = '';
          if (previewEl) {
            const hiddenSpan = previewEl.querySelector('span.hidden');
            preview = hiddenSpan ? hiddenSpan.textContent.trim() : previewEl.textContent.trim();
          }
          
          articles.push({
            title: title,
            url: linkEl ? linkEl.href : '',
            preview: preview,
            image_url: imgEl ? imgEl.src : '',
            date: dateEl ? dateEl.textContent.trim() : '',
            category: categoryEl ? categoryEl.textContent.trim() : ''
          });
        });
        
        return articles;
      }
    });
    
    const newArticles = results[0].result || [];
    
    if (newArticles.length === 0) {
      showMessage('No articles found on this page', 'warning');
      return;
    }
    
    // Add metadata to articles
    const articlesWithMeta = newArticles.map(article => ({
      ...article,
      page_number: pageNum,
      date_range: dateRange.replace('+', ' ')
    }));
    
    // Get existing articles and filter duplicates by URL
    const existingArticles = await getStoredArticles();
    const existingUrls = new Set(existingArticles.map(a => a.url));
    
    const uniqueNewArticles = articlesWithMeta.filter(a => !existingUrls.has(a.url));
    
    if (uniqueNewArticles.length === 0) {
      showMessage(`All ${newArticles.length} articles already saved`, 'warning');
    } else {
      // Save new articles
      const allArticles = [...existingArticles, ...uniqueNewArticles];
      await saveArticles(allArticles);
      
      const skipped = newArticles.length - uniqueNewArticles.length;
      if (skipped > 0) {
        showMessage(`Saved ${uniqueNewArticles.length} new articles (${skipped} duplicates skipped)`, 'success');
      } else {
        showMessage(`Saved ${uniqueNewArticles.length} articles!`, 'success');
      }
    }
    
    updateUI();
    
  } catch (e) {
    console.error(e);
    showMessage('Error scraping page: ' + e.message, 'error');
  }
}

// Download articles as CSV
async function downloadCSV() {
  const articles = await getStoredArticles();
  
  if (articles.length === 0) {
    showMessage('No articles to download', 'warning');
    return;
  }
  
  // Create CSV content
  const headers = ['title', 'url', 'preview', 'image_url', 'date', 'category', 'page_number', 'date_range'];
  
  const escapeCSV = (str) => {
    if (str === null || str === undefined) return '';
    str = String(str);
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
  };
  
  const csvContent = [
    headers.join(','),
    ...articles.map(article => 
      headers.map(h => escapeCSV(article[h])).join(',')
    )
  ].join('\n');
  
  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  
  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const filename = `turnbackhoax_headlines_extension_${timestamp}.csv`;
  
  chrome.downloads.download({
    url: url,
    filename: filename,
    saveAs: true
  });
  
  showMessage(`Downloading ${articles.length} articles...`, 'success');
}

// Clear all stored data
async function clearData() {
  if (confirm('Are you sure you want to delete all saved articles?')) {
    await saveArticles([]);
    updateUI();
    showMessage('All data cleared', 'success');
  }
}

// Show message to user
function showMessage(text, type) {
  const msgEl = document.getElementById('message');
  msgEl.textContent = text;
  msgEl.className = 'message ' + type;
  
  setTimeout(() => {
    msgEl.textContent = '';
    msgEl.className = 'message';
  }, 3000);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  updateUI();
  
  document.getElementById('scrapeBtn').addEventListener('click', scrapeCurrentPage);
  document.getElementById('downloadBtn').addEventListener('click', downloadCSV);
  document.getElementById('clearBtn').addEventListener('click', clearData);
});
