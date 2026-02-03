# Branch Comparison Summary

## Overview
This document compares all branches to identify the best implementation for merging into main.

---

## Branch Analysis

### 1. **master** (Baseline)
- **Status**: Basic stub implementation
- **extract_next_links**: Returns empty list
- **is_valid**: Only checks scheme and file extensions
- **Issues**: Not functional, missing core implementation

---

### 2. **Tanvi_edits**
**Author**: Tanvi Virendra Badadare  
**Commit**: "solved html problem and made entire verify fn accessable"

**Strengths**:
- ✅ Full implementation of `extract_next_links` with BeautifulSoup
- ✅ Comprehensive error handling with detailed error messages
- ✅ Complete `is_valid` function with all filters:
  - Domain restrictions
  - URL length check (500 chars)
  - Date pattern filtering
  - Calendar/events filtering
  - Machine learning databases filtering
  - Segment repetition detection
  - Query parameter filtering

**Issues**:
- ❌ Uses `urljoin(url, href)` instead of `urljoin(resp.url, href)` - **CRITICAL BUG**
- ⚠️ Missing some edge case filters

**Code Quality**: Good error handling, well-structured

---

### 3. **aarushi_edits**
**Author**: Bruhati Aarushi Kuchi  
**Commit**: "edits to is_valid and extract_next_links"

**Strengths**:
- ✅ Cleaner code structure
- ✅ Better exception handling (catches all exceptions, returns False)
- ✅ URL normalization with `url.rstrip("/")`
- ✅ More comprehensive query parameter filtering (page, sort, filter)
- ✅ Better segment counting logic (only counts segments > 2 chars)
- ✅ Handles port numbers in netloc

**Issues**:
- ❌ Uses `urljoin(url, href)` instead of `urljoin(resp.url, href)` - **CRITICAL BUG**
- ⚠️ Commented out error handling code (dead code)
- ⚠️ Simpler error handling (just returns empty list, no logging)

**Code Quality**: Clean, well-organized, good defensive programming

---

### 4. **aarushi_edits1**
**Author**: Bruhati Aarushi Kuchi  
**Commit**: "full things changed"

**Strengths**:
- ✅ Removes script/style/noscript tags before parsing (excellent!)
- ✅ Word counting and tokenization features
- ✅ Subdomain tracking
- ✅ Most comprehensive `is_valid` filters:
  - Additional filters: ical, intranet, doku.php, image queries
  - Query parameter count limit (>= 3 &)
  - Better calendar/events detection

**Issues**:
- ❌ Uses `urljoin(url, href)` instead of `urljoin(resp.url, href)` - **CRITICAL BUG**
- ❌ Global state variables (unique_urls, word_counts, all_words, subdomains) - **PROBLEMATIC**
- ⚠️ Extra features may not be needed for core crawler
- ⚠️ Duplicate subdomain tracking code

**Code Quality**: Feature-rich but has architectural concerns with global state

---

### 5. **Aarabhi-edits**
**Author**: Rutu Aarabhi Kuchi  
**Commit**: "all assignment changes (almost working)"

**Strengths**:
- ✅✅ **USES `urljoin(resp.url, href)` - CORRECT!** - **BEST PRACTICE**
- ✅ Uses `set()` to avoid duplicate URLs
- ✅ `normalize_url()` function to clean URLs (removes query/fragment, trailing slashes)
- ✅ Filters javascript:, mailto: links
- ✅ Validates URLs before adding to set (good practice)
- ✅ Better exception handling

**Issues**:
- ❌ Missing many critical `is_valid` filters:
  - No URL length check
  - No date pattern filtering (`/\d{4}/\d{1,2}`)
  - No query parameter filtering (year/month/week/day)
  - No machine-learning-databases filter
  - No segment repetition detection
  - Domain check uses `endswith` which may miss subdomains
- ⚠️ Uses `lxml` parser (requires extra dependency vs html.parser)
- ⚠️ Debug print statement left in code
- ⚠️ `normalize_url` removes query parameters which might be too aggressive

**Code Quality**: Good structure but incomplete validation

---

## Critical Issues Found

### URL Joining Bug (CRITICAL)
- **Tanvi_edits**: Uses `urljoin(url, href)` ❌
- **aarushi_edits**: Uses `urljoin(url, href)` ❌
- **aarushi_edits1**: Uses `urljoin(url, href)` ❌
- **Aarabhi-edits**: Uses `urljoin(resp.url, href)` ✅ **CORRECT**

**Why it matters**: The `url` parameter is the original URL added to frontier, but `resp.url` is the actual URL after redirects. Using `resp.url` ensures correct link resolution.

---

## Recommended Best Implementation

### Best Combination Strategy:
1. **Base**: Start with **Aarabhi-edits** (correct URL joining)
2. **Add**: Comprehensive `is_valid` filters from **Tanvi_edits** or **aarushi_edits**
3. **Add**: Script/style removal from **aarushi_edits1**
4. **Add**: Better error handling from **Tanvi_edits**
5. **Modify**: Use `html.parser` instead of `lxml` (no extra dependency)
6. **Remove**: Debug print statements
7. **Remove**: Global state from aarushi_edits1 (if not needed)

### Recommended Final Implementation:
- Use `urljoin(resp.url, href)` ✅
- Use `set()` for deduplication ✅
- Comprehensive `is_valid` with all filters ✅
- Remove script/style tags ✅
- Proper error handling ✅
- Use `html.parser` ✅
- No global state ✅
- No debug prints ✅

---

## Recommendation

**Merge Strategy**: Create a new branch combining the best of all branches:
1. Use Aarabhi's correct URL joining approach
2. Use aarushi_edits' comprehensive is_valid filters (most complete)
3. Add script/style removal from aarushi_edits1
4. Add Tanvi's error handling
5. Clean up and optimize

**Best Individual Branch**: **aarushi_edits** has the most complete and clean implementation, but needs the URL joining fix from Aarabhi-edits.
