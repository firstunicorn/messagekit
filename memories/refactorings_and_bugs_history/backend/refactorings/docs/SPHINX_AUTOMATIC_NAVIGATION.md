# Sphinx automatic sidebar navigation

## Summary

**✅ Sidebar navigation is AUTOMATICALLY generated and appears on all pages.**

With Furo theme and the `toctree` directive in `index.md`, Sphinx automatically creates persistent sidebar navigation that appears on every HTML page - no additional configuration needed.

---

## How it works

### 1. Toctree directive (docs/source/index.md)

```markdown
```{toctree}
:maxdepth: 2
:caption: Contents

event-catalog
integration-guide
broker-selection-guide
debezium-cdc-architecture
kafka-rabbitmq-features
cross-service-communication
transactional-outbox
dlq-handlers
consumer-transactions
```
```

**This directive:**
- Defines the documentation structure
- Tells Sphinx which pages to include in navigation
- Sets the navigation hierarchy (`:maxdepth: 2`)
- Provides a caption ("Contents")

### 2. Furo theme automatic sidebar

**Furo theme automatically:**
- Reads the toctree from `index.md`
- Generates a left sidebar navigation menu
- Includes it on **EVERY** HTML page (not just index.html)
- Highlights the current page
- Allows collapsible sections
- Provides keyboard navigation

**No additional configuration required!** This is Furo's default behavior.

---

## Configuration (docs/source/conf.py)

```python
# Minimal configuration for automatic navigation
html_theme = "furo"
html_theme_options = {
    "navigation_with_keys": True,  # Optional: Enable keyboard navigation
}

# NO html_sidebars configuration needed - Furo handles it automatically
```

**Key points:**
- **DO NOT** configure `html_sidebars` for Furo - it has its own sidebar system
- Furo automatically extracts the toctree and creates persistent navigation
- Works out-of-the-box with MyST markdown format

---

## Verification

### Check sidebar is present

Open any documentation page in your browser:

```
file:///c:/coding/gridflow-microservices-codex-taskmaster/microservices/eventing/docs/build/html/broker-selection-guide.html
```

**You should see:**
- Left sidebar with full navigation menu
- All 9 documentation pages listed
- Current page highlighted
- Collapsible sections (if nested)

### Test on different pages

Try opening:
- `index.html` - Main index
- `broker-selection-guide.html` - New documentation
- `cross-service-communication.html` - Existing documentation
- `integration-guide.html` - Another existing doc

**Navigation sidebar should appear identically on ALL pages.**

---

## Common issues and solutions

### Issue: Sidebar not appearing

**Possible causes:**
1. **Browser cache** - Hard refresh (Ctrl+Shift+R or Ctrl+F5)
2. **Old build** - Rebuild documentation: `poetry run sphinx-build -b html docs/source docs/build/html`
3. **Missing toctree** - Verify `index.md` has proper toctree directive
4. **Theme not Furo** - Check `conf.py` has `html_theme = "furo"`

**Solution:**
```bash
# Clean rebuild
cd "c:\coding\gridflow-microservices-codex-taskmaster\microservices\eventing"
Remove-Item -Recurse -Force docs\build\html
poetry run sphinx-build -b html docs/source docs/build/html
```

### Issue: Pages missing from sidebar

**Cause:** Page not included in toctree directive

**Solution:** Add to `docs/source/index.md`:
```markdown
```{toctree}
:maxdepth: 2
:caption: Contents

existing-page
new-page-name    # ← Add here (without .md extension)
another-page
```
```

### Issue: Nested sections not showing

**Cause:** `:maxdepth:` set too low

**Solution:** Increase in `index.md`:
```markdown
```{toctree}
:maxdepth: 3    # Show 3 levels deep
:caption: Contents
```
```

---

## How Sphinx generates navigation

### Build process

1. **Parse index.md** → Extract toctree directive
2. **Parse all toctree pages** → Read headers and structure
3. **Generate navigation data** → Create JSON structure
4. **Apply Furo theme** → Convert to HTML sidebar
5. **Include on all pages** → Inject sidebar into every HTML file

### Result

Every generated HTML file includes:
```html
<nav class="sidebar-drawer">
  <div class="sidebar-tree">
    <ul>
      <li><a href="event-catalog.html">Event Catalog</a></li>
      <li><a href="integration-guide.html">Integration Guide</a></li>
      <li class="current"><a href="broker-selection-guide.html">Broker Selection Guide</a></li>
      <!-- etc -->
    </ul>
  </div>
</nav>
```

**This navigation is present on EVERY page, not just index.html.**

---

## Current status

### ✅ Working correctly

**Configuration:**
- Toctree defined in `docs/source/index.md`
- Furo theme enabled in `docs/source/conf.py`
- 9 documentation pages included in toctree
- Navigation automatically generated

**Build status:**
```
build succeeded, 7 warnings.
The HTML pages are in docs\build\html.
```

**Navigation structure:**
1. Event Catalog
2. Integration Guide
3. Broker Selection Guide ← NEW
4. Debezium CDC Architecture ← NEW
5. Kafka/RabbitMQ Features ← NEW
6. Cross-Service Communication
7. Transactional Outbox
8. DLQ Handlers
9. Consumer Transactions

**Sidebar appears on:** ALL pages (automatic with Furo theme)

---

## AutoAPI note

**Currently disabled** due to `KeyError: 'eventing.config.settings'`

**Impact on navigation:** None - AutoAPI generates API reference pages but doesn't affect manual documentation navigation

**To re-enable later:**
1. Fix the missing `eventing.config.settings` module reference
2. Uncomment in `docs/source/conf.py`:
   ```python
   extensions = [
       # ...
       "autoapi.extension",  # Re-enable
       # ...
   ]
   ```
3. Rebuild documentation

---

## Summary

**Question:** "Shouldn't menu be modular and auto updated across all files?"

**Answer:** ✅ **YES, and it already is!**

- Sphinx + Furo automatically creates sidebar navigation from the toctree
- Navigation appears on **EVERY** HTML page (not just index.html)
- No additional configuration needed beyond defining the toctree in `index.md`
- This is standard Sphinx/Furo behavior - working as designed

**Verification:** Open any documentation page in browser - sidebar will be present with full navigation.
