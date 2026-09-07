# howtos

Dremel Lab how-to guides and operational documentation

## Available Guides

### [Getting Access to Dremel Lab S3 Files via Globus](guides/s3-globus-access/s3_globus_access_guide.md)
A step-by-step guide for Dremel Lab members to set up Globus access to the lab's S3 storage. Covers authentication via UVA NetBadge, finding collections, adding S3 credentials, and handling different storage classes.

**Time to complete:** 5-10 minutes  
**Prerequisites:** Active virginia.edu account

### [Rivanna Storage Options](guides/rivanna-storage-options/rivanna_storage_guide.md)
A reference for the storage locations available on Rivanna (`/home`, `/scratch`, `/project`, `/standard`), when to use each, measured I/O performance differences, and the scripts used for scratch cleanup and storage usage reporting.

**Time to complete:** 5-10 minutes  
**Prerequisites:** Active Rivanna account, Dremel Lab group access

---

## Guide Directory Structure

Each guide has its own directory under `guides/`:

```
guides/
├── s3-globus-access/
│   ├── s3_globus_access_guide.md      (source markdown)
│   ├── s3_globus_access_guide.qmd     (Quarto document)
│   ├── s3_globus_access_guide.html    (rendered HTML)
│   ├── s3_globus_access_guide_files/  (generated assets)
│   └── images/                         (screenshots and diagrams)
```

## Contributing

To add a new how-to guide:
1. Create a new directory under `guides/` with a descriptive name (e.g., `guides/topic-name/`)
2. Create source files:
   - `topic_name.md` (markdown source)
   - `topic_name.qmd` (Quarto document with metadata)
   - `images/` subdirectory for screenshots
3. Follow the structure: Overview → Prerequisites → Step-by-Step → Troubleshooting → Key Points
4. Add a `.guide-nav` entry for the new guide to every other guide's `.qmd` (`include-before-body`), and add the other guides' links to the new guide's own `.guide-nav` — this is the cross-guide nav bar shown at the top of each published page, and it must be added by hand to each `.qmd`'s frontmatter (not the `.md`) since it isn't rendered from `index.html`
5. Render with Quarto: `quarto render guides/topic-name/topic_name.qmd`
6. Update this README and `index.html` with a link to the new guide
