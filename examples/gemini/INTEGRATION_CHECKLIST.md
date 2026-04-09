# Gemini + CIAF Integration Checklist

Use this checklist to track your integration progress.

## Phase 1: Setup (Est. 30 minutes)

### Environment Setup
- [ ] Python 3.8+ installed
- [ ] Create new project directory
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate virtual environment
- [ ] Copy `.env.example` to `.env`
- [ ] Add your `GEMINI_API_KEY` to `.env`

### Dependencies
- [ ] Install core packages: `pip install ciaf-watermarks google-generativeai`
- [ ] Install optional packages (if needed)
- [ ] Create `requirements.txt` for your project
- [ ] Test imports work:
  ```python
  import google.generativeai as genai
  from ciaf_watermarks import watermark_ai_output
  print("✓ Imports successful")
  ```

### Configuration
- [ ] Copy `config_template.py` to your project
- [ ] Customize configuration values
- [ ] Set `VERIFICATION_BASE_URL`
- [ ] Choose evidence storage method (JSON or MongoDB)
- [ ] Create evidence directory: `mkdir evidence`

---

## Phase 2: Basic Integration (Est. 1-2 hours)

### Gemini Setup
- [ ] Configure Gemini API client
- [ ] Test basic Gemini call:
  ```python
  model = genai.GenerativeModel('gemini-pro')
  response = model.generate_content("Hello Gemini")
  print(response.text)
  ```
- [ ] Verify API key works
- [ ] Test error handling for invalid key

### First Watermark
- [ ] Create simple test script
- [ ] Generate text with Gemini
- [ ] Watermark the output using `watermark_ai_output()`
- [ ] Print watermarked text
- [ ] Verify footer/header appears
- [ ] Check evidence object structure
- [ ] Verify `artifact_id` and `watermark_id` generated

### Evidence Storage
- [ ] Save evidence to JSON file
- [ ] Test loading evidence back
- [ ] Verify JSON structure matches expected format
- [ ] Test with multiple artifacts
- [ ] Implement error handling for file I/O

### First Verification
- [ ] Import verification function
- [ ] Load stored evidence
- [ ] Verify same content (should match 100%)
- [ ] Test with modified content (should detect changes)
- [ ] Check verification result structure
- [ ] Understand confidence scores

---

## Phase 3: Real Integration (Est. 2-4 hours)

### Application Integration
- [ ] Identify where Gemini is called in your app
- [ ] Wrap Gemini responses with watermarking
- [ ] Pass correct parameters:
  - [ ] `model_id` from Gemini model name
  - [ ] `model_version` from version/date
  - [ ] `actor_id` from user identifier
  - [ ] `prompt` from user input
- [ ] Test watermarking in your app flow
- [ ] Verify no breaking changes

### Error Handling
- [ ] Handle empty Gemini responses
- [ ] Handle watermarking failures gracefully
- [ ] Handle evidence storage failures
- [ ] Add retry logic for transient errors
- [ ] Log all errors appropriately
- [ ] Test error scenarios

### Configuration Management
- [ ] Set up global CIAF config
- [ ] Initialize watermarking on app startup
- [ ] Test configuration override per-request
- [ ] Verify different watermark styles work
- [ ] Test with different artifact types (if applicable)

### Logging
- [ ] Add logging for watermarking operations
- [ ] Log evidence storage success/failure
- [ ] Log verification requests
- [ ] Include relevant metadata in logs
- [ ] Set appropriate log levels

---

## Phase 4: Verification System (Est. 2-3 hours)

### Verification Function
- [ ] Create verification helper function
- [ ] Load evidence by `artifact_id` or `watermark_id`
- [ ] Call appropriate verification function for type
- [ ] Return structured result
- [ ] Handle missing evidence gracefully

### Verification API (Optional)
- [ ] Create POST `/verify` endpoint
- [ ] Accept `content` and `watermark_id`
- [ ] Look up evidence from storage
- [ ] Run verification
- [ ] Return JSON result with confidence
- [ ] Add authentication if needed
- [ ] Test with curl/Postman

### Verification UI (Optional)
- [ ] Create simple web form
- [ ] Accept pasted content + watermark ID
- [ ] Display verification result
- [ ] Show confidence score visually
- [ ] Explain what tier matched
- [ ] Handle errors gracefully

---

## Phase 5: Testing (Est. 2-3 hours)

### Unit Tests
- [ ] Test watermarking with mock Gemini response
- [ ] Test evidence serialization
- [ ] Test evidence deserialization
- [ ] Test verification with known artifacts
- [ ] Test error handling paths
- [ ] Achieve >80% code coverage

### Integration Tests
- [ ] Real Gemini call → watermark → verify
- [ ] Test with different prompts
- [ ] Test with long content (>5K chars)
- [ ] Test with empty responses
- [ ] Test concurrent requests
- [ ] Test evidence storage/retrieval

### Edge Cases
- [ ] Very long Gemini responses (>10K chars)
- [ ] Empty or whitespace-only responses
- [ ] Special characters in content
- [ ] Unicode content
- [ ] Malformed evidence JSON
- [ ] Missing evidence files

### Performance Tests
- [ ] Measure watermarking latency
- [ ] Test under load (N requests/second)
- [ ] Monitor memory usage
- [ ] Test evidence storage performance
- [ ] Identify bottlenecks

---

## Phase 6: Production Preparation (Est. 3-5 hours)

### Security Hardening
- [ ] Hash prompts containing PII
- [ ] Encrypt evidence at rest (if required)
- [ ] Add API authentication for verification
- [ ] Validate all user inputs
- [ ] Sanitize outputs
- [ ] Review and fix security warnings

### Monitoring
- [ ] Add health check endpoint
- [ ] Implement metrics collection
- [ ] Set up alerts for failures
- [ ] Monitor watermarking latency
- [ ] Track evidence storage failures
- [ ] Monitor verification request rate

### Documentation
- [ ] Document API endpoints
- [ ] Write deployment guide
- [ ] Create troubleshooting runbook
- [ ] Document configuration options
- [ ] Add code comments
- [ ] Update README

### Deployment
- [ ] Set up environment variables in prod
- [ ] Configure secrets management
- [ ] Test in staging environment
- [ ] Plan rollback strategy
- [ ] Deploy to production
- [ ] Monitor initial deployment

---

## Phase 7: Optional Enhancements

### Advanced Features
- [ ] Implement async evidence generation
- [ ] Add batch processing for multiple requests
- [ ] Set up MongoDB vault (if using)
- [ ] Implement caching for verification
- [ ] Add rate limiting
- [ ] Enable metrics export (Prometheus)

### User Experience
- [ ] Add watermark visibility toggle
- [ ] Create user preferences for watermark style
- [ ] Show verification link in UI
- [ ] Add "Verify this content" button
- [ ] Display provenance information nicely

### Analytics
- [ ] Track watermarking adoption rate
- [ ] Analyze verification request patterns
- [ ] Monitor confidence score distribution
- [ ] Track authentication rates (Tier 1/2/3)
- [ ] Generate compliance reports

---

## Validation Checklist

Before considering integration complete, verify:

### Functionality
- [ ] All Gemini responses are watermarked
- [ ] Evidence is stored reliably
- [ ] Verification works for authentic content
- [ ] Modified content is detected
- [ ] Error handling works correctly

### Performance
- [ ] Watermarking adds <100ms latency
- [ ] No memory leaks detected
- [ ] Evidence storage scales
- [ ] Verification is fast (<50ms typical)

### Security
- [ ] PII in prompts is hashed
- [ ] API authentication works
- [ ] Evidence is stored securely
- [ ] No sensitive data logged

### Reliability
- [ ] Handles Gemini API failures
- [ ] Graceful degradation works
- [ ] Retry logic functions
- [ ] Monitoring is in place

### Documentation
- [ ] Setup instructions clear
- [ ] API documented
- [ ] Troubleshooting guide available
- [ ] Code is commented

---

## Success Criteria

Integration is successful when:
- ✅ All Gemini outputs are automatically watermarked
- ✅ Evidence is stored and retrievable
- ✅ Verification correctly identifies authentic content
- ✅ System handles errors gracefully
- ✅ Performance impact is minimal (<10% overhead)
- ✅ Team is trained on system usage
- ✅ Monitoring is operational

---

## Timeline Estimate

| Phase | Estimated Time | Dependencies |
|-------|----------------|--------------|
| Setup | 30 min | API keys |
| Basic Integration | 1-2 hours | Setup complete |
| Real Integration | 2-4 hours | Basic working |
| Verification System | 2-3 hours | Integration done |
| Testing | 2-3 hours | All features done |
| Production Prep | 3-5 hours | Tests passing |
| **Total** | **11-17 hours** | - |

*Add 50% buffer for unexpected issues*

---

## Need Help?

- Review [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for code examples
- Check [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for detailed explanations
- Check troubleshooting section in implementation guide
- Review error messages carefully
- Test with minimal examples first

---

**Track your progress and check off items as you go!**
